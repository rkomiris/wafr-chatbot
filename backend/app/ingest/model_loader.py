from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from typing import Protocol

from sentence_transformers import SentenceTransformer


class EmbeddingModel(Protocol):
    def encode(self, sentences: list[str], convert_to_numpy: bool = False) -> list[list[float]]:
        ...


class DummyEmbeddingModel:
    """Fallback model useful for offline testing."""

    def encode(self, sentences: list[str], convert_to_numpy: bool = False):
        vectors = []
        for sentence in sentences:
            digest = sha256(sentence.encode("utf-8")).digest()
            floats = [int.from_bytes(digest[i : i + 8], "big", signed=False) / 10**18 for i in range(0, 32, 8)]
            vectors.append(floats)
        if convert_to_numpy:
            return vectors  # compatible with caller expecting `.tolist()` handling
        return vectors


@lru_cache
def get_embedding_model(name: str = "sentence-transformers/all-MiniLM-L6-v2") -> EmbeddingModel:
    if name == "dummy":
        return DummyEmbeddingModel()
    return SentenceTransformer(name)
