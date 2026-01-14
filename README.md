Projectzero2 — Scrapy + Playwright + PostgreSQL

Estructura creada dentro de `projectzero2`:
- `projectzero2/` paquete Scrapy con `settings.py`, `pipelines.py`, `spiders/mi_spider.py`, `items.py`.
- `Dockerfile`, `docker-compose.yml`, `requirements.txt`.

Qué hace el proyecto
- El spider `mi_spider` visita `https://httpbin.org/html` (ejemplo) y extrae: `url` y `titulo`.
- Las pipelines persisten los items en tres destinos (orden configurado en `settings.py`):
  - `PostgresPipeline`: inserta/actualiza en la tabla `items` de PostgreSQL (columnas: `id`, `url`, `titulo`, `precio`, `stock`, `raw`).
  - `CsvPipeline`: añade filas a `/data/output.csv` (evita duplicados por `url`).
  - `JsonIncrementalPipeline`: mantiene `/data/output.json` con todos los items (escritura atómica).

Campos obtenidos (ejemplo)
- `url`: URL de la página scrapeada.
- `titulo` (o `titulo`): título extraído del HTML (`h1` en el ejemplo).
- `precio`: campo preparado para sites de e-commerce (si tu spider extrae `precio`).
- `stock`: campo preparado para disponibilidad (si tu spider extrae `stock`).
- `raw`: JSON con el item completo guardado en la BD para referencia.

Construir y arrancar con Docker Compose (levanta Postgres y la app):

```powershell
cd "C:\Users\Peruano Pinto\Desktop\proyectZERO\projectzero2"
docker compose up --build
```

Esto crea el servicio `db` (Postgres) y `app`. El `app` usa `DATABASE_URL` apuntando al servicio `db`.

Persistencia en host
- Para acceder a los outputs en tu máquina, mueve el directorio `output` fuera o monta el volumen:

```powershell
# ejemplo: crea carpeta output y monta en /data
mkdir output
docker compose up --build
```

El `CsvPipeline` y `JsonIncrementalPipeline` escribirán en `./output/output.csv` y `./output/output.json`.

Notas y siguientes pasos
- Si vas a scrapear sitios reales, adapta `mi_spider` con los selectores correctos (`titulo`, `precio`, `stock`).
- Puedes añadir índices adicionales o normalizar datos antes de insertarlos (por ejemplo transformar `precio` a número).
- Para esquemas más complejos crear modelos con SQLAlchemy declarative y migraciones (Alembic).

¿Deseas que:
- adapte el spider para un site objetivo y los selectores reales?
- añada migraciones con Alembic y scripts de inicialización?
- exponga un pequeño script `manage_db.py` para consultar la BD desde el proyecto?
 - exponga un pequeño script `manage_db.py` para consultar la BD desde el proyecto? (ya añadido)

Gestión de la base de datos y outputs

He añadido `manage_db.py` en la raíz del proyecto. Ejemplos de uso:

```powershell
# eliminar los ficheros de salida
python manage_db.py --clean-output

# truncar la tabla items (mantiene esquema)
python manage_db.py --wipe-db --db postgresql://postgres:postgres@db:5432/projectzero

# borrar la tabla items
python manage_db.py --drop-db --db postgresql://postgres:postgres@db:5432/projectzero
```

Nota: ejecuta esos comandos desde dentro del contenedor o desde un entorno con acceso a la BD (por ejemplo ejecutar `docker compose run --rm app python manage_db.py ...` si usas docker-compose).

Nuevo spider para n1g.cl

He añadido `n1g_spider` para extraer productos desde `https://n1g.cl/Home/`.

Campos extraídos por defecto:
- `url`: URL del producto.
- `titulo`: título del producto.
- `precio`: precio como número (si se detecta).
- `stock`: 1 si parece disponible, 0 si aparece como agotado.
- `category`: categoría principal (si hay breadcrumbs).
- `description`: texto descriptivo.
- `images`: lista de URLs de imágenes encontradas en la página.
- `score`: calificación numérica (0-100) para priorizar/buscar rápidamente.

Scoring mejorado y campos adicionales

He mejorado la heurística de `score` para que la calificación sea más útil sin convertir `precio`:

- `stock`: si es un número lo uso como señal principal (hasta +50 puntos). Si solo aparece texto positivo, suma +40.
- `images`: cada imagen suma hasta +20 puntos (máx. 4 imágenes * 5 puntos).
- `description`: longitud de la descripción aporta hasta +15 puntos.
- `promo keywords`: palabras como `oferta`, `descuento`, `rebaja`, `pack` suman puntos.
- `precio`: se mantiene como cadena sin conversión (lo solicitaste). No se usa como número, solo su existencia puede ser señal.

Nuevo campo `stock_image`:

- El spider extrae `stock_image` buscando imágenes cercanas al indicador de stock (`.si-outer img`, `.product-stock img`, etc.). Este campo contiene la URL absoluta de la imagen relacionada al stock (si existe), para usar en interfaces o reportes más profesionales.

Ejecución recomendada para la categoría `computacion`:

```powershell
docker compose run --rm app scrapy crawl n1g_spider -a urls="https://n1g.cl/Home/2-computacion"
```

Salida y verificación
- `./output/output.json`: lista completa de items con `score` y `stock_image`.
- `./output/output.csv`: CSV con campos principales.
- BD Postgres: tabla `items` con columna `raw` que contiene el item completo en JSON.

