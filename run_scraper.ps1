# run_scraper.ps1
# Starts Docker Desktop if needed, waits for docker daemon, builds the images,
# runs the n1g_spider for the computacion category and shows output.

param(
    [string]$CategoryUrl = "https://n1g.cl/Home/2-computacion",
    [int]$WaitSecondsForDocker = 180
)

function Test-Docker {
    try {
        docker info > $null 2>&1
        return $true
    } catch {
        return $false
    }
}

Write-Host "Ensuring output folder exists..."
$proj = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $proj
if (-not (Test-Path .\output)) { New-Item -ItemType Directory -Path .\output | Out-Null }

if (-not (Test-Docker)) {
    Write-Host "Docker daemon no responde. Intentando iniciar Docker Desktop..."
    # common install paths
    $candidates = @(
        "C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe",
        "C:\\Program Files (x86)\\Docker\\Docker\\Docker Desktop.exe"
    )
    $started = $false
    foreach ($c in $candidates) {
        if (Test-Path $c) {
            Write-Host "Iniciando: $c"
            Start-Process -FilePath $c -WindowStyle Hidden
            $started = $true
            break
        }
    }
    if (-not $started) {
        Write-Host "No encontré Docker Desktop en rutas comunes. Intenta abrir Docker Desktop manualmente y vuelve a ejecutar este script."
    }

    Write-Host "Esperando a que Docker responda (timeout $WaitSecondsForDocker s)..."
    $start = Get-Date
    while (-not (Test-Docker)) {
        Start-Sleep -Seconds 2
        if ((Get-Date) - $start -gt ([TimeSpan]::FromSeconds($WaitSecondsForDocker))) {
            Write-Error "Timeout esperando Docker. Revisa que Docker Desktop esté iniciado."
            exit 1
        }
    }
    Write-Host "Docker listo."
} else {
    Write-Host "Docker daemon ya está corriendo."
}

# Build and run with docker compose
Write-Host "Construyendo imágenes y levantando servicios (detached)..."
docker compose up --build -d
if ($LASTEXITCODE -ne 0) {
    Write-Error "docker compose up falló. Revisa la salida anterior."
    exit 1
}

Write-Host "Ejecutando spider n1g_spider para: $CategoryUrl"
# run the spider (will print logs to terminal)
docker compose run --rm app scrapy crawl n1g_spider -a urls="$CategoryUrl"
$rc = $LASTEXITCODE
if ($rc -ne 0) {
    Write-Error "El spider terminó con código $rc. Revisa logs: docker compose logs app --tail 200"
} else {
    Write-Host "Spider finalizado correctamente."
}

Write-Host "Mostrando resumen de output/"
if (Test-Path .\output\output.json) {
    Write-Host "output/output.json:"
    Get-Content .\output\output.json -Tail 80
} else {
    Write-Host "No se encontró ./output/output.json. Lista de ./output:" 
    Get-ChildItem .\output
}

Write-Host "Puedes ver logs en vivo con: docker compose logs --follow app"

exit $rc
