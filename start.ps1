# 🕷️ N1G Scraper - Script de Ejecución Rápida
# Ejecuta este script para iniciar el scraping

param(
    [switch]$Setup,      # Configurar entorno
    [switch]$Quick,      # Modo rápido (2 páginas)
    [string]$Category,   # Categorías específicas
    [switch]$Local,      # Usar HTML local
    [switch]$Help        # Mostrar ayuda
)

# Colores
$colors = @{
    Cyan = "Cyan"
    Green = "Green"
    Yellow = "Yellow"
    Red = "Red"
    Blue = "Blue"
}

function Write-Banner {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                                                               ║" -ForegroundColor Cyan
    Write-Host "║   🕷️  N1G SCRAPER - Web Scraping para n1g.cl                  ║" -ForegroundColor Cyan
    Write-Host "║                                                               ║" -ForegroundColor Cyan
    Write-Host "║   Extrae productos, precios y stock de todas las categorías   ║" -ForegroundColor Cyan
    Write-Host "║                                                               ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Help {
    Write-Host "USO:" -ForegroundColor Yellow
    Write-Host "  .\start.ps1              # Scraping completo de todas las categorías"
    Write-Host "  .\start.ps1 -Setup       # Configurar entorno (instalar dependencias)"
    Write-Host "  .\start.ps1 -Quick       # Modo rápido (solo 2 páginas por categoría)"
    Write-Host "  .\start.ps1 -Category 'gaming,computacion'  # Solo categorías específicas"
    Write-Host "  .\start.ps1 -Local       # Usar HTML local para pruebas"
    Write-Host ""
    Write-Host "EJEMPLOS:" -ForegroundColor Yellow
    Write-Host "  .\start.ps1 -Setup                    # Primera vez: configurar todo"
    Write-Host "  .\start.ps1 -Quick                    # Prueba rápida"
    Write-Host "  .\start.ps1 -Quick -Category gaming   # Probar solo gaming"
    Write-Host ""
}

function Setup-Environment {
    Write-Host "`n🔧 CONFIGURANDO ENTORNO`n" -ForegroundColor Yellow
    
    Write-Host "▶ Instalando dependencias Python..." -ForegroundColor Blue
    pip install -r requirements.txt
    
    Write-Host "`n▶ Instalando navegador Chromium..." -ForegroundColor Blue
    playwright install chromium
    
    Write-Host "`n▶ Configurando base de datos..." -ForegroundColor Blue
    python manage_db.py upgrade 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  (Base de datos ya configurada o usando SQLite)" -ForegroundColor Yellow
    }
    
    Write-Host "`n✓ Entorno configurado correctamente`n" -ForegroundColor Green
}

function Run-Scraper {
    Write-Host "`n🚀 INICIANDO SCRAPING`n" -ForegroundColor Yellow
    
    $args_list = @()
    
    if ($Quick) {
        $args_list += "-a"
        $args_list += "max_pages=2"
        Write-Host "   Modo rápido: máximo 2 páginas por categoría" -ForegroundColor Cyan
    }
    
    if ($Category) {
        $args_list += "-a"
        $args_list += "categories=$Category"
        Write-Host "   Categorías: $Category" -ForegroundColor Cyan
    }
    
    $cmd = "scrapy crawl categories $($args_list -join ' ')"
    Write-Host "   Comando: $cmd" -ForegroundColor Blue
    Write-Host ""
    
    Invoke-Expression $cmd
}

function Show-Results {
    Write-Host "`n📊 RESULTADOS`n" -ForegroundColor Yellow
    
    # Archivos de categorías
    $dataDir = ".\data\categories"
    if (Test-Path $dataDir) {
        $files = Get-ChildItem $dataDir -Filter "*.json"
        Write-Host "   📁 Archivos de categorías: $($files.Count)" -ForegroundColor Green
        foreach ($f in $files) {
            if ($f.Name -ne "_summary.json") {
                Write-Host "      - $($f.Name)"
            }
        }
    }
    
    # Output principal
    $outputDir = ".\output"
    if (Test-Path $outputDir) {
        Write-Host "`n   📁 Archivos de salida:" -ForegroundColor Green
        Get-ChildItem $outputDir | ForEach-Object {
            $size = [math]::Round($_.Length / 1KB, 1)
            Write-Host "      - $($_.Name) ($size KB)"
        }
    }
    
    # Base de datos
    if (Test-Path ".\projectzero.db") {
        $size = [math]::Round((Get-Item ".\projectzero.db").Length / 1KB, 1)
        Write-Host "`n   🗄️ Base de datos: projectzero.db ($size KB)" -ForegroundColor Green
    }
}

# MAIN
Write-Banner

if ($Help) {
    Write-Help
    exit 0
}

# Verificar directorio
if (-not (Test-Path ".\scrapy.cfg")) {
    Write-Host "❌ Error: No se encuentra scrapy.cfg. Ejecuta desde el directorio del proyecto." -ForegroundColor Red
    exit 1
}

if ($Setup) {
    Setup-Environment
    exit 0
}

Run-Scraper
Show-Results

Write-Host "`n✅ Scraping completado`n" -ForegroundColor Green
