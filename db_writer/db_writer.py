import json
import os
from datetime import UTC, datetime
from typing import Protocol

import paho.mqtt.client as mqtt
from pymongo import MongoClient


class WritableCollection(Protocol):
    def create_index(self, keys): ...

    def replace_one(self, filter_doc, document, upsert=False): ...

    def insert_one(self, document): ...


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def create_mongo_client() -> tuple[MongoClient, WritableCollection, WritableCollection]:
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB", "news_analytics")
    client: MongoClient = MongoClient(mongo_uri)
    database = client[db_name]
    raw_collection = database[os.getenv("RAW_COLLECTION", "raw_articles")]
    analyzed_collection = database[os.getenv("ANALYZED_COLLECTION", "sentiment_analyzed")]

    raw_collection.create_index([("source_name", 1), ("timestamp", 1)])
    analyzed_collection.create_index([("ticker", 1), ("timestamp", 1)])
    return client, raw_collection, analyzed_collection


def create_client() -> mqtt.Client:
    return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="consumer-db")


def subscribe_topics(client: mqtt.Client) -> None:
    client.subscribe(os.getenv("NEWS_RAW_TOPIC", "news/articles/raw"), qos=1)
    client.subscribe(os.getenv("NEWS_ANALYZED_TOPIC", "news/articles/analyzed"), qos=1)


def persist_document(collection: WritableCollection, document: dict[str, object]) -> None:
    document = dict(document)
    document.setdefault("ingested_at", utc_now())
    identifier = document.get("id")
    if identifier:
        collection.replace_one({"id": identifier}, document, upsert=True)
    else:
        collection.insert_one(document)


def main() -> None:
    mongo_client, raw_collection, analyzed_collection = create_mongo_client()
    mqtt_client = create_client()

    def on_connect(client: mqtt.Client, _userdata, _flags, reason_code, _properties=None) -> None:
        if reason_code == mqtt.MQTT_ERR_SUCCESS:
            subscribe_topics(client)

    def on_message(_client: mqtt.Client, _userdata, message: mqtt.MQTTMessage) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except json.JSONDecodeError:
            return

        if message.topic.endswith("articles/raw"):
            persist_document(raw_collection, {**payload, "source_topic": message.topic})
        elif message.topic.endswith("articles/analyzed"):
            persist_document(analyzed_collection, {**payload, "source_topic": message.topic})

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    host = os.getenv("MQTT_HOST", "localhost")
    port = int(os.getenv("MQTT_PORT", "1883"))
    mqtt_client.connect(host, port, keepalive=60)
    try:
        mqtt_client.loop_forever()
    finally:
        mongo_client.close()


if __name__ == "__main__":
    main()