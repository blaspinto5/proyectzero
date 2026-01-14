param(
    [switch]$Install,
    [switch]$Playwright,
    [switch]$Test,
    [switch]$Migrate,
    [switch]$RunMi,
    [switch]$RunN1G
)

function Activate-Venv {
    $venv = Join-Path $PSScriptRoot '.venv\Scripts\Activate.ps1'
    if (-Not (Test-Path $venv)) {
        python -m venv .venv
    }
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    . .\.venv\Scripts\Activate.ps1
}

if ($Install) {
    Activate-Venv
    pip install --upgrade pip
    pip install -r requirements.txt
}
if ($Playwright) {
    Activate-Venv
    python -m playwright install --with-deps chromium
}
if ($Test) {
    Activate-Venv
    pytest -q
}
if ($Migrate) {
    Activate-Venv
    alembic -c alembic.ini upgrade head
}
if ($RunMi) {
    Activate-Venv
    scrapy crawl mi_spider
}
if ($RunN1G) {
    Activate-Venv
    scrapy crawl n1g_spider -a urls="https://n1g.cl/Home/2-computacion"
}
