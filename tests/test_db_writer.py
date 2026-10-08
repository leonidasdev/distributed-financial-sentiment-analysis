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


db_writer = load_module("db_writer_module", "db_writer/db_writer.py")


class FakeCollection:
    def __init__(self):
        self.calls = []

    def replace_one(self, filter_doc, document, upsert=False):
        self.calls.append(("replace_one", filter_doc, document, upsert))

    def insert_one(self, document):
        self.calls.append(("insert_one", document))


def test_persist_document_uses_idempotent_upsert_when_id_exists(monkeypatch):
    monkeypatch.setattr(db_writer, "utc_now", lambda: "2026-09-30T12:00:00Z")
    collection = FakeCollection()

    db_writer.persist_document(collection, {"id": "abc", "ticker": "NVDA"})

    assert collection.calls[0][0] == "replace_one"
    assert collection.calls[0][1] == {"id": "abc"}
    assert collection.calls[0][3] is True


def test_persist_document_inserts_when_id_is_missing(monkeypatch):
    monkeypatch.setattr(db_writer, "utc_now", lambda: "2026-09-30T12:00:00Z")
    collection = FakeCollection()

    db_writer.persist_document(collection, {"ticker": "NVDA"})

    assert collection.calls[0][0] == "insert_one"
    assert collection.calls[0][1]["ingested_at"] == "2026-09-30T12:00:00Z"