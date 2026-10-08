# Reddit Financial Sentiment Analysis

Arquitectura distribuida en Docker Compose + MQTT para ingesta sintética o real de Reddit, análisis de sentimiento con VADER y persistencia en MongoDB.

## Qué hace el sistema

El flujo principal es este:

1. `producer-reddit` genera o extrae publicaciones de Reddit y publica mensajes JSON en MQTT.
2. `analyzer-sentiment` consume los posts brutos, detecta el ticker, calcula sentimiento con VADER y emite un mensaje enriquecido.
3. `consumer-db` persiste tanto el mensaje bruto como el analizado en MongoDB.
4. `dashboard-nodered` queda preparado para consumir los topics analizados y mostrar un dashboard.

La implementación prioriza aislamiento: el runtime vive en contenedores Docker y el desarrollo local se hace con `.venv`.

## Servicios

- `broker-mqtt`: Mosquitto con MQTT en `1883` y websockets en `9001`.
- `db-mongodb`: MongoDB para `reddit_analytics`.
- `producer-reddit`: publicador de posts crudos.
- `analyzer-sentiment`: clasificador de sentimiento y detector de tickers.
- `consumer-db`: persistencia de mensajes crudos y analizados.
- `dashboard-nodered`: base de Node-RED para construir la interfaz.

## Topics MQTT

Este proyecto usa una convención estándar de topics MQTT sin barras dobles:

- `reddit/posts/raw` para publicaciones crudas
- `reddit/posts/analyzed` para resultados del analizador
- `reddit/alerts` para alertas de sentimiento extremo
- `reddit/status/producer` para el estado del productor con retained message

La elección de esta jerarquía simplifica la interoperabilidad, la observabilidad y la documentación del sistema.

## Esquemas de mensaje

Entrada (`reddit/posts/raw`):

```json
{
	"id": "string",
	"subreddit": "string",
	"ticker_hint": "string",
	"title": "string",
	"author": "string",
	"timestamp": "ISO-8601 UTC"
}
```

Salida (`reddit/posts/analyzed`):

```json
{
	"id": "string",
	"subreddit": "string",
	"ticker": "string",
	"title": "string",
	"author": "string",
	"sentiment": {
		"compound": 0.0,
		"pos": 0.0,
		"neu": 0.0,
		"neg": 0.0,
		"label": "positivo | neutro | negativo"
	},
	"timestamp": "ISO-8601 UTC"
}
```

## Ejecución

1. Copia `.env.example` a `.env` si quieres configurar Reddit real o ajustar parámetros.
2. Ejecuta `docker compose up --build`.
3. Abre Node-RED en `http://localhost:1880`.

## Desarrollo local

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest
python -m ruff check .
```

El proyecto está pensado para ejecutarse en contenedores; las dependencias de runtime no deben instalarse globalmente en el sistema. Para trabajo local, crea un entorno virtual en `.venv` y usa ese aislamiento para pruebas y tooling.

Estado validado en este workspace: `.venv` creada, dependencias instaladas, `pytest` en verde y `ruff check .` en verde.

## Variables clave

- `REDDIT_USE_MOCK=true` activa la generación sintética.
- Si defines credenciales `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` y `REDDIT_USER_AGENT`, el productor intentará leer Reddit con `praw`.
- `MONGO_URI` apunta a `mongodb://db-mongodb:27017` dentro de Compose.

## Persistencia

- `raw_posts`: documentos originales.
- `sentiment_analyzed`: documentos enriquecidos con `ticker` y `sentiment`.

## Calidad y límites actuales

- La lógica crítica tiene tests unitarios y además se validó con arranque real de Docker.
- El dashboard de Node-RED queda exportado en el repositorio como JSON reproducible.
- La idempotencia en MongoDB está resuelta con `replace_one` por `id`; si se quiere robustez total, conviene definir una clave de negocio adicional.

Los tests actuales cubren la lógica pura de productor, analizador y writer de MongoDB. La validación end-to-end se ha comprobado con Docker y MQTT reales.

## Notas de diseño

- El productor publica un LWT en `reddit/status/producer` con `{"status": "OFFLINE"}` y marca `ONLINE` al conectarse.
- El analizador emite alertas cuando `|compound| > 0.6`.
- MongoDB crea índices sobre `ticker`/`timestamp` en analizados y `ticker_hint`/`timestamp` en crudos.