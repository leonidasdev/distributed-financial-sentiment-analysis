import json
import os
import re
from datetime import UTC, datetime
from typing import TypedDict

import nltk
import paho.mqtt.client as mqtt
from nltk.sentiment import SentimentIntensityAnalyzer

TICKER_PATTERN = re.compile(r"\b(NVDA|AMD|TSM|AVGO|INTC|MSFT|GOOGL|AMZN|META|AAPL|PLTR|SNOW|ORCL)\b", re.IGNORECASE)


class SentimentScores(TypedDict):
    compound: float
    pos: float
    neu: float
    neg: float


class SentimentDetails(SentimentScores):
    label: str


class AnalyzedPost(TypedDict):
    id: str
    subreddit: str
    ticker: str
    title: str
    author: str
    sentiment: SentimentDetails
    timestamp: str


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def sentiment_label(compound: float) -> str:
    if compound >= 0.05:
        return "positivo"
    if compound <= -0.05:
        return "negativo"
    return "neutro"


def ensure_vader() -> SentimentIntensityAnalyzer:
    nltk.download("vader_lexicon", quiet=True)
    return SentimentIntensityAnalyzer()


def create_client() -> mqtt.Client:
    return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="analyzer-sentiment")


RAW_TOPIC = "reddit/posts/raw"
ANALYZED_TOPIC = "reddit/posts/analyzed"
ALERT_TOPIC = "reddit/alerts"


def subscribe_topics(client: mqtt.Client) -> None:
    client.subscribe(os.getenv("REDDIT_RAW_TOPIC", RAW_TOPIC), qos=1)


def publish_analyzed(client: mqtt.Client, payload: AnalyzedPost) -> None:
    topic = os.getenv("REDDIT_ANALYZED_TOPIC", ANALYZED_TOPIC)
    client.publish(topic, json.dumps(payload, ensure_ascii=True), qos=1)


def publish_alert(client: mqtt.Client, payload: dict[str, object]) -> None:
    topic = os.getenv("REDDIT_ALERT_TOPIC", ALERT_TOPIC)
    client.publish(topic, json.dumps(payload, ensure_ascii=True), qos=0)


def build_analyzed_payload(post: dict[str, object], sia: SentimentIntensityAnalyzer) -> AnalyzedPost:
    title = str(post.get("title", ""))
    ticker_hint = str(post.get("ticker_hint", "")).upper()
    match = TICKER_PATTERN.search(title)
    ticker = match.group(1).upper() if match else (ticker_hint or "UNKNOWN")
    scores = sia.polarity_scores(title)
    compound = float(scores["compound"])

    return {
        "id": str(post.get("id", "")),
        "subreddit": str(post.get("subreddit", "")),
        "ticker": ticker,
        "title": title,
        "author": str(post.get("author", "")),
        "sentiment": {
            "compound": compound,
            "pos": float(scores["pos"]),
            "neu": float(scores["neu"]),
            "neg": float(scores["neg"]),
            "label": sentiment_label(compound),
        },
        "timestamp": str(post.get("timestamp", utc_now())),
    }


def on_message_factory(client: mqtt.Client, sia: SentimentIntensityAnalyzer):
    def on_message(_client: mqtt.Client, _userdata, message: mqtt.MQTTMessage) -> None:
        try:
            post = json.loads(message.payload.decode("utf-8"))
        except json.JSONDecodeError:
            return

        analyzed = build_analyzed_payload(post, sia)
        publish_analyzed(client, analyzed)

        compound = float(analyzed["sentiment"]["compound"])
        if abs(compound) > 0.6:
            publish_alert(
                client,
                {
                    "id": analyzed["id"],
                    "ticker": analyzed["ticker"],
                    "subreddit": analyzed["subreddit"],
                    "title": analyzed["title"],
                    "compound": compound,
                    "label": analyzed["sentiment"]["label"],
                    "timestamp": analyzed["timestamp"],
                    "source_topic": message.topic,
                },
            )

    return on_message


def main() -> None:
    sia = ensure_vader()
    client = create_client()

    def on_connect(mqtt_client: mqtt.Client, _userdata, _flags, reason_code, _properties=None) -> None:
        if reason_code == mqtt.MQTT_ERR_SUCCESS:
            subscribe_topics(mqtt_client)

    client.on_connect = on_connect
    client.on_message = on_message_factory(client, sia)

    host = os.getenv("MQTT_HOST", "localhost")
    port = int(os.getenv("MQTT_PORT", "1883"))
    client.connect(host, port, keepalive=60)
    client.loop_forever()


if __name__ == "__main__":
    main()