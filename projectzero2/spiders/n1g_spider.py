import re
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
        def first(selectors):
            for s in selectors:
                v = response.css(s).get()
                if v:
                    return v.strip()
            return None

        title = first(["h1::text", "h1.product-title::text", ".product-title::text", ".titulo::text", ".title::text"]) or response.css("title::text").get()
        # keep raw price string (do not convert as requested)
        price_raw = first([".price::text", ".product-price::text", ".precio::text", ".price-number::text"]) or response.css("meta[property='product:price:amount']::attr(content)").get()
        price = price_raw.strip() if price_raw else None

        # stock: try to read explicit stock count rendered dynamically
        stock_text = None
        for s in (".si-items::text", ".si-product-page .si-items::text", ".si-items", ".stock::text", ".availability::text", ".disponible::text"):
            v = response.css(s).get()
            if v:
                stock_text = v
                break

        stock = None
        if stock_text:
            # extract digits
            m = re.search(r"(\d+)", stock_text.replace(".", ""))
            if m:
                try:
                    stock = int(m.group(1))
                except Exception:
                    stock = None
            else:
                # heuristic: presence of text means available
                stock = 1

        category = response.css(".breadcrumb a::text").getall()
        category = category[-1].strip() if category else None
        description = first([".description::text", ".product-description::text", "#description::text"]) or ""
        images = [response.urljoin(x) for x in response.css("img::attr(src)").getall()]

        # attempt to extract a stock-related image (e.g. progress bar or badge near stock element)
        stock_image = None
        stock_img_sel_candidates = [
            ".si-outer img::attr(src)",
            ".si-product-page .si-outer img::attr(src)",
            ".stock img::attr(src)",
            ".product-stock img::attr(src)",
        ]
        for s in stock_img_sel_candidates:
            v = response.css(s).get()
            if v:
                stock_image = response.urljoin(v)
                break

        item = {
            "url": response.url,
            "titulo": title,
            # raw price string kept
            "precio": price,
            "stock": stock,
            "stock_image": stock_image,
            "category": category,
            "description": description.strip() if description else None,
            "images": images,
        }

        # compute a basic score: availability + inverse price + promo keywords
        score = 0
        score += 50 if stock else 0
        if price:
            score += int(50 / (1 + price))  # lower price => higher contribution
        promo = 0
        desc_text = (title or "") + " " + (description or "")
        for kw in ("oferta", "descuento", "nuevo", "rebaja", "promocion"):
            if kw in desc_text.lower():
                promo += 10
        score = min(100, score + promo)
        item["score"] = score

        yield item
