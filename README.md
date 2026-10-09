# Financial News Sentiment Analysis

Distributed MQTT pipeline for financial news sentiment analysis. The producer reads from NewsAPI or mock data, the analyzer scores sentiment with VADER, MongoDB stores raw and enriched events, and Node-RED visualizes the stream.

## Components

- `producer-newsapi`: fetches live articles or generates mock ones.
- `analyzer-sentiment`: extracts tickers and computes sentiment.
- `consumer-db`: stores raw and analyzed documents in MongoDB.
- `dashboard-nodered`: visual dashboard for analyzed events and alerts.

## MQTT topics

- `news/articles/raw`
- `news/articles/analyzed`
- `news/alerts`
- `news/status/producer`

## Quick start

1. Copy `.env.example` to `.env` and set `NEWSAPI_KEY` if you want live data.
2. Run `docker compose up --build`.
3. Open Node-RED at `http://localhost:1880`.

## Development

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest
python -m ruff check .
```

## Notes

- `NEWSAPI_USE_MOCK=true` keeps the pipeline fully offline and reproducible.
- Live NewsAPI ingestion was validated in this workspace with the configured API key.