VENV=.venv
PY=python
PIP=$(VENV)/Scripts/pip.exe
ACTIVATE=$(VENV)/Scripts/Activate.ps1

.PHONY: venv install play install-play test migrate run mi n1g clean

venv:
	$(PY) -m venv $(VENV)

install: venv
	Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; & $(ACTIVATE); $(PIP) install --upgrade pip; $(PIP) install -r requirements.txt

install-play:
	& $(ACTIVATE); python -m playwright install --with-deps chromium

test:
	& $(ACTIVATE); pytest -q

migrate:
	& $(ACTIVATE); alembic -c alembic.ini upgrade head

run-mi:
	& $(ACTIVATE); scrapy crawl mi_spider

run-n1g:
	& $(ACTIVATE); scrapy crawl n1g_spider -a urls="https://n1g.cl/Home/2-computacion"

clean:
	rm -rf output/*.json output/*.csv projectzero.db