Si quieres que ajuste la heurística (por ejemplo dar más peso a descuentos reales detectados por la presencia de precio anterior tachado), pásame HTML de un producto con esos elementos y lo adapto exactamente.

Ejecución local sin Docker

He añadido `run_local.ps1` en la raíz del proyecto para preparar un `virtualenv`, instalar Playwright y sus navegadores, y ejecutar el spider en modo local usando SQLite (por defecto).
# Projectzero2 — Scrapy + Playwright + PostgreSQL

¡Bienvenido a Projectzero2! Aquí tenemos un scraper elegante y práctico que usa Scrapy y Playwright para extraer productos y datos desde páginas dinámicas, normalizarlos y guardarlos en varios destinos.

**Estado actual**
- Spiders: `mi_spider` (demo) y `n1g_spider` (n1g.cl extractor).
- Pipelines: normalización, scoring, Postgres upsert (o SQLite fallback), CSV y JSON incremental atómico.
- Tests: suite con `pytest` que cubre parsers y pipelines.

[![CI](https://github.com/blaspinto5/proyectzero/actions/workflows/ci.yml/badge.svg)](https://github.com/blaspinto5/proyectzero/actions)
[![Pytest](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/blaspinto5/proyectzero/actions)

![demo](demo.svg)

¿Por qué usar este proyecto?
- Combina renderizado headless (Playwright) con la potencia de Scrapy.
- Persistencia robusta: upsert en Postgres y salidas CSV/JSON limpias.
- Preparado para CI y migraciones (Alembic ya configurado).

-----

## Rápido — Ejecutar en Windows (PowerShell)

1) Clona y entra en el proyecto:

```powershell
cd "C:\Users\Peruano Pinto\Desktop\proyectZERO\projectzero2"
```

2) Virtualenv y dependencias:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

3) Instala navegadores Playwright (recomendado):

```powershell
python -m playwright install --with-deps chromium
```

4) Prepara la carpeta de salida (opcional):

```powershell
mkdir output
```

5) Ejecuta un spider:

```powershell
# demo
scrapy crawl mi_spider

# n1g (ejemplo de categoría)
scrapy crawl n1g_spider -a urls="https://n1g.cl/Home/2-computacion"
```

Salida local por defecto:
- `./output/output.json` — JSON incremental (escritura atómica).
- `./output/output.csv` — CSV deduplicado.
- `projectzero.db` — SQLite fallback si no hay `DATABASE_URL`.

-----

## Ejecutar con Docker (rápido)

```powershell
docker compose up --build

# ejecutar un spider puntual dentro del contenedor
docker compose run --rm app scrapy crawl n1g_spider -a urls="https://n1g.cl/Home/2-computacion"
```

El contenedor `app` ya instala Playwright y Chromium en build.

-----

## Migraciones (Alembic)

Alembic está configurado. Por defecto apunta a `sqlite:///./projectzero.db`. Para aplicar la migración inicial:

```powershell
# opcional: usar Postgres
$env:DATABASE_URL = "postgresql://postgres:postgres@db:5432/projectzero"
alembic -c alembic.ini upgrade head
```

-----

## Tests

Ejecuta la suite de tests locales:

```powershell
pytest -q
```

Los tests verifican parsers (`parse_price`), `NormalizeItemPipeline`, `ScorePipeline`, `PostgresPipeline` (SQLite in-memory), `CsvPipeline` y `JsonIncrementalPipeline`.

-----

## Esquema de `items` (ejemplo y explicación)

Campos principales (tabla `items`):

- `id` (int): identificador autoincremental asignado por la BD.
- `url` (string): URL única del producto.
- `titulo` (text): título o nombre del producto.
- `precio` (text): precio tal cual se extrajo (cadena). Puedes normalizarlo si lo deseas.
- `stock` (text): valor numérico o indicador de disponibilidad.
- `raw` (text): JSON serializado con el item completo para referencia.

Ejemplo de objeto JSON que se guarda dentro de `raw`:

```json
{
  "url": "https://n1g.cl/producto/ejemplo",
  "titulo": "Placa madre XYZ",
  "precio": "$ 129.990",
  "stock": 5,
  "stock_image": "https://n1g.cl/media/stock-badge.png",
  "category": "Computación",
  "description": "Placa madre compatible con...",
  "images": ["https://n1g.cl/media/1.jpg", "https://n1g.cl/media/2.jpg"],
  "score": 78
}
```

Nota: `PostgresPipeline` guarda la representación completa en `raw` y además mantiene columnas principales para búsquedas y ordenación rápidas.

-----

## CI

Incluí un workflow de GitHub Actions en `.github/workflows/ci.yml` que instala dependencias, Playwright y ejecuta `pytest`.

-----

## Archivos clave
- `projectzero2/settings.py` — configuración Scrapy y pipelines.
- `projectzero2/pipelines.py` — normalización, scoring y persistencia.
- `projectzero2/spiders/n1g_spider.py` — extractor principal y `parse_price`.
- `manage_db.py` — utilidades para limpiar outputs y manejar la tabla `items`.
- `alembic/` — configuración y migración inicial.

-----

¿Quieres que deje este `README` también en inglés, o que añada ejemplos con HTML de producto reales para ajustar selectores? Si quieres, puedo además:

- Añadir badges y un GIF corto mostrando el scraper en acción.
- Documentar el esquema de la tabla `items` con ejemplos JSON.
- Preparar un `Makefile` o script `inv` para comandos frecuentes.

¡Dime qué prefieres y lo hago!
