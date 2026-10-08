import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import UTC, datetime
from typing import TypedDict

import paho.mqtt.client as mqtt


TICKERS = [
    "NVDA",
    "AMD",
    "TSM",
    "AVGO",
    "INTC",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "AAPL",
    "PLTR",
    "SNOW",
    "ORCL",
]

PRODUCER_STATUS_TOPIC = "news/status/producer"
RAW_TOPIC = "news/articles/raw"

SOURCES = ["Reuters", "Bloomberg", "CNBC", "Financial Times", "The Wall Street Journal"]
KEYWORDS = ["stocks", "markets", "earnings", "inflation", "rates", "technology"]
POSITIVE_TEMPLATES = [
    "Positive market tone around {ticker} after strong earnings guidance",
    "{ticker} looks ready to break out on momentum",
    "Strong reaction for {ticker} as investors step in",
]
NEGATIVE_TEMPLATES = [
    "Bearish warning for {ticker} after weak demand",
    "{ticker} looks fragile with heavy selling pressure",
    "Muted outlook for {ticker} as sentiment turns cautious",
]
NEUTRAL_TEMPLATES = [
    "Market update mentioning {ticker} and broader positioning",
    "Watching {ticker} for the next session move",
    "{ticker} appears in a broader sector review",
]
DESCRIPTION_TEMPLATES = [
    "The article highlights corporate results, analyst commentary and near-term expectations.",
    "The story focuses on macro trends, investor positioning and market reaction.",
    "The report summarizes the latest developments affecting the stock and sector outlook.",
]


class NewsRawArticle(TypedDict):
    id: str
    source_name: str
    ticker_hint: str
    title: str
    description: str
    url: str
    timestamp: str


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def pick_item(options: list[str] | tuple[str, ...]) -> str:
    return options[0]


def pick_int(lower: int, upper: int) -> int:
    return lower if lower <= upper else upper


def get_ticker_list() -> list[str]:
    raw_value = os.getenv("NEWS_TICKERS", "")
    if not raw_value.strip():
        return TICKERS
    parsed = [item.strip().upper() for item in raw_value.split(",") if item.strip()]
    return parsed or TICKERS


def get_sources() -> list[str]:
    raw_value = os.getenv("NEWS_SOURCES", "")
    if not raw_value.strip():
        return SOURCES
    parsed = [item.strip() for item in raw_value.split(",") if item.strip()]
    return parsed or SOURCES


def get_keywords() -> list[str]:
    raw_value = os.getenv("NEWS_KEYWORDS", "")
    if not raw_value.strip():
        return KEYWORDS
    parsed = [item.strip() for item in raw_value.split(",") if item.strip()]
    return parsed or KEYWORDS


def build_mock_post() -> NewsRawArticle:
    article_id = str(uuid.uuid4())
    ticker = pick_item(get_ticker_list())
    sentiment_bucket = pick_item(("positive", "negative", "neutral"))
    if sentiment_bucket == "positive":
        title = pick_item(POSITIVE_TEMPLATES).format(ticker=ticker)
    elif sentiment_bucket == "negative":
        title = pick_item(NEGATIVE_TEMPLATES).format(ticker=ticker)
    else:
        title = pick_item(NEUTRAL_TEMPLATES).format(ticker=ticker)

    return {
        "id": article_id,
        "source_name": pick_item(get_sources()),
        "ticker_hint": ticker,
        "title": title,
        "description": pick_item(DESCRIPTION_TEMPLATES),
        "url": f"https://news.example.com/articles/{article_id}",
        "timestamp": utc_now(),
    }


def has_newsapi_credentials() -> bool:
    return bool(os.getenv("NEWSAPI_KEY"))


def build_search_query() -> str:
    configured_query = os.getenv("NEWSAPI_QUERY", "").strip()
    if configured_query:
        return configured_query

    return " OR ".join(get_keywords())


def fetch_news_article() -> NewsRawArticle | None:
    if not has_newsapi_credentials():
        return None

    try:
        query = urllib.parse.urlencode(
            {
                "q": build_search_query(),
                "language": os.getenv("NEWSAPI_LANGUAGE", "en"),
                "sortBy": os.getenv("NEWSAPI_SORT_BY", "publishedAt"),
                "pageSize": os.getenv("NEWSAPI_PAGE_SIZE", "1"),
            }
        )
        request = urllib.request.Request(
            f"https://newsapi.org/v2/everything?{query}",
            headers={
                "X-Api-Key": os.environ["NEWSAPI_KEY"],
                "User-Agent": os.getenv("NEWSAPI_USER_AGENT", "financial-sentiment-demo/1.0"),
            },
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError):
        return None

    articles = payload.get("articles") if isinstance(payload, dict) else None
    if not articles:
        return None

    article = articles[0]
    if not isinstance(article, dict):
        return None

    title = str(article.get("title", "")).strip()
    description = str(article.get("description", "")).strip()
    url = str(article.get("url", "")).strip()
    source = article.get("source", {})
    source_name = str(source.get("name", "NewsAPI")).strip() if isinstance(source, dict) else "NewsAPI"
    if not title:
        return None

    ticker = next(
        (candidate for candidate in get_ticker_list() if candidate in f"{title} {description}".upper()),
        pick_item(get_ticker_list()),
    )
    return {
        "id": url or str(article.get("publishedAt", utc_now())),
        "source_name": source_name or "NewsAPI",
        "ticker_hint": ticker,
        "title": title,
        "description": description or f"Latest coverage about {ticker}",
        "url": url or f"https://news.example.com/articles/{uuid.uuid4()}",
        "timestamp": str(article.get("publishedAt", utc_now())),
    }


def create_client() -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="producer-newsapi")
    status_topic = os.getenv("NEWS_STATUS_TOPIC", PRODUCER_STATUS_TOPIC)
    client.will_set(status_topic, json.dumps({"status": "OFFLINE"}), qos=1, retain=True)
    return client


def connect_mqtt(client: mqtt.Client) -> None:
    host = os.getenv("MQTT_HOST", "localhost")
    port = int(os.getenv("MQTT_PORT", "1883"))
    client.connect(host, port, keepalive=60)
    client.loop_start()
    status_topic = os.getenv("NEWS_STATUS_TOPIC", PRODUCER_STATUS_TOPIC)
    client.publish(status_topic, json.dumps({"status": "ONLINE"}), qos=1, retain=True)


def publish_post(client: mqtt.Client, topic: str, post: NewsRawArticle) -> None:
    client.publish(topic, json.dumps(post, ensure_ascii=True), qos=1)


def main() -> None:
    topic = os.getenv("NEWS_RAW_TOPIC", RAW_TOPIC)
    min_interval = max(1, int(os.getenv("NEWS_INTERVAL_MIN", "60")))
    max_interval = max(min_interval, int(os.getenv("NEWS_INTERVAL_MAX", str(min_interval))))
    use_mock = os.getenv("NEWSAPI_USE_MOCK", "true").lower() in {"1", "true", "yes", "on"}

    client = create_client()
    connect_mqtt(client)

    try:
        while True:
            payload = fetch_news_article() if not use_mock else None
            if payload is None:
                payload = build_mock_post()

            publish_post(client, topic, payload)
            time.sleep(pick_int(min_interval, max_interval))
    except KeyboardInterrupt:
        pass
    finally:
        status_topic = os.getenv("NEWS_STATUS_TOPIC", PRODUCER_STATUS_TOPIC)
        client.publish(status_topic, json.dumps({"status": "OFFLINE"}), qos=1, retain=True)
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
