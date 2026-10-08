import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def load_module(module_name: str, relative_path: str) -> ModuleType:
    module_path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


producer = load_module("producer_module", "producer/producer.py")


def test_get_ticker_list_uses_default_when_env_is_empty(monkeypatch):
    monkeypatch.delenv("NEWS_TICKERS", raising=False)

    assert producer.get_ticker_list() == producer.TICKERS


def test_build_mock_post_uses_configured_ticker_and_source(monkeypatch):
    monkeypatch.setattr(producer, "pick_item", lambda seq: seq[0])
    monkeypatch.setattr(producer.uuid, "uuid4", lambda: "11111111-2222-3333-4444-555555555555")
    monkeypatch.setenv("NEWS_TICKERS", "NVDA,AMD")
    monkeypatch.setenv("NEWS_SOURCES", "Reuters,Bloomberg")

    post = producer.build_mock_post()

    assert post["id"] == "11111111-2222-3333-4444-555555555555"
    assert post["source_name"] == "Reuters"
    assert post["ticker_hint"] == "NVDA"
    assert post["description"]
    assert post["url"] == "https://news.example.com/articles/11111111-2222-3333-4444-555555555555"
    assert "timestamp" in post