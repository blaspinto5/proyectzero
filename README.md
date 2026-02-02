<div align="center">

# 🕷️ N1G Scraper

### Web Scraping Profesional para n1g.cl

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Scrapy](https://img.shields.io/badge/Scrapy-2.13-60A839?style=for-the-badge&logo=scrapy&logoColor=white)](https://scrapy.org)
[![Playwright](https://img.shields.io/badge/Playwright-1.47-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)](https://playwright.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)

<br>

**Extrae productos, precios, stock e imágenes de todas las categorías de n1g.cl**

[🚀 Inicio Rápido](#-inicio-rápido) •
[� Requisitos](#-requisitos-del-sistema) •
[📖 Documentación](#-documentación) •
[🏗️ Arquitectura](#️-arquitectura)

</div>

---

## 📋 Requisitos del Sistema

> ⚠️ **IMPORTANTE:** Asegúrate de cumplir estos requisitos ANTES de intentar ejecutar el proyecto.

### ✅ Lo que necesitas tener instalado

| Requisito | Versión Mínima | ¿Cómo verificar? | ¿Dónde descargarlo? |
|-----------|---------------|------------------|---------------------|
| **Windows** | 10 o superior | Ya lo tienes si usas Windows | - |
| **Python** | 3.10 o superior | Abre CMD y escribe: `python --version` | [python.org/downloads](https://www.python.org/downloads/) |
| **pip** | Cualquiera | Viene con Python automáticamente | Se instala con Python |
| **Git** | Cualquiera (opcional) | `git --version` | [git-scm.com](https://git-scm.com/download/win) |

### 🔍 ¿No tienes Python instalado?

1. Ve a [python.org/downloads](https://www.python.org/downloads/)
2. Descarga la versión más reciente (botón amarillo grande)
3. **MUY IMPORTANTE:** Al instalar, marca la casilla ✅ **"Add Python to PATH"**
4. Reinicia tu computadora después de instalar

### 💻 Requisitos de Hardware

- **RAM:** Mínimo 4 GB (recomendado 8 GB)
- **Espacio en disco:** 1 GB libre para el proyecto y navegador
- **Internet:** Conexión estable para descargar imágenes y datos

### 🌐 Requisitos de Red

- El sitio web **n1g.cl debe estar accesible** desde tu conexión
- Si usas VPN o proxy, el sitio podría bloquearte
- Algunas redes corporativas bloquean el scraping

---

## ✨ Características

| Feature | Descripción |
|---------|-------------|
| 🔄 **Multi-Categoría** | Scrapea todas las categorías automáticamente |
| 🎭 **JavaScript Rendering** | Usa Playwright para contenido dinámico |
| 💾 **Múltiples Salidas** | JSON, CSV y Base de Datos |
| 📁 **JSON por Categoría** | Archivos separados para cada categoría |
| 🛡️ **Anti-Bloqueo** | Headers realistas y delays configurables |
| 🐳 **Docker Ready** | Despliegue con un comando |
| 🧪 **Tests Incluidos** | Suite de pruebas con pytest |
| 🖥️ **Panel Visual** | Interfaz gráfica para ver los productos |

---

## 🚀 Inicio Rápido

### 📝 Instrucciones paso a paso (para principiantes)

#### Paso 1: Abre PowerShell
1. Presiona la tecla **Windows** en tu teclado
2. Escribe **"PowerShell"**
3. Haz clic en **"Windows PowerShell"** (el azul)

#### Paso 2: Navega a la carpeta del proyecto
```powershell
# Copia y pega este comando (cambia la ruta si es necesario):
cd "C:\Users\TU_USUARIO\Desktop\proyectZERO\projectzero2"
```
> 💡 **Tip:** Reemplaza `TU_USUARIO` por tu nombre de usuario de Windows

#### Paso 3: Configura el entorno (solo la primera vez)
```powershell
.\start.ps1 -Setup
```
> ⏱️ Esto toma 2-5 minutos. Descarga las dependencias y el navegador.

#### Paso 4: Ejecuta el scraping
```powershell
# Para hacer un scraping completo:
.\start.ps1

# O para una prueba rápida (más rápido):
.\start.ps1 -Quick
```

#### Paso 5: Ve los resultados en el panel visual
```powershell
.\panel.ps1
```
> 🖼️ Se abrirá una ventana con todos los productos organizados por categoría.

---

### 🐍 Opción alternativa: Usando Python directamente

Si prefieres usar Python en lugar de PowerShell:

```bash
# Paso 1: Configurar (solo una vez)
python run.py --setup

# Paso 2: Ejecutar scraping
python run.py

# Paso 3: Ver resultados
python frontend/app.py
```

### 🐳 Opción Docker (usuarios avanzados)

```bash
docker-compose up --build
```

---

## 🖥️ Panel de Visualización

El proyecto incluye un **panel de escritorio** moderno para visualizar los productos scrapeados.

### Características del Panel
- 🎨 Interfaz oscura moderna (CustomTkinter)
- 📂 Navegación por categorías en el menú lateral
- 🔍 Barra de búsqueda en tiempo real
- 🖼️ Imágenes de productos (requiere conexión a n1g.cl)
- 📊 Contador de productos y estadísticas
- 💎 Click en cualquier producto para ver detalles

### Cómo abrir el Panel

```powershell
.\panel.ps1
```

> ⚠️ **Nota:** Las imágenes solo cargan si el sitio n1g.cl está disponible.

---

## ❓ Solución de Problemas Comunes

### "No se reconoce el término 'python'"
**Causa:** Python no está instalado o no está en el PATH.
**Solución:** 
1. Reinstala Python desde [python.org](https://python.org)
2. **IMPORTANTE:** Marca "Add Python to PATH" durante la instalación
3. Reinicia PowerShell

### "No se puede cargar el archivo start.ps1"
**Causa:** PowerShell bloquea scripts por seguridad.
**Solución:** Ejecuta este comando primero:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### "Error 406" o "Timeout" al scrapear
**Causa:** El sitio n1g.cl está bloqueando tu conexión.
**Solución:** 
- Espera unos minutos e intenta de nuevo
- Verifica que puedas abrir n1g.cl en tu navegador
- Si usas VPN, desactívala

### "Las imágenes no cargan en el panel"
**Causa:** El sitio n1g.cl no está disponible.
**Solución:** Es normal, los datos del producto se muestran igual, solo sin imagen.

---

## 📖 Documentación

### Comandos Disponibles

| Comando | Descripción |
|---------|-------------|
| `.\start.ps1` | Scraping completo de todas las categorías |
| `.\start.ps1 -Setup` | Configurar entorno (deps, DB, Chromium) |
| `.\start.ps1 -Quick` | Modo rápido (2 páginas por categoría) |
| `.\start.ps1 -Category "gaming"` | Solo categorías específicas |
| `.\panel.ps1` | Abrir panel de visualización |
| `.\start.ps1 -Help` | Ver ayuda completa |

### Categorías Disponibles

```
computacion  │  componentes  │  perifericos  │  monitores
notebooks    │  almacenamiento  │  redes  │  gaming
impresoras   │  accesorios
```

### Ejemplos de Uso

```powershell
# Scrapear solo gaming y computación
.\start.ps1 -Category "gaming,computacion"

# Prueba rápida de una categoría
.\start.ps1 -Quick -Category "monitores"

# Ejecutar con Scrapy directamente
scrapy crawl categories -a max_pages=3 -a categories=gaming
```

---

## 🏗️ Arquitectura

```
projectzero2/
├── 📂 projectzero2/          # Código principal
│   ├── 📂 spiders/           # Spiders de Scrapy
│   │   ├── categories_spider.py   # 🌟 Spider maestro
│   │   ├── n1g_spider.py          # Spider de productos
│   │   └── n1g_product_spider.py  # Spider individual
│   ├── items.py              # Definición de items
│   ├── pipelines.py          # Procesamiento de datos
│   ├── models.py             # Modelos SQLAlchemy
│   └── settings.py           # Configuración
│
├── 📂 data/                  # Datos extraídos
│   └── 📂 categories/        # JSONs por categoría
│       ├── computacion.json
│       ├── gaming.json
│       └── _summary.json     # Resumen general
│
├── 📂 output/                # Salidas consolidadas
│   ├── output.json           # Todos los productos
│   └── output.csv            # Formato CSV
│
├── 📂 tests/                 # Tests automatizados
├── 📂 alembic/               # Migraciones de DB
├── 📂 scripts/               # Scripts auxiliares
├── 📂 docs/                  # Documentación extra
│
├── 🚀 start.ps1              # Script PowerShell
├── 🐍 run.py                 # Script Python
├── 🐳 docker-compose.yml     # Docker
├── 📋 requirements.txt       # Dependencias
└── 📖 README.md              # Este archivo
```

---

## 📊 Salidas

### 1. JSON por Categoría (`data/categories/`)

```json
{
  "category": "gaming",
  "total_products": 150,
  "scraped_at": "2026-02-02T12:00:00",
  "products": [
    {
      "titulo": "ASUS ROG Strix RTX 4090",
      "precio": "1899990",
      "stock": 5,
      "score": 85,
      "images": ["url1", "url2"],
      "description": "..."
    }
  ]
}
```

### 2. JSON Consolidado (`output/output.json`)

Todos los productos de todas las categorías en un solo archivo.

### 3. CSV (`output/output.csv`)

| id | url | titulo | precio | stock | score |
|----|-----|--------|--------|-------|-------|
| 1 | https://... | ASUS RTX 4090 | 1899990 | 5 | 85 |

### 4. Base de Datos SQLite/PostgreSQL

```sql
SELECT * FROM items WHERE stock > 0 ORDER BY score DESC;
```

---

## ⚙️ Configuración

### Variables de Entorno

```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost/n1g_db
JSON_OUTPUT_FILE=/data/output.json
CSV_OUTPUT_FILE=/data/output.csv
DISABLE_PLAYWRIGHT=0  # 1 para deshabilitar JS rendering
```

### Settings de Scrapy

```python
# projectzero2/settings.py
CONCURRENT_REQUESTS = 4          # Requests paralelos
DOWNLOAD_DELAY = 0.5             # Delay entre requests
RETRY_TIMES = 3                  # Reintentos
LOG_LEVEL = "INFO"               # Nivel de log
```

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=projectzero2

# Test específico
pytest tests/test_pipelines.py -v
```

---

## 🐳 Docker

### Desarrollo

```bash
docker-compose up
```

### Producción

```bash
docker-compose -f docker-compose.yml up -d
```

### Variables de Docker

```yaml
environment:
  - DATABASE_URL=postgresql://postgres:postgres@db:5432/scraper
  - LOG_LEVEL=INFO
```

---

## 📈 Métricas y Monitoreo

El spider genera estadísticas automáticamente:

```json
{
  "stats": {
    "categories_scraped": 10,
    "products_scraped": 1500,
    "start_time": "2026-02-02T10:00:00",
    "end_time": "2026-02-02T10:30:00"
  }
}
```

---

## 🤝 Contribuir

1. Fork el repositorio
2. Crea tu rama (`git checkout -b feature/nueva-feature`)
3. Commit tus cambios (`git commit -am 'Add nueva feature'`)
4. Push a la rama (`git push origin feature/nueva-feature`)
5. Abre un Pull Request

---

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles.

---

<div align="center">

**Hecho con ❤️ usando Scrapy + Playwright**

[⬆ Volver arriba](#-n1g-scraper)

</div>
