import json
import os
import random
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

SOURCES = [
    "Reuters",
    "Bloomberg",
    "CNBC",
    "Financial Times",
    "The Wall Street Journal",
]

KEYWORDS = [
    "stocks",
    "markets",
    "earnings",
    "inflation",
    "rates",
    "technology",
]

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
    """Select a random item from a list or tuple."""
    if not options:
        raise ValueError("Cannot select an item from an empty collection")
    return random.choice(options)


def pick_int(lower: int, upper: int) -> int:
    """Select a random integer between lower and upper, inclusive."""
    return random.randint(lower, upper)


def get_ticker_list() -> list[str]:
    raw_value = os.getenv("NEWS_TICKERS", "")
    if not raw_value.strip():
        return TICKERS

    parsed = [
        item.strip().upper()
        for item in raw_value.split(",")
        if item.strip()
    ]
    return parsed or TICKERS


def get_sources() -> list[str]:
    raw_value = os.getenv("NEWS_SOURCES", "")
    if not raw_value.strip():
        return SOURCES

    parsed = [
        item.strip()
        for item in raw_value.split(",")
        if item.strip()
    ]
    return parsed or SOURCES


def get_keywords() -> list[str]:
    raw_value = os.getenv("NEWS_KEYWORDS", "")
    if not raw_value.strip():
        return KEYWORDS

    parsed = [
        item.strip()
        for item in raw_value.split(",")
        if item.strip()
    ]
    return parsed or KEYWORDS


def build_mock_post() -> NewsRawArticle:
    """Build a randomized mock financial news article."""
    article_id = str(uuid.uuid4())

    ticker = pick_item(get_ticker_list())
    sentiment_bucket = pick_item(
        ("positive", "negative", "neutral")
    )

    if sentiment_bucket == "positive":
        title = pick_item(POSITIVE_TEMPLATES).format(
            ticker=ticker
        )
    elif sentiment_bucket == "negative":
        title = pick_item(NEGATIVE_TEMPLATES).format(
            ticker=ticker
        )
    else:
        title = pick_item(NEUTRAL_TEMPLATES).format(
            ticker=ticker
        )

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

    # Search for configured financial news keywords.
    return " OR ".join(get_keywords())


def fetch_news_article() -> NewsRawArticle | None:
    """Fetch a randomly selected real article from NewsAPI."""
    if not has_newsapi_credentials():
        return None

    try:
        page_size = max(
            1,
            min(100, int(os.getenv("NEWSAPI_PAGE_SIZE", "10"))),
        )

        query = urllib.parse.urlencode(
            {
                "q": build_search_query(),
                "language": os.getenv("NEWSAPI_LANGUAGE", "en"),
                "sortBy": os.getenv(
                    "NEWSAPI_SORT_BY",
                    "publishedAt",
                ),
                "pageSize": str(page_size),
            }
        )

        request = urllib.request.Request(
            f"https://newsapi.org/v2/everything?{query}",
            headers={
                "X-Api-Key": os.environ["NEWSAPI_KEY"],
                "User-Agent": os.getenv(
                    "NEWSAPI_USER_AGENT",
                    "financial-sentiment-demo/1.0",
                ),
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=15,
        ) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )

    except (
        urllib.error.URLError,
        TimeoutError,
        KeyError,
        ValueError,
    ) as exc:
        print(f"NewsAPI request failed: {exc}")
        return None

    if not isinstance(payload, dict):
        return None

    if payload.get("status") != "ok":
        print(
            "NewsAPI returned an error: "
            f"{payload.get('message', 'Unknown error')}"
        )
        return None

    articles = payload.get("articles")

    if not isinstance(articles, list) or not articles:
        print("NewsAPI returned no articles.")
        return None

    valid_articles = [
        article
        for article in articles
        if isinstance(article, dict)
        and str(article.get("title", "")).strip()
        and str(article.get("url", "")).strip()
    ]

    if not valid_articles:
        return None

    article = random.choice(valid_articles)

    title = str(article.get("title", "")).strip()
    description = str(
        article.get("description") or ""
    ).strip()
    url = str(article.get("url", "")).strip()

    source = article.get("source", {})
    if isinstance(source, dict):
        source_name = str(
            source.get("name") or "NewsAPI"
        ).strip()
    else:
        source_name = "NewsAPI"

    # Detect a configured ticker mentioned in the headline
    # or description. Otherwise, select a random ticker hint.
    article_text = f"{title} {description}".upper()

    ticker = next(
        (
            candidate
            for candidate in get_ticker_list()
            if candidate.upper() in article_text
        ),
        pick_item(get_ticker_list()),
    )

    return {
        "id": url or str(uuid.uuid4()),
        "source_name": source_name or "NewsAPI",
        "ticker_hint": ticker,
        "title": title,
        "description": (
            description
            or f"Latest coverage potentially related to {ticker}."
        ),
        "url": url,
        "timestamp": str(
            article.get("publishedAt") or utc_now()
        ),
    }


def create_client() -> mqtt.Client:
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="producer-newsapi",
    )

    status_topic = os.getenv(
        "NEWS_STATUS_TOPIC",
        PRODUCER_STATUS_TOPIC,
    )

    client.will_set(
        status_topic,
        json.dumps({"status": "OFFLINE"}),
        qos=1,
        retain=True,
    )

    return client


def connect_mqtt(client: mqtt.Client) -> None:
    host = os.getenv("MQTT_HOST", "localhost")
    port = int(os.getenv("MQTT_PORT", "1883"))

    client.connect(host, port, keepalive=60)
    client.loop_start()

    status_topic = os.getenv(
        "NEWS_STATUS_TOPIC",
        PRODUCER_STATUS_TOPIC,
    )

    info = client.publish(
        status_topic,
        json.dumps({"status": "ONLINE"}),
        qos=1,
        retain=True,
    )
    info.wait_for_publish(timeout=5)

    print(f"Connected to MQTT broker at {host}:{port}")
    print(f"Producer status topic: {status_topic}")


def publish_post(
    client: mqtt.Client,
    topic: str,
    post: NewsRawArticle,
) -> None:
    info = client.publish(
        topic,
        json.dumps(post, ensure_ascii=True),
        qos=1,
    )

    info.wait_for_publish(timeout=5)

    print(
        f"Published | ticker={post['ticker_hint']} "
        f"| source={post['source_name']} "
        f"| title={post['title']}"
    )


def main() -> None:
    topic = os.getenv("NEWS_RAW_TOPIC", RAW_TOPIC)

    min_interval = max(
        1,
        int(os.getenv("NEWS_INTERVAL_MIN", "60")),
    )

    max_interval = max(
        min_interval,
        int(
            os.getenv(
                "NEWS_INTERVAL_MAX",
                str(min_interval),
            )
        ),
    )

    use_mock = (
        os.getenv("NEWSAPI_USE_MOCK", "true").lower()
        in {"1", "true", "yes", "on"}
    )

    client = create_client()

    try:
        connect_mqtt(client)

        print(f"Publishing articles to: {topic}")
        print(f"Mock mode: {use_mock}")
        print(
            f"Available tickers: {', '.join(get_ticker_list())}"
        )
        print(
            f"Publishing interval: {min_interval}-"
            f"{max_interval} seconds"
        )

        while True:
            payload = None

            if not use_mock:
                payload = fetch_news_article()

            # Fall back to mock data if NewsAPI is disabled,
            # unavailable, or returns no usable article.
            if payload is None:
                payload = build_mock_post()

            publish_post(client, topic, payload)

            time.sleep(
                pick_int(min_interval, max_interval)
            )

    except KeyboardInterrupt:
        print("\nProducer stopped by user.")

    except (
        OSError,
        ValueError,        
    ) as exc:
        print(f"Producer error: {exc}")

    finally:
        status_topic = os.getenv(
            "NEWS_STATUS_TOPIC",
            PRODUCER_STATUS_TOPIC,
        )

        if client.is_connected():
            info = client.publish(
                status_topic,
                json.dumps({"status": "OFFLINE"}),
                qos=1,
                retain=True,
            )
            info.wait_for_publish(timeout=5)

        client.loop_stop()
        client.disconnect()

        print("MQTT producer disconnected.")


if __name__ == "__main__":
    main()