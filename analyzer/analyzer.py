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
    source_name: str
    ticker: str
    title: str
    description: str
    url: str
    sentiment: SentimentDetails
    timestamp: str


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def sentiment_label(compound: float) -> str:
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"


def ensure_vader() -> SentimentIntensityAnalyzer:
    nltk.download("vader_lexicon", quiet=True)
    return SentimentIntensityAnalyzer()


def create_client() -> mqtt.Client:
    return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="analyzer-sentiment")


RAW_TOPIC = "news/articles/raw"
ANALYZED_TOPIC = "news/articles/analyzed"
ALERT_TOPIC = "news/alerts"


def subscribe_topics(client: mqtt.Client) -> None:
    client.subscribe(os.getenv("NEWS_RAW_TOPIC", RAW_TOPIC), qos=1)


def publish_analyzed(client: mqtt.Client, payload: AnalyzedPost) -> None:
    topic = os.getenv("NEWS_ANALYZED_TOPIC", ANALYZED_TOPIC)
    client.publish(topic, json.dumps(payload, ensure_ascii=True), qos=1)


def publish_alert(client: mqtt.Client, payload: dict[str, object]) -> None:
    topic = os.getenv("NEWS_ALERT_TOPIC", ALERT_TOPIC)
    client.publish(topic, json.dumps(payload, ensure_ascii=True), qos=0)


def build_analyzed_payload(post: dict[str, object], sia: SentimentIntensityAnalyzer) -> AnalyzedPost:
    title = str(post.get("title", ""))
    description = str(post.get("description", ""))
    combined_text = f"{title} {description}".strip()
    ticker_hint = str(post.get("ticker_hint", "")).upper()
    match = TICKER_PATTERN.search(combined_text)
    ticker = match.group(1).upper() if match else (ticker_hint or "UNKNOWN")
    scores = sia.polarity_scores(combined_text)
    compound = float(scores["compound"])

    return {
        "id": str(post.get("id", "")),
        "source_name": str(post.get("source_name", "")),
        "ticker": ticker,
        "title": title,
        "description": description,
        "url": str(post.get("url", "")),
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
                    "source_name": analyzed["source_name"],
                    "title": analyzed["title"],
                    "url": analyzed["url"],
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