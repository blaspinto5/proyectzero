import scrapy
from scrapy_playwright.page import PageMethod


class MiSpider(scrapy.Spider):
    name = "mi_spider"

    def start_requests(self):
        url = "https://httpbin.org/html"
        yield scrapy.Request(
            url,
            meta={
                "playwright": True,
                "playwright_page_methods": [PageMethod("wait_for_selector", "h1")],
            },
            callback=self.parse,
        )

    def parse(self, response):
        yield {
            "url": response.url,
            "titulo": response.css("h1::text").get(),
        }
