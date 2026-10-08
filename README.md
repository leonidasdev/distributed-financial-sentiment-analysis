# Reddit Financial Sentiment Analysis

Distributed architecture built with Docker Compose + MQTT for synthetic or real Reddit ingestion, sentiment analysis with VADER, and persistence in MongoDB.

## What the system does

The main flow is:

1. `producer-reddit` generates or fetches Reddit posts and publishes JSON messages to MQTT.
2. `analyzer-sentiment` consumes the raw posts, detects the ticker, computes sentiment with VADER, and emits an enriched message.
3. `consumer-db` stores both the raw payload and the analyzed payload in MongoDB.
4. `dashboard-nodered` subscribes to the analyzed topics and exposes a visual dashboard.

The implementation prioritizes isolation: the runtime lives in Docker containers and local development uses a `.venv` environment.

## Services

- `broker-mqtt`: Mosquitto with MQTT on `1883` and websocket support on `9001`.
- `db-mongodb`: MongoDB for `reddit_analytics`.
- `producer-reddit`: publishes raw posts.
- `analyzer-sentiment`: sentiment classifier and ticker detector.
- `consumer-db`: persists raw and analyzed messages.
- `dashboard-nodered`: Node-RED base for the web dashboard.

## MQTT topics

This project uses a standard MQTT topic convention without double slashes:

- `reddit/posts/raw` for raw publications
- `reddit/posts/analyzed` for analyzer results
- `reddit/alerts` for extreme sentiment alerts
- `reddit/status/producer` for producer health with retained message

This topic structure improves interoperability, observability, and documentation clarity.

## Message schemas

Input (`reddit/posts/raw`):

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

Output (`reddit/posts/analyzed`):

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
    "label": "positive | neutral | negative"
  },
  "timestamp": "ISO-8601 UTC"
}
```

## Execution

1. Copy `.env.example` to `.env` if you want to configure real Reddit access or adjust parameters.
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

- `REDDIT_USE_MOCK=true` enables synthetic generation.
- If you define `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, and `REDDIT_USER_AGENT`, the producer can attempt to read from Reddit via `praw`.
- `MONGO_URI` points to `mongodb://db-mongodb:27017` inside Compose.

## Reddit free-tier note

The project is compatible with a Reddit free-tier or developer app workflow. A Reddit account is sufficient to create a script app under the Reddit developer settings, and the app credentials can be used without a paid plan for demo or academic usage. This is useful when you want to replace mock data with live Reddit posts while being within lightweight usage limits.

## Persistence

- `raw_posts`: original documents.
- `sentiment_analyzed`: enriched documents with `ticker` and `sentiment` analysis.

## Quality and current limitations

- The core logic has unit tests and was also validated with a real Docker startup.
- The Node-RED dashboard is exported in the repository as a reproducible JSON flow.
- MongoDB idempotency is handled with `replace_one` by `id`; for stronger production guarantees, a dedicated business key should be added.

The current tests cover the pure logic of the producer, analyzer, and MongoDB writer. End-to-end validation has also been confirmed with real Docker and MQTT traffic.

## Design notes

- The producer publishes an LWT on `reddit/status/producer` with `{"status": "OFFLINE"}` and marks `ONLINE` when it connects.
- The analyzer emits alerts when `|compound| > 0.6`.
- MongoDB creates indexes on `ticker`/`timestamp` for analyzed documents and `ticker_hint`/`timestamp` for raw documents.