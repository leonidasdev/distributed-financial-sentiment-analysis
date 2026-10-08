# Financial News Sentiment Analysis

Distributed architecture built with Docker Compose + MQTT for synthetic or real NewsAPI ingestion, sentiment analysis with VADER, and persistence in MongoDB.

## What the system does

The main flow is:

1. `producer-newsapi` generates or fetches news articles from NewsAPI and publishes JSON messages to MQTT.
2. `analyzer-sentiment` consumes the raw posts, detects the ticker, computes sentiment with VADER, and emits an enriched message.
3. `consumer-db` stores both the raw payload and the analyzed payload in MongoDB.
4. `dashboard-nodered` subscribes to the analyzed topics and exposes a visual dashboard.

The implementation prioritizes isolation: the runtime lives in Docker containers and local development uses a `.venv` environment.

## Services

- `broker-mqtt`: Mosquitto with MQTT on `1883` and websocket support on `9001`.
- `db-mongodb`: MongoDB for `news_analytics`.
- `producer-newsapi`: publishes raw articles.
- `analyzer-sentiment`: sentiment classifier and ticker detector.
- `consumer-db`: persists raw and analyzed messages.
- `dashboard-nodered`: Node-RED base for the web dashboard.

## MQTT topics

This project uses a standard MQTT topic convention without double slashes:

- `news/articles/raw` for raw publications
- `news/articles/analyzed` for analyzer results
- `news/alerts` for extreme sentiment alerts
- `news/status/producer` for producer health with retained message

This topic structure improves interoperability, observability, and documentation clarity.

## Message schemas

Input (`news/articles/raw`):

```json
{
  "id": "string",
  "source_name": "string",
  "ticker_hint": "string",
  "title": "string",
  "description": "string",
  "url": "string",
  "timestamp": "ISO-8601 UTC"
}
```

Output (`news/articles/analyzed`):

```json
{
  "id": "string",
  "source_name": "string",
  "ticker": "string",
  "title": "string",
  "description": "string",
  "url": "string",
  "sentiment": {
    "compound": 0.0,
    "pos": 0.0,
    "neu": 0.0,
    "neg": 0.0,
    "label": "positive | neutral | negative"
  },
  "timestamp": "ISO-8601 UTC"
}
```

## Execution

1. Copy `.env.example` to `.env` if you want to configure a NewsAPI key or adjust parameters.
2. Run `docker compose up --build`.
3. Open Node-RED at `http://localhost:1880`.

## Local development

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest
python -m ruff check .
```

The project is designed to run in containers; runtime dependencies should not be installed globally. For local work, use a dedicated `.venv` environment for tests and tooling.

Validated in this workspace: `.venv` created, dependencies installed, `pytest` green, and `ruff check .` green.

## Key variables

- `NEWSAPI_USE_MOCK=true` enables synthetic generation.
- If you define `NEWSAPI_KEY`, the producer can query NewsAPI for live articles.
- `MONGO_URI` points to `mongodb://db-mongodb:27017` inside Compose.

## NewsAPI setup

The project supports live NewsAPI data when a valid API key is provided. The default query targets finance-related stories and you can narrow it with `NEWSAPI_QUERY`.

1. Create a NewsAPI account and copy the API key.
2. Paste the key into `.env`.
3. Set `NEWSAPI_USE_MOCK=false` to fetch live news.

The mock mode remains available for demos, tests, and offline development.

## Persistence

- `raw_posts`: original documents.
- `sentiment_analyzed`: enriched documents with `ticker` and `sentiment` analysis.

## Quality and current limitations

- The core logic has unit tests and was also validated with a real Docker startup.
- The Node-RED dashboard is exported in the repository as a reproducible JSON flow.
- MongoDB idempotency is handled with `replace_one` by `id`; for stronger production guarantees, a dedicated business key should be added.

The current tests cover the pure logic of the producer, analyzer, and MongoDB writer. End-to-end validation has also been confirmed with real Docker and MQTT traffic.

## Design notes

- The producer publishes an LWT on `news/status/producer` with `{"status": "OFFLINE"}` and marks `ONLINE` when it connects.
- The analyzer emits alerts when `|compound| > 0.6`.
- MongoDB creates indexes on `ticker`/`timestamp` for analyzed documents and `source_name`/`timestamp` for raw documents.