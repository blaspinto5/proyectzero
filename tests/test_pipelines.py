import json
import os
from types import SimpleNamespace
from sqlalchemy import text

import pytest

from projectzero2.pipelines import PostgresPipeline, CsvPipeline, JsonIncrementalPipeline


class DummySpider:
    def __init__(self):
        self.logger = SimpleNamespace(error=lambda *a, **k: None, warning=lambda *a, **k: None)


def test_postgres_pipeline_sqlite_inmemory():
    p = PostgresPipeline("sqlite:///:memory:")
    spider = DummySpider()
    p.open_spider(spider)

    item = {"url": "http://example.test/a", "titulo": "One", "precio": "10", "stock": 1}
    out = p.process_item(item, spider)
    assert out.get("id") is not None
    first_id = int(out.get("id"))

    # update same URL
    item2 = {"url": "http://example.test/a", "titulo": "One-updated", "precio": "11", "stock": 2}
    out2 = p.process_item(item2, spider)
    assert int(out2.get("id")) == first_id

    # verify persisted value in DB
    res = p.conn.execute(text("SELECT titulo, precio, stock FROM items WHERE id = :id"), {"id": first_id}).fetchone()
    assert res is not None
    assert res[0] == "One-updated"

    p.close_spider(spider)


def test_csv_pipeline_dedup_and_fields(tmp_path):
    fp = tmp_path / "out.csv"
    p = CsvPipeline(str(fp))
    p.open_spider(None)

    item1 = {"url": "http://a/1", "titulo": "T1", "precio": "10", "stock": 1}
    item2 = {"url": "http://a/1", "titulo": "T1-dup", "precio": "10", "stock": 1}
    item3 = {"url": "http://a/2", "titulo": "T2", "precio": "20", "stock": 0, "id": 123}

    p.process_item(item1, None)
    p.process_item(item2, None)  # should dedupe by url
    p.process_item(item3, None)

    assert fp.exists()
    with open(fp, "r", encoding="utf-8") as f:
        lines = [l for l in f.readlines() if l.strip()]
    # header + 2 rows (item1 and item3)
    assert len(lines) == 3
    assert "T1" in lines[1]
    assert "123" in lines[2]


def test_json_incremental_atomic_and_ordering(tmp_path):
    fp = tmp_path / "out.json"
    p = JsonIncrementalPipeline(str(fp))
    p.open_spider(None)

    item1 = {"id": 20, "url": "u1", "titulo": "A"}
    item2 = {"id": 5, "url": "u2", "titulo": "B"}
    item3 = {"url": "u3", "titulo": "C"}

    p.process_item(item1, None)
    p.process_item(item2, None)
    p.process_item(item3, None)

    assert fp.exists()
    data = json.loads(fp.read_text(encoding="utf-8"))
    # items should be ordered by numeric id when present: id 5 then 20 then item3 without id at end
    assert isinstance(data, list)
    assert data[0]["id"] == 5
    assert data[1]["id"] == 20
    # last element should be the one without id
    assert data[-1]["url"] == "u3"
