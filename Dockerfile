FROM python:3.11-slim-bullseye

ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential wget ca-certificates gnupg \
    libnss3 libxss1 libasound2 libatk1.0-0 libatk-bridge2.0-0 libc6 libgbm1 libgtk-3-0 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install playwright browsers and deps
RUN python -m playwright install --with-deps chromium

# non-root user
RUN useradd -m scrapper
USER scrapper

COPY --chown=scrapper:scrapper . /app

CMD ["scrapy", "crawl", "mi_spider"]
