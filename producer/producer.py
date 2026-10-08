import json
import os
import time
import uuid
from datetime import UTC, datetime
from typing import TypedDict

import paho.mqtt.client as mqtt

try:
    import praw
except Exception:  # pragma: no cover - optional dependency for mock-only deployments
    praw = None


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

PRODUCER_STATUS_TOPIC = "reddit/status/producer"
RAW_TOPIC = "reddit/posts/raw"

SUBREDDITS = ["wallstreetbets", "stocks", "investing", "options"]
POSITIVE_TEMPLATES = [
    "Bullish setup on {ticker} after strong guidance",
    "{ticker} looks ready to break out on momentum",
    "Great earnings reaction for {ticker}, buyers stepping in",
]
NEGATIVE_TEMPLATES = [
    "Bearish warning for {ticker} after weak demand",
    "{ticker} looks fragile with heavy selling pressure",
    "Terrible outlook for {ticker}, sentiment is sour",
]
NEUTRAL_TEMPLATES = [
    "Discussion thread about {ticker} and market positioning",
    "Watching {ticker} for the next session move",
    "{ticker} mentioned in a broader sector review",
]


class RedditRawPost(TypedDict):
    id: str
    subreddit: str
    ticker_hint: str
    title: str
    author: str
    timestamp: str


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def pick_item(options: list[str] | tuple[str, ...]) -> str:
    return options[0]


def pick_int(lower: int, upper: int) -> int:
    return lower if lower <= upper else upper


def get_ticker_list() -> list[str]:
    raw_value = os.getenv("REDDIT_TICKERS", "")
    if not raw_value.strip():
        return TICKERS
    parsed = [item.strip().upper() for item in raw_value.split(",") if item.strip()]
    return parsed or TICKERS


def get_subreddits() -> list[str]:
    raw_value = os.getenv("REDDIT_SUBREDDITS", "")
    if not raw_value.strip():
        return SUBREDDITS
    parsed = [item.strip() for item in raw_value.split(",") if item.strip()]
    return parsed or SUBREDDITS


def build_mock_post() -> RedditRawPost:
    ticker = pick_item(get_ticker_list())
    sentiment_bucket = pick_item(("positive", "negative", "neutral"))
    if sentiment_bucket == "positive":
        title = pick_item(POSITIVE_TEMPLATES).format(ticker=ticker)
    elif sentiment_bucket == "negative":
        title = pick_item(NEGATIVE_TEMPLATES).format(ticker=ticker)
    else:
        title = pick_item(NEUTRAL_TEMPLATES).format(ticker=ticker)

    return {
        "id": str(uuid.uuid4()),
        "subreddit": pick_item(get_subreddits()),
        "ticker_hint": ticker,
        "title": title,
        "author": f"user_{pick_int(1000, 9999)}",
        "timestamp": utc_now(),
    }


def has_reddit_credentials() -> bool:
    required = [
        os.getenv("REDDIT_CLIENT_ID"),
        os.getenv("REDDIT_CLIENT_SECRET"),
        os.getenv("REDDIT_USER_AGENT"),
    ]
    return all(required)


def reddit_client():
    if praw is None or not has_reddit_credentials():
        return None

    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ["REDDIT_USER_AGENT"],
        username=os.getenv("REDDIT_USERNAME") or None,
        password=os.getenv("REDDIT_PASSWORD") or None,
    )


def fetch_reddit_post(reddit_api) -> RedditRawPost | None:
    try:
        subreddit_name = pick_item(get_subreddits())
        submission = next(reddit_api.subreddit(subreddit_name).hot(limit=1), None)
        if submission is None:
            return None

        title = submission.title.strip() or f"Post from {subreddit_name}"
        ticker = next((ticker for ticker in get_ticker_list() if ticker in title.upper()), pick_item(get_ticker_list()))
        return {
            "id": submission.id,
            "subreddit": subreddit_name,
            "ticker_hint": ticker,
            "title": title,
            "author": str(submission.author) if submission.author else "unknown",
            "timestamp": utc_now(),
        }
    except Exception:
        return None


def create_client() -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="producer-reddit")
    status_topic = os.getenv("REDDIT_STATUS_TOPIC", PRODUCER_STATUS_TOPIC)
    client.will_set(status_topic, json.dumps({"status": "OFFLINE"}), qos=1, retain=True)
    return client


def connect_mqtt(client: mqtt.Client) -> None:
    host = os.getenv("MQTT_HOST", "localhost")
    port = int(os.getenv("MQTT_PORT", "1883"))
    client.connect(host, port, keepalive=60)
    client.loop_start()
    status_topic = os.getenv("REDDIT_STATUS_TOPIC", PRODUCER_STATUS_TOPIC)
    client.publish(status_topic, json.dumps({"status": "ONLINE"}), qos=1, retain=True)


def publish_post(client: mqtt.Client, topic: str, post: RedditRawPost) -> None:
    client.publish(topic, json.dumps(post, ensure_ascii=True), qos=1)


def main() -> None:
    topic = os.getenv("REDDIT_RAW_TOPIC", RAW_TOPIC)
    min_interval = max(1, int(os.getenv("REDDIT_INTERVAL_MIN", "1")))
    max_interval = max(min_interval, int(os.getenv("REDDIT_INTERVAL_MAX", str(min_interval))))
    use_mock = os.getenv("REDDIT_USE_MOCK", "true").lower() in {"1", "true", "yes", "on"}

    client = create_client()
    connect_mqtt(client)
    reddit_api = None if use_mock else reddit_client()

    try:
        while True:
            payload = fetch_reddit_post(reddit_api) if reddit_api is not None else None
            if payload is None:
                payload = build_mock_post()

            publish_post(client, topic, payload)
            time.sleep(pick_int(min_interval, max_interval))
    except KeyboardInterrupt:
        pass
    finally:
        status_topic = os.getenv("REDDIT_STATUS_TOPIC", PRODUCER_STATUS_TOPIC)
        client.publish(status_topic, json.dumps({"status": "OFFLINE"}), qos=1, retain=True)
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()