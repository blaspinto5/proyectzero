import logging
from pathlib import Path
import scrapy
from scrapy_playwright.page import PageMethod

from .n1g_spider import extract_product


class N1GProductSpider(scrapy.Spider):
    name = "n1g_products"
    custom_settings = {"PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True}}

    def __init__(self, links=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        repo_root = Path(__file__).resolve().parents[2]
        default_links = repo_root / "output" / "links.txt"
        if links:
            self.links_file = Path(links)
        else:
            self.links_file = default_links

        self.start_urls = []
        if self.links_file.exists():
            with self.links_file.open("r", encoding="utf-8") as f:
                for line in f:
                    url = line.strip()
                    if url:
                        self.start_urls.append(url)

    def start_requests(self):
        if not self.start_urls:
            self.logger.error("No links to crawl. Generate links with n1g_links spider.")
            return

        for url in self.start_urls:
            methods = [PageMethod("wait_for_selector", "body")]
            yield scrapy.Request(url, meta={"playwright_page_methods": methods, "playwright": True}, callback=self.parse_product)

    def parse_product(self, response):
        item = extract_product(response.selector, base_url=response.url)
        # attach compatibility fields expected by pipelines
        item["url"] = response.url
        logging.info("Parsed product: %s", item.get("titulo"))
        yield item
