<#
run_local.ps1 - prepara un entorno Python local y ejecuta el spider n1g_spider

Uso:
  .\run_local.ps1                 # instala deps (si hace falta) y ejecuta n1g_spider en SQLite
  .\run_local.ps1 -Url <categoria_url>

Requisitos:
- Windows PowerShell con Python 3.10+ en PATH
- Permisos para ejecutar scripts (Set-ExecutionPolicy RemoteSigned -Scope CurrentUser)
#>
param(
    [string]$Url = "https://n1g.cl/Home/2-computacion",
    [switch]$ReinstallDependencies = $false
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# crear output
if (-not (Test-Path .\output)) { New-Item -ItemType Directory -Path .\output | Out-Null }

# crear/activar virtualenv
$venvPath = Join-Path $root ".venv"
if (-not (Test-Path $venvPath) -or $ReinstallDependencies) {
    Write-Host "Creando virtualenv en $venvPath..."
    python -m venv $venvPath
}

# activation script path for PowerShell
$activate = Join-Path $venvPath "Scripts\Activate.ps1"
if (-not (Test-Path $activate)) {
    Write-Error "No pude encontrar el script de activación: $activate. Asegúrate de tener Python instalado y venv disponible."
    exit 1
}

Write-Host "Activando virtualenv..."
. $activate

Write-Host "Actualizando pip..."
python -m pip install --upgrade pip

if ($ReinstallDependencies) {
    Write-Host "Instalando dependencias desde requirements.txt (puede tardar)..."
    pip install -r requirements.txt
}

# siempre aseguramos que scrapy-playwright y playwright estén instalados
Write-Host "Instalando/asegurando scrapy-playwright y Playwright..."
pip install scrapy-playwright playwright --upgrade

# instalar navegadores de Playwright (Chromium)
Write-Host "Instalando navegadores Playwright (chromium)..."
python -m playwright install chromium

# Ejecutar spider con SQLite (configuración por defecto en settings.py usa sqlite si no hay DATABASE_URL)
Write-Host "Ejecutando spider n1g_spider para: $Url"
# crear carpeta output si no existe (de nuevo)
if (-not (Test-Path .\output)) { New-Item -ItemType Directory -Path .\output | Out-Null }

# Ejecutar con Scrapy
scrapy crawl n1g_spider -a urls="$Url"
$rc = $LASTEXITCODE

if ($rc -ne 0) {
    Write-Error "El spider terminó con código $rc. Revisa la salida para errores."
    exit $rc
}

Write-Host "Spider finalizó correctamente. Resumen de salida (últimas 80 líneas de output.json si existe):"
if (Test-Path .\output\output.json) {
    Get-Content .\output\output.json -Tail 80
} else {
    Write-Host "No se encontró ./output/output.json. Lista ./output:" 
    Get-ChildItem .\output | Format-Table -AutoSize
}

Write-Host "La base de datos SQLite (si se usó) está en projectzero.db en la raíz del proyecto."
Write-Host "Si quieres usar Postgres en local, exporta DATABASE_URL y ejecuta el mismo comando dentro del venv:"
Write-Host "  $env:DATABASE_URL = 'postgresql://user:pass@localhost:5432/projectzero' ; scrapy crawl n1g_spider -a urls=..."

exit 0
