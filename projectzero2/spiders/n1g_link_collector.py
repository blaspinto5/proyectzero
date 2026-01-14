import logging
from pathlib import Path
import scrapy
from scrapy_playwright.page import PageMethod


class N1GLinkCollector(scrapy.Spider):
    name = "n1g_links"
    custom_settings = {"PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True}}

    def __init__(self, urls=None, out=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if urls:
            self.start_urls = [u.strip() for u in urls.split(",") if u.strip()]
        else:
            self.start_urls = ["https://n1g.cl/Home/2-computacion"]

        # output file for links
        repo_root = Path(__file__).resolve().parents[2]
        self.out_path = Path(out) if out else repo_root / "output" / "links.txt"
        self.out_path.parent.mkdir(parents=True, exist_ok=True)

        # in-memory dedupe
        self.seen = set()

    def start_requests(self):
        for url in self.start_urls:
            # send common browser headers to avoid 406/blocks and keep resilient
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            # lightweight render wait; keep resilient if playwright not available
            methods = [PageMethod("wait_for_selector", "body")]
            yield scrapy.Request(url, headers=headers, meta={"playwright_page_methods": methods, "playwright": True}, callback=self.parse)

    def parse(self, response):
        link_selectors = [
            "a.product::attr(href)",
            "a.product-item::attr(href)",
            "div.product a::attr(href)",
            "ul.products li a::attr(href)",
        ]

        new = 0
        for sel in link_selectors:
            for href in response.css(sel).getall():
                url = response.urljoin(href)
                if url not in self.seen:
                    self.seen.add(url)
                    new += 1
                    # append to file immediately to be safe across runs
                    with self.out_path.open("a", encoding="utf-8") as f:
                        f.write(url + "\n")

        logging.info("Found %d new links on %s", new, response.url)

        # follow pagination
        next_sel = response.css("a[rel=next]::attr(href)").get() or response.css("a.next::attr(href)").get()
        if next_sel:
            yield response.follow(next_sel, callback=self.parse)
