import os
import json
import tempfile
from threading import Lock
from csv import DictWriter

from sqlalchemy import (create_engine, MetaData, Table, Column, Integer, Text, String)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError


class JsonIncrementalPipeline:
    def __init__(self, file_path):
        self.file_path = file_path
        self.lock = Lock()
        self.data = {}

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.get("JSON_OUTPUT_FILE", "/data/output.json"))

    def open_spider(self, spider):
        os.makedirs(os.path.dirname(self.file_path) or ".", exist_ok=True)
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    items = json.load(f)
                    if isinstance(items, list):
                        self.data = {item.get("url", str(i)): item for i, item in enumerate(items)}
                    elif isinstance(items, dict):
                        self.data = items
            except Exception:
                self.data = {}

    def process_item(self, item, spider):
        # Prefer DB id if available for stable ordering and keys
        key = None
        if item.get("id") is not None:
            key = str(item.get("id"))
        else:
            key = item.get("url") if hasattr(item, "get") else json.dumps(dict(item), sort_keys=True)

        with self.lock:
            self.data[key] = dict(item)

            # Write items ordered by numeric id when available
            dirpath = os.path.dirname(self.file_path) or "."
            os.makedirs(dirpath, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(dir=dirpath)
            try:
                # sort by integer id when present
                def sort_key(i):
                    try:
                        return int(i.get("id"))
                    except Exception:
                        return float("inf")

                items = list(self.data.values())
                items.sort(key=sort_key)

                with os.fdopen(fd, "w", encoding="utf-8") as tmpf:
                    json.dump(items, tmpf, ensure_ascii=False, indent=2)
                os.replace(tmp_path, self.file_path)
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
        return item


class CsvPipeline:
    def __init__(self, file_path):
        self.file_path = file_path
        self.lock = Lock()
        self.seen = set()
        self.fieldnames = ["id", "url", "titulo", "precio", "stock", "stock_image"]

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.get("CSV_OUTPUT_FILE", "/data/output.csv"))

    def open_spider(self, spider):
        os.makedirs(os.path.dirname(self.file_path) or ".", exist_ok=True)
        # if file exists, load seen keys
        if os.path.exists(self.file_path):
            try:
                # read ids from csv header-aware
                with open(self.file_path, "r", encoding="utf-8", newline="") as f:
                    from csv import DictReader
                    reader = DictReader(f)
                    for row in reader:
                        if row.get("id"):
                            self.seen.add(row.get("id"))
            except Exception:
                self.seen = set()

    def process_item(self, item, spider):
        # prefer id for deduplication
        key = None
        if item.get("id") is not None:
            key = str(item.get("id"))
        else:
            key = item.get("url") if hasattr(item, "get") else json.dumps(dict(item), sort_keys=True)

        with self.lock:
            is_new = key not in self.seen
            if is_new:
                write_header = not os.path.exists(self.file_path)
                with open(self.file_path, "a", encoding="utf-8", newline="") as csvf:
                    writer = DictWriter(csvf, fieldnames=self.fieldnames)
                    if write_header:
                        writer.writeheader()
                    row = {
                        "id": item.get("id", ""),
                        "url": item.get("url", ""),
                        "titulo": item.get("titulo", ""),
                        "precio": item.get("precio", ""),
                        "stock": item.get("stock", ""),
                        "stock_image": item.get("stock_image", ""),
                    }
                    writer.writerow(row)
                self.seen.add(key)
        return item


