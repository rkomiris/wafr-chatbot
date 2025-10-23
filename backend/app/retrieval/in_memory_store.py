from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import numpy as np


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    text: str
    score: float
    source: str | None = None
    pillar: str | None = None
    summary: str | None = None


class InMemoryVectorStore:
    """Simple cosine-similarity search over precomputed embeddings."""

    def __init__(self, chunks_file: Path) -> None:
        if not chunks_file.exists():
            raise FileNotFoundError(
                f"Processed chunks file not found at {chunks_file}. "
                "Run the ingestion pipeline to generate embeddings."
            )

        self._records: list[dict] = []
        embeddings: list[list[float]] = []

        with chunks_file.open(encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                payload = json.loads(line)
                embeddings.append(payload["embedding"])
                self._records.append(payload)

        if not self._records:
            raise ValueError("No chunks were loaded from the embeddings file.")

        matrix = np.asarray(embeddings, dtype=np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        self._embeddings = matrix / np.maximum(norms, 1e-12)

    def search(self, query_vector: Iterable[float], top_k: int = 4) -> List[RetrievedChunk]:
        query = np.asarray(list(query_vector), dtype=np.float32)
        if query.ndim != 1:
            raise ValueError("Query vector must be one-dimensional.")

        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            raise ValueError("Query vector norm is zero; cannot normalise.")
        query_unit = query / query_norm

        scores = np.dot(self._embeddings, query_unit)
        top_indices = np.argsort(scores)[::-1][:top_k]

        results: list[RetrievedChunk] = []
        for idx in top_indices:
            record = self._records[int(idx)]
            results.append(
                RetrievedChunk(
                    chunk_id=record["chunk_id"],
                    text=record["text"],
                    score=float(scores[idx]),
                    source=record.get("source"),
                    pillar=record.get("pillar"),
                    summary=record.get("summary"),
                )
            )
        return results
