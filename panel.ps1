# 🖥️ N1G Scraper - Abrir Panel de Visualización
# Ejecuta este script para abrir el frontend

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                               ║" -ForegroundColor Cyan
Write-Host "║   🖥️  N1G SCRAPER - Panel de Visualización                    ║" -ForegroundColor Cyan
Write-Host "║                                                               ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Verificar dependencias
$hasCustomTkinter = pip show customtkinter 2>$null
if (-not $hasCustomTkinter) {
    Write-Host "📦 Instalando dependencias del frontend..." -ForegroundColor Yellow
    pip install customtkinter Pillow
}

Write-Host "🚀 Iniciando panel de visualización..." -ForegroundColor Green
Write-Host ""

# Ejecutar aplicación
python -m frontend.app
