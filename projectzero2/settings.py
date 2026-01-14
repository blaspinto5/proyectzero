# Scrapy settings for projectzero2

BOT_NAME = "projectzero2"

SPIDER_MODULES = ["projectzero2.spiders"]
NEWSPIDER_MODULE = "projectzero2.spiders"

# Download handlers for scrapy-playwright
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# `scrapy_playwright` recent releases provide a download handler instead of a
# separate middleware module. The middleware module may be missing in the
# installed package, so we avoid referencing it here to prevent import errors.
# If you install a version that exposes `scrapy_playwright.middleware`, you
# can re-enable a middleware entry as needed.

PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True}
CONCURRENT_REQUESTS = 4
LOG_LEVEL = "INFO"

# Pipelines: normalize first, then persist to Postgres, CSV and JSON
ITEM_PIPELINES = {
    "projectzero2.pipelines.NormalizeItemPipeline": 100,
    "projectzero2.pipelines.ScorePipeline": 150,
    "projectzero2.pipelines.PostgresPipeline": 200,
    "projectzero2.pipelines.CsvPipeline": 300,
    "projectzero2.pipelines.JsonIncrementalPipeline": 400,
}

# Output locations (mount /data in Docker)
JSON_OUTPUT_FILE = "/data/output.json"
CSV_OUTPUT_FILE = "/data/output.csv"

# Database URL (override via env var). If not set, fall back to a local SQLite file
# For full production use PostgreSQL and set DATABASE_URL accordingly.
import os
DATABASE_URL = os.environ.get("DATABASE_URL") if os.environ.get("DATABASE_URL") else "sqlite:///./projectzero.db"
