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


analyzer = load_module("analyzer_module", "analyzer/analyzer.py")


class FakeSIA:
    def __init__(self, score):
        self.score = score

    def polarity_scores(self, _text):
        return self.score


def test_sentiment_label_thresholds():
    assert analyzer.sentiment_label(0.10) == "positivo"
    assert analyzer.sentiment_label(-0.10) == "negativo"
    assert analyzer.sentiment_label(0.00) == "neutro"


def test_build_analyzed_payload_extracts_ticker_from_title():
    payload = {
        "id": "abc",
        "subreddit": "stocks",
        "ticker_hint": "AMD",
        "title": "NVDA beats expectations and rallies",
        "author": "alice",
        "timestamp": "2026-09-30T12:00:00Z",
    }

    result = analyzer.build_analyzed_payload(payload, FakeSIA({"compound": 0.7, "pos": 0.8, "neu": 0.1, "neg": 0.1}))

    assert result["ticker"] == "NVDA"
    assert result["sentiment"]["label"] == "positivo"
    assert result["sentiment"]["compound"] == 0.7