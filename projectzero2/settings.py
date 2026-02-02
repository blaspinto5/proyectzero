# Scrapy settings for projectzero2

BOT_NAME = "projectzero2"

SPIDER_MODULES = ["projectzero2.spiders"]
NEWSPIDER_MODULE = "projectzero2.spiders"

import os

# Allow disabling scrapy-playwright explicitly via env var for local/testing.
if os.environ.get("DISABLE_PLAYWRIGHT") == "1":
    DOWNLOAD_HANDLERS = {}
else:
    # Download handlers for scrapy-playwright (only configure if available)
    try:
        import scrapy_playwright  # type: ignore

        DOWNLOAD_HANDLERS = {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        }
        TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
    except Exception:
        # scrapy-playwright not available or incompatible in this environment;
        # fall back to default HTTP download handlers so spiders can run without JS rendering.
        DOWNLOAD_HANDLERS = {}
        # use default reactor (don't override)

# `scrapy_playwright` recent releases provide a download handler instead of a
# separate middleware module. The middleware module may be missing in the
# installed package, so we avoid referencing it here to prevent import errors.
# If you install a version that exposes `scrapy_playwright.middleware`, you
# can re-enable a middleware entry as needed.

PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True}
CONCURRENT_REQUESTS = 4
LOG_LEVEL = "INFO"

# User agent and headers to avoid bot detection
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
}

# Allow 406 responses to be processed
HTTPERROR_ALLOWED_CODES = [406]

# Pipelines: normalize first, then persist to Postgres, CSV and JSON
ITEM_PIPELINES = {
    "projectzero2.pipelines.NormalizeItemPipeline": 100,
    "projectzero2.pipelines.ScorePipeline": 150,
    "projectzero2.pipelines.PostgresPipeline": 200,
    "projectzero2.pipelines.CsvPipeline": 300,
    "projectzero2.pipelines.JsonIncrementalPipeline": 400,
}

# Output locations - use env vars or defaults that work locally and in Docker
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent
_output_dir = _project_root / "output"
_data_dir = _project_root / "data"

# Asegurar que los directorios existen
_output_dir.mkdir(exist_ok=True)
_data_dir.mkdir(exist_ok=True)
(_data_dir / "categories").mkdir(exist_ok=True)

JSON_OUTPUT_FILE = os.environ.get("JSON_OUTPUT_FILE", str(_output_dir / "output.json"))
CSV_OUTPUT_FILE = os.environ.get("CSV_OUTPUT_FILE", str(_output_dir / "output.csv"))

# Database URL (override via env var). If not set, fall back to a local SQLite file
# For full production use PostgreSQL and set DATABASE_URL accordingly.
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{_project_root}/projectzero.db")

# Retry configuration for resilience
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Download delay to be respectful
DOWNLOAD_DELAY = 0.5
RANDOMIZE_DOWNLOAD_DELAY = True
