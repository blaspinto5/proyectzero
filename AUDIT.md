AUDIT — projectzero2

Resumen rápido
- Proyecto basado en Scrapy + scrapy-playwright para renderizado dinámico.
- Contenedor Docker + docker-compose con Postgres incluido.
- Pipelines implementadas: Normalize, Score, Postgres (upsert), CSV, JSON incremental.

Hallazgos
1) Código y estructura
- `projectzero2/` contiene la versión activa con spiders en `spiders/`.
- Existe una carpeta `legacy_myproject/` que contiene una copia de seguridad del proyecto antiguo.

2) Dependencias
- `requirements.txt` incluía paquetes no usados: `pydantic`, `tenacity`, `pandas`. Los removí.

3) Persistencia y orden
- Antes: JSON incremental no usaba `id` asignado por BD; ahora la pipeline de Postgres devuelve el `id` y lo adjunta al `item`.
- JSON ahora se escribe ordenado por `id` cuando está disponible.
- CSV ahora incluye `id` y `stock_image` y deduplica por `id`.

4) Robustez
- JSON se escribe de forma atómica mediante archivo temporal + `os.replace`.
- Postgres upsert usa `RETURNING id` para recuperar `id` del registro.

Recomendaciones
- Mantener `legacy_myproject/` fuera del repo o en un branch remoto si necesitas backup. Si ya no lo necesitas, puedes borrar la carpeta para limpiar.
- Añadir migraciones (Alembic) si el esquema de la tabla `items` va a evolucionar.
- Añadir tests unitarios para parsers y pipelines.
- Considerar guardado de fecha de scrape (`scraped_at`) en la BD para auditoría y re-scrapes.

Acciones aplicadas
- Implementado `id` persistente desde Postgres y pasado al `item`.
- JSON ordenado por `id`.
- CSV con `id` y `stock_image`.
- `requirements.txt` limpiado.

Próximos pasos sugeridos (si quieres que los haga ahora)
- Eliminar `legacy_myproject/` para limpieza.
- Añadir `scraped_at` automático en `PostgresPipeline`.
- Añadir Alembic y primer migración para tabla `items`.
- Crear endpoint FastAPI para consultar productos por `score`.

