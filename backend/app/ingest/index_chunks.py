from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from elasticsearch import Elasticsearch

from ..config import get_settings
from .generate_chunks import parse_args as parse_chunk_args, run as generate_chunks
from .model_loader import get_embedding_model
from .writers import (
    ChunkWriter,
    ElasticsearchChunkWriter,
    FileChunkWriter,
    StdoutChunkWriter,
)


def load_chunk_records(path: Path) -> Iterator[dict]:
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            yield json.loads(line)


def add_embeddings(records: Iterable[dict], model_name: str) -> Iterator[dict]:
    model = get_embedding_model(model_name)
    texts: list[str] = []
    buffered: list[dict] = []

    for record in records:
        texts.append(record["text"])
        buffered.append(record)

        if len(texts) >= 32:
            vectors = model.encode(texts, convert_to_numpy=True)
            for payload, vector in zip(buffered, vectors, strict=False):
                payload["embedding"] = vector.tolist() if hasattr(vector, "tolist") else list(vector)
                yield payload
            texts.clear()
            buffered.clear()

    if texts:
        vectors = model.encode(texts, convert_to_numpy=True)
        for payload, vector in zip(buffered, vectors, strict=False):
            payload["embedding"] = vector.tolist() if hasattr(vector, "tolist") else list(vector)
            yield payload


def create_writer(
    mode: str,
    *,
    output_path: Path,
    index_name: str,
    es_host: str | None,
) -> ChunkWriter:
    if mode == "stdout":
        return StdoutChunkWriter()
    if mode == "file":
        return FileChunkWriter(output_path)
    if mode == "elasticsearch":
        if not es_host:
            raise ValueError("Elasticsearch host must be provided when using elasticsearch mode.")
        client = Elasticsearch(es_host)
        return ElasticsearchChunkWriter(client, index_name=index_name)
    raise ValueError(f"Unsupported writer mode: {mode}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    settings = get_settings()

    parser = argparse.ArgumentParser(
        description="Generate embeddings for processed chunks and route them to the desired sink."
    )
    parser.add_argument(
        "--chunks-path",
        type=Path,
        default=settings.scraper_output_dir.parent / "processed" / "wafr_chunks.jsonl",
        help="Location of processed chunk file.",
    )
    parser.add_argument(
        "--writer",
        choices=["stdout", "file", "elasticsearch"],
        default="stdout",
        help="Where to send the enriched records.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=settings.scraper_output_dir.parent / "processed" / "wafr_chunks_with_embeddings.jsonl",
        help="Output path when using the 'file' writer.",
    )
    parser.add_argument(
        "--embedding-model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="SentenceTransformer model identifier.",
    )
    parser.add_argument(
        "--es-host",
        default=None,
        help="Elasticsearch host URL (required for elasticsearch writer).",
    )
    parser.add_argument(
        "--es-index",
        default="wafr-chunks",
        help="Target Elasticsearch index name.",
    )
    parser.add_argument(
        "--refresh-chunks",
        action="store_true",
        help="Regenerate chunks from raw documents before embedding.",
    )
    return parser.parse_args(argv)


def run(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)

    chunks_path = args.chunks_path
    if args.refresh_chunks or not chunks_path.exists():
        generate_chunks(
            [
                "--output",
                str(chunks_path.parent),
                "--input",
                str(get_settings().scraper_output_dir),
            ]
        )

    records = load_chunk_records(chunks_path)
    enriched_records = add_embeddings(records, args.embedding_model)

    writer = create_writer(
        args.writer,
        output_path=args.output,
        index_name=args.es_index,
        es_host=args.es_host,
    )
    writer.write(enriched_records)


def main() -> None:
    run()


if __name__ == "__main__":
    main()
