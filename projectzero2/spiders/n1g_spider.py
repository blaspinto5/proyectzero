import re
import urllib.parse
import scrapy
from scrapy_playwright.page import PageMethod


def parse_price(text):
    if not text:
        return None
    s = re.sub(r"[^0-9,\.]+", "", text)
    # Handle both EU (1.234,56) and US (1,234.56) formats.
    if "." in s and "," in s:
        # the last separator is most likely the decimal separator
        if s.rfind(",") > s.rfind("."):
            # comma as decimal: remove dots (thousands) and replace comma with dot
            s = s.replace(".", "").replace(",", ".")
        else:
            # dot as decimal: remove commas (thousands)
            s = s.replace(",", "")
    else:
        # single separator present or none: try to decide whether separator is thousands or decimal
        if "," in s and "." not in s:
            parts = s.split(",")
            # if comma groups indicate thousands (3-digit group) treat as thousands separator
            if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
                s = s.replace(",", "")
            else:
                s = s.replace(",", ".")
        elif "." in s and "," not in s:
            parts = s.split(".")
            # treat like thousands separator when fractional group length is 3 (e.g. '1.234')
            if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
                s = s.replace(".", "")
            else:
                s = s
        else:
            s = s
    try:
        return float(s)
    except Exception:
        try:
            return float(re.findall(r"\d+", s)[0])
        except Exception:
            return None


def extract_product(selector, base_url=None):
    def first(selectors):
        for s in selectors:
            v = selector.css(s).get()
            if v:
                return v.strip()
        return None

    title = first(["h1.product_name::text", "h1[itemprop='name']::text", "h1::text", "h1.product-title::text"]) or selector.css("title::text").get()

    # price: raw visible text and a content attr fallback used by some templates
    price = first(["div.product-prices .current-price span.price::text", "span.price::text", "span.regular-price::text"]) or None
    price_content = selector.css("div.product-prices .current-price span.price::attr(content)").get() or selector.css("meta[property='product:price:amount']::attr(content)").get()

    # prefer the full HTML block and extract its visible text
    desc_html = selector.css("div[id^='product-description-short']").get()
    if desc_html:
        from parsel import Selector as ParselSelector

        try:
            description = ParselSelector(desc_html).xpath('string(.)').get().strip()
        except Exception:
            description = ""
    else:
        description = first(["div.product-description::text", "#description::text", ".description::text"]) or ""

    images = selector.css("ul.product-images img.thumb::attr(data-image-large-src)").getall()
    if not images:
        images = selector.css("ul.product-images img.thumb::attr(src)").getall()
    if not images:
        images = selector.css("div.product-cover img::attr(src)").getall()

    # join relative URLs when base_url provided
    if base_url and images:
        images = [urllib.parse.urljoin(base_url, x) for x in images]

    return {
        "url": base_url or None,
        "titulo": title.strip() if title else None,
        "price": price.strip() if isinstance(price, str) else price,
        "price_content": price_content,
        "description": description.strip() if description else None,
        "images": images,
    }


class N1GSpider(scrapy.Spider):
    name = "n1g_spider"
    custom_settings = {"PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True}}

    def __init__(self, urls=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if urls:
            # allow passing comma-separated URLs via `-a urls="url1,url2"`
            self.start_urls = [u.strip() for u in urls.split(",") if u.strip()]
        else:
            # default to the computacion category as requested
            self.start_urls = ["https://n1g.cl/Home/2-computacion"]

    def start_requests(self):
        for url in self.start_urls:
            # wait for stock element (rendered dynamically) or fallback to body
            # Wait for body only to avoid timeouts when site blocks or changes
            methods = [PageMethod("wait_for_selector", "body")]
            yield scrapy.Request(
                url,
                meta={"playwright": True, "playwright_page_methods": methods},
                callback=self.parse,
            )

    def parse(self, response):
        # try multiple selectors to find product links
        link_selectors = [
            "a.product::attr(href)",
            "a.product-item::attr(href)",
            "a.card::attr(href)",
            "div.product a::attr(href)",
            "div.product-item a::attr(href)",
        ]
        seen = set()
        for sel in link_selectors:
            for href in response.css(sel).getall():
                url = response.urljoin(href)
                if url not in seen:
                    seen.add(url)
                    methods = [PageMethod("wait_for_selector", "body")]
                    yield scrapy.Request(url, meta={"playwright": True, "playwright_page_methods": methods, "playwright_include_page": False}, callback=self.parse_product)

        # fallback: collect anchors that look like product pages (heuristic)
        for href in response.css("a::attr(href)").getall():
            if "/producto" in href or "/productos" in href or "/producto/" in href:
                url = response.urljoin(href)
                if url not in seen:
                    seen.add(url)
                    methods = [PageMethod("wait_for_selector", "body")]
                    yield scrapy.Request(url, meta={"playwright": True, "playwright_page_methods": methods, "playwright_include_page": False}, callback=self.parse_product)

        # pagination
        next_sel = response.css("a[rel=next]::attr(href)").get() or response.css("a.next::attr(href)").get()
        if next_sel:
            yield scrapy.Request(response.urljoin(next_sel), callback=self.parse)

    def parse_product(self, response):
        sel = response.selector
        item = extract_product(sel, base_url=response.url)

        # stock extraction (keep earlier heuristics)
        stock = None
        stock_text = None
        for s in (".si-items::text", ".si-product-page .si-items::text", ".si-items", ".stock::text", ".availability::text", ".disponible::text"):
            v = response.css(s).get()
            if v:
                stock_text = v
                break
        if stock_text:
            m = re.search(r"(\d+)", stock_text.replace(".", ""))
            if m:
                try:
                    stock = int(m.group(1))
                except Exception:
                    stock = None
            else:
                stock = 1

        # attach stock and compatibility fields expected elsewhere
        item["stock"] = stock
        item["stock_image"] = None

        # category heuristic
        category = response.css(".breadcrumb a::text").getall()
        item["category"] = category[-1].strip() if category else None

        # compute a basic score: availability + inverse price + promo keywords
        score = 0
        score += 50 if stock else 0
        numeric_price = None
        if item.get("price_content"):
            try:
                numeric_price = float(re.sub(r"[^0-9.]", "", item["price_content"]))
            except Exception:
                numeric_price = None
        if numeric_price:
            score += int(50 / (1 + numeric_price))
        promo = 0
        desc_text = (item.get("titulo") or "") + " " + (item.get("description") or "")
        for kw in ("oferta", "descuento", "nuevo", "rebaja", "promocion"):
            if kw in desc_text.lower():
                promo += 10
        score = min(100, score + promo)
        item["score"] = score

        # keep compatibility key name used by pipelines
        item["precio"] = item.get("price") or None

        yield item
