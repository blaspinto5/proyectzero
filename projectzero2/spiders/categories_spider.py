"""
Spider maestro para extraer todas las categorías y productos de n1g.cl
Genera JSONs separados por categoría y guarda todo en la base de datos.
"""
import json
import os
import re
from pathlib import Path
from datetime import datetime

import scrapy
from scrapy_playwright.page import PageMethod

from .n1g_spider import extract_product


class CategoriesSpider(scrapy.Spider):
    """
    Spider que extrae TODAS las categorías del sitio n1g.cl
    y scrapea los productos de cada una.
    
    Uso:
        scrapy crawl categories
        scrapy crawl categories -a max_pages=5  # Limitar páginas por categoría
    """
    name = "categories"
    allowed_domains = ["n1g.cl"]
    start_urls = ["https://n1g.cl/Home/"]
    
    # Categorías conocidas de n1g.cl (se actualizan dinámicamente)
    KNOWN_CATEGORIES = {
        "computacion": "https://n1g.cl/Home/2-computacion",
        "componentes": "https://n1g.cl/Home/6-componentes",
        "perifericos": "https://n1g.cl/Home/7-perifericos",
        "monitores": "https://n1g.cl/Home/8-monitores",
        "notebooks": "https://n1g.cl/Home/9-notebooks",
        "almacenamiento": "https://n1g.cl/Home/10-almacenamiento",
        "redes": "https://n1g.cl/Home/11-redes",
        "gaming": "https://n1g.cl/Home/12-gaming",
        "impresoras": "https://n1g.cl/Home/13-impresoras",
        "accesorios": "https://n1g.cl/Home/14-accesorios",
    }
    
    custom_settings = {
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "CONCURRENT_REQUESTS": 2,  # Más conservador para evitar bloqueos
        "DOWNLOAD_DELAY": 1,  # Delay entre requests
    }

    def __init__(self, max_pages=None, categories=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_pages = int(max_pages) if max_pages else None
        self.categories_data = {}  # {categoria: [productos]}
        self.stats = {
            "categories_scraped": 0,
            "products_scraped": 0,
            "start_time": datetime.now().isoformat(),
        }
        
        # Filtrar categorías si se especifican
        if categories:
            cat_list = [c.strip() for c in categories.split(",")]
            self.target_categories = {k: v for k, v in self.KNOWN_CATEGORIES.items() if k in cat_list}
        else:
            self.target_categories = self.KNOWN_CATEGORIES
        
        # Crear directorio de salida
        self.output_dir = Path(__file__).resolve().parents[2] / "data" / "categories"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def start_requests(self):
        """Inicia el scraping de cada categoría"""
        for cat_name, cat_url in self.target_categories.items():
            self.categories_data[cat_name] = []
            self.logger.info(f"🚀 Iniciando categoría: {cat_name}")
            
            yield scrapy.Request(
                cat_url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [PageMethod("wait_for_selector", "body")],
                    "category": cat_name,
                    "page_num": 1,
                },
                callback=self.parse_category,
                errback=self.handle_error,
            )

    def parse_category(self, response):
        """Parsea una página de categoría y extrae links de productos"""
        category = response.meta["category"]
        page_num = response.meta["page_num"]
        
        self.logger.info(f"📂 Parseando {category} - Página {page_num}")
        
        # Extraer links de productos
        product_links = set()
        link_selectors = [
            "a.product::attr(href)",
            "a.product-item::attr(href)",
            "article.product-miniature a::attr(href)",
            "div.product a::attr(href)",
            "h3.product-title a::attr(href)",
        ]
        
        for sel in link_selectors:
            for href in response.css(sel).getall():
                url = response.urljoin(href)
                if url not in product_links and "/Home/" in url:
                    product_links.add(url)
        
        # También buscar por patrón de URL
        for href in response.css("a::attr(href)").getall():
            if re.search(r"/Home/\d+-[a-z]", href):
                url = response.urljoin(href)
                if url not in product_links:
                    product_links.add(url)
        
        self.logger.info(f"   Encontrados {len(product_links)} productos en página {page_num}")
        
        # Generar requests para cada producto
        for url in product_links:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [PageMethod("wait_for_selector", "body")],
                    "category": category,
                },
                callback=self.parse_product,
                errback=self.handle_error,
            )
        
        # Paginación
        if self.max_pages is None or page_num < self.max_pages:
            next_page = response.css("a[rel=next]::attr(href)").get()
            if not next_page:
                next_page = response.css("a.next::attr(href)").get()
            if not next_page:
                # Intentar construir URL de siguiente página
                next_page = response.css(f'a[href*="page={page_num + 1}"]::attr(href)').get()
            
            if next_page:
                yield scrapy.Request(
                    response.urljoin(next_page),
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [PageMethod("wait_for_selector", "body")],
                        "category": category,
                        "page_num": page_num + 1,
                    },
                    callback=self.parse_category,
                    errback=self.handle_error,
                )

    def parse_product(self, response):
        """Extrae datos de un producto individual"""
        category = response.meta["category"]
        
        item = extract_product(response.selector, base_url=response.url)
        
        # Extraer stock
        stock = None
        stock_text = None
        for s in (".si-items::text", ".si-product-page .si-items::text", ".stock::text", ".availability::text"):
            v = response.css(s).get()
            if v:
                stock_text = v
                break
        
        if stock_text:
            m = re.search(r"(\d+)", stock_text.replace(".", ""))
            stock = int(m.group(1)) if m else 1
        
        # Completar item
        item["stock"] = stock
        item["stock_image"] = None
        item["category"] = category
        item["scraped_at"] = datetime.now().isoformat()
        
        # Calcular score
        score = 0
        score += 50 if stock else 0
        
        if item.get("price_content"):
            try:
                numeric_price = float(re.sub(r"[^0-9.]", "", item["price_content"]))
                score += int(50 / (1 + numeric_price / 10000))
            except:
                pass
        
        desc_text = (item.get("titulo") or "") + " " + (item.get("description") or "")
        for kw in ("oferta", "descuento", "nuevo", "rebaja", "promocion"):
            if kw in desc_text.lower():
                score += 10
        
        item["score"] = min(100, score)
        item["precio"] = item.get("price_content") or item.get("price") or None
        
        # Guardar en memoria para JSON por categoría
        if category in self.categories_data:
            self.categories_data[category].append(dict(item))
        
        self.stats["products_scraped"] += 1
        self.logger.info(f"✅ [{category}] {item.get('titulo', 'Sin título')[:50]}...")
        
        yield item

    def handle_error(self, failure):
        """Maneja errores de requests"""
        self.logger.error(f"❌ Error: {failure.value}")

    def closed(self, reason):
        """Al cerrar el spider, guarda JSONs por categoría"""
        self.stats["end_time"] = datetime.now().isoformat()
        self.stats["categories_scraped"] = len([c for c, p in self.categories_data.items() if p])
        
        # Guardar JSON por cada categoría
        for category, products in self.categories_data.items():
            if products:
                output_file = self.output_dir / f"{category}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "category": category,
                        "total_products": len(products),
                        "scraped_at": self.stats["start_time"],
                        "products": products,
                    }, f, ensure_ascii=False, indent=2)
                self.logger.info(f"💾 Guardado: {output_file} ({len(products)} productos)")
        
        # Guardar resumen general
        summary_file = self.output_dir / "_summary.json"
        summary = {
            "stats": self.stats,
            "categories": {
                cat: len(prods) for cat, prods in self.categories_data.items()
            }
        }
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"📊 Resumen guardado en {summary_file}")
        self.logger.info(f"🏁 Scraping completado: {self.stats['products_scraped']} productos en {self.stats['categories_scraped']} categorías")
