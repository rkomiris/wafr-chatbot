from collections import deque
from typing import Iterator

import pytest

from app.ingest import index_chunks


class DummyModel:
    def __init__(self) -> None:
        self.calls = []

    def encode(self, sentences, convert_to_numpy=False):
        self.calls.append(list(sentences))
        return [[float(len(text))] for text in sentences]


def test_add_embeddings_batches(monkeypatch: pytest.MonkeyPatch) -> None:
    model = DummyModel()
    monkeypatch.setattr(index_chunks, "get_embedding_model", lambda name: model)

    records = [{"text": "hello"}, {"text": "world"}]
    enriched = list(index_chunks.add_embeddings(records, model_name="dummy"))

    assert enriched[0]["embedding"] == [5.0]
    assert enriched[1]["embedding"] == [5.0]
    assert model.calls == [["hello", "world"]]
