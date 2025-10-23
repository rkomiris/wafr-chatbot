from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, Mapping

from elasticsearch import Elasticsearch


ChunkPayload = Mapping[str, object]


class ChunkWriter(ABC):
    @abstractmethod
    def write(self, payloads: Iterable[ChunkPayload]) -> None:
        ...


class StdoutChunkWriter(ChunkWriter):
    """Debug writer that prints payloads as JSON lines."""

    def write(self, payloads: Iterable[ChunkPayload]) -> None:
        for payload in payloads:
            print(json.dumps(payload, ensure_ascii=False))  # noqa: T201


class FileChunkWriter(ChunkWriter):
    """Persist payloads locally (e.g., to inspect embeddings before indexing)."""

    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, payloads: Iterable[ChunkPayload]) -> None:
        with self.output_path.open("w", encoding="utf-8") as stream:
            for payload in payloads:
                stream.write(json.dumps(payload, ensure_ascii=False) + "\n")


class ElasticsearchChunkWriter(ChunkWriter):
    """Send payloads to an Elasticsearch ingest endpoint."""

    def __init__(
        self,
        client: Elasticsearch,
        index_name: str,
    ) -> None:
        self.client = client
        self.index_name = index_name

    def write(self, payloads: Iterable[ChunkPayload]) -> None:
        actions = []
        for payload in payloads:
            actions.append({"index": {"_index": self.index_name, "_id": payload["chunk_id"]}})
            actions.append(payload)

        if not actions:
            return

        body_lines = "\n".join(json.dumps(action, ensure_ascii=False) for action in actions) + "\n"
        self.client.bulk(body=body_lines)