class PostgresPipeline:
    """Pipeline que inserta/actualiza items en PostgreSQL usando SQLAlchemy + upsert.

    Requiere `DATABASE_URL` en settings o como variable de entorno.
    """

    def __init__(self, db_url):
        self.db_url = db_url
        self.engine = None
        self.conn = None
        self.metadata = MetaData()
        self.table = Table(
            "items",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("url", String, unique=True, index=True),
            Column("titulo", Text),
            Column("precio", Text),
            Column("stock", Text),
            Column("raw", Text),
        )

    @classmethod
    def from_crawler(cls, crawler):
        db = crawler.settings.get("DATABASE_URL") or crawler.settings.get("DATABASE_URL")
        if not db:
            db = os.environ.get("DATABASE_URL")
        return cls(db)

    def open_spider(self, spider):
        if not self.db_url:
            spider.logger.warning("No DATABASE_URL configured; PostgresPipeline disabled")
            return
        self.engine = create_engine(self.db_url)
        self.metadata.create_all(self.engine)
        self.conn = self.engine.connect()
        # detect sqlite fallback
        self._is_sqlite = False
        try:
            if self.engine.url.get_backend_name() == 'sqlite':
                self._is_sqlite = True
        except Exception:
            self._is_sqlite = False

    def process_item(self, item, spider):
        if not self.conn:
            return item

        values = {
            "url": item.get("url"),
            "titulo": item.get("titulo"),
            "precio": item.get("precio"),
            "stock": item.get("stock"),
            "raw": json.dumps(dict(item), ensure_ascii=False),
        }

        # If using sqlite (fallback), SQLAlchemy's PG upsert is not available; do insert-or-update logic
        if getattr(self, '_is_sqlite', False):
            try:
                ins = self.table.insert().values(**values)
                self.conn.execute(ins)
            except IntegrityError:
                try:
                    upd = self.table.update().where(self.table.c.url == values.get('url')).values(**values)
                    self.conn.execute(upd)
                except Exception as e:
                    spider.logger.error(f"SQLite write failed during update: {e}")
            except Exception as e:
                spider.logger.error(f"SQLite write failed during insert: {e}")

            # fetch id
            try:
                sel = self.table.select().with_only_columns([self.table.c.id]).where(self.table.c.url == item.get("url"))
                r = self.conn.execute(sel).fetchone()
                returned_id = r[0] if r else None
                if returned_id is not None:
                    item["id"] = int(returned_id)
            except Exception:
                pass

            return item

        # Default: assume Postgres and use dialect upsert
        insert_stmt = pg_insert(self.table).values(**values)
        update_cols = {c.name: insert_stmt.excluded[c.name] for c in self.table.c if c.name not in ("id",)}
        upsert = insert_stmt.on_conflict_do_update(
            index_elements=[self.table.c.url],
            set_=update_cols,
        ).returning(self.table.c.id)

        try:
            result = self.conn.execute(upsert)
            try:
                returned_id = result.scalar_one()
            except Exception:
                # fallback: fetch by URL
                sel = self.table.select().with_only_columns([self.table.c.id]).where(self.table.c.url == item.get("url"))
                r = self.conn.execute(sel).fetchone()
                returned_id = r[0] if r else None

            if returned_id is not None:
                item["id"] = int(returned_id)

        except Exception as e:
            spider.logger.error(f"Postgres write failed: {e}")

        return item

    def close_spider(self, spider):
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
        if self.engine:
            try:
                self.engine.dispose()
            except Exception:
                pass


class NormalizeItemPipeline:
    """Normaliza campos del item antes de persistir:
    - asegura claves `url`, `titulo`, `precio`, `stock`
    - mapea `title` -> `titulo` si existe
    - convierte `precio` a string simple (puedes adaptar a float)
    """

    def process_item(self, item, spider):
        # map english title
        if not item.get("titulo") and item.get("title"):
            item["titulo"] = item.get("title")

        # ensure fields exist
        for k in ("url", "titulo", "precio", "stock"):
            if k not in item:
                item[k] = None

        # normalize price: remove currency symbols, keep as string or numeric
        precio = item.get("precio")
        if precio is not None:
            try:
                # try to extract digits and separators
                cleaned = str(precio).replace("$", "").replace("€", "").replace(" ", "")
                item["precio"] = cleaned
            except Exception:
                item["precio"] = str(precio)

        return item


class ScorePipeline:
    """Asegura que el item tiene un campo `score`. Si no lo tiene, lo calcula.

    - Usa `stock` y `precio` si están disponibles
    - Respeta `score` si ya está presente
    """

    def process_item(self, item, spider):
        if item.get("score") is not None:
            return item

        score = 0

        # 1) availability: prefer items with explicit stock numbers
        stock = item.get("stock")
        if isinstance(stock, int):
            # scale stock up to 50 points (capped)
            score += min(50, int(stock))
        elif stock:
            # presence indicates availability
            score += 40

        # 2) images: more images -> higher score (up to 20)
        images = item.get("images") or []
        try:
            score += min(20, len(images) * 5)
        except Exception:
            pass

        # 3) description length: more detail -> up to 15 points
        desc = (item.get("description") or "")
        if len(desc) > 200:
            score += 15
        elif len(desc) > 80:
            score += 8

        # 4) promotional keywords
        txt = " ".join([str(item.get(k, "")) for k in ("titulo", "description")])
        for kw in ("oferta", "descuento", "nuevo", "rebaja", "promocion", "pack"):
            if kw in txt.lower():
                score += 5

        # 5) discount detection: presence of an old price (struck-through) is positive signal
        raw = txt + " " + str(item.get("precio") or "")
        if "\"" in raw:  # keep cheap check trivial (no conversion) - placeholder
            pass

        # cap and ensure integer
        item["score"] = max(0, min(100, int(score)))
        return item
