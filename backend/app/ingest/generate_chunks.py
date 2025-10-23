from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from ..config import get_settings
from .chunker import TextChunk, chunk_text


@dataclass
class RawDocument:
    identifier: str
    source: str
    content: str
    doc_type: str


PILLAR_KEYWORDS = {
    "operational": "Operational Excellence",
    "security": "Security",
    "reliability": "Reliability",
    "performance": "Performance Efficiency",
    "cost": "Cost Optimization",
    "sustainability": "Sustainability",
}


def discover_documents(input_dir: Path) -> Iterator[RawDocument]:
    for path in sorted(input_dir.glob("*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                identifier = payload.get("id") or path.stem
                yield RawDocument(
                    identifier=identifier,
                    source=payload.get("source", ""),
                    content=payload.get("content", ""),
                    doc_type="html",
                )
    for path in sorted(input_dir.glob("*.pdf")):
        yield RawDocument(
            identifier=path.stem,
            source="",
            content="",
            doc_type="pdf",
        )


def infer_pillar(identifier: str) -> str | None:
    slug = identifier.lower()
    for keyword, pillar in PILLAR_KEYWORDS.items():
        if keyword in slug:
            return pillar
    return None


def build_chunk_payloads(
    document: RawDocument,
    *,
    chunk_size: int,
    overlap: int,
) -> Iterable[dict]:
    chunks = chunk_text(
        document.content,
        max_words=chunk_size,
        overlap_words=overlap,
    )
    for index, chunk in enumerate(chunks, start=1):
        summary = " ".join(chunk.content.split()[:18])
        yield {
            "chunk_id": f"{document.identifier}::chunk-{index}",
            "document_id": document.identifier,
            "source": document.source,
            "pillar": infer_pillar(document.identifier),
            "chunk_index": index,
            "text": chunk.content,
            "word_count": chunk.word_count,
            "summary": summary,
            "doc_type": document.doc_type,
        }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        description="Generate structured chunks from raw WAFR documents."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=settings.scraper_output_dir,
        help="Directory containing raw scraper output (default: data/raw).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=settings.scraper_output_dir.parent / "processed",
        help="Destination directory for processed chunks (default: data/processed).",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=220,
        help="Maximum words per chunk (default: 220).",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=40,
        help="Words of overlap between consecutive chunks (default: 40).",
    )
    return parser.parse_args(argv)


def run(argv: Sequence[str] | None = None) -> Path:
    args = parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)

    output_path = args.output / "wafr_chunks.jsonl"
    total_chunks = 0

    with output_path.open("w", encoding="utf-8") as writer:
        for document in discover_documents(args.input):
            if document.doc_type == "pdf":
                # PDFs require further processing (e.g. OCR) which is not implemented yet.
                continue
            for payload in build_chunk_payloads(
                document,
                chunk_size=args.chunk_size,
                overlap=args.overlap,
            ):
                writer.write(json.dumps(payload, ensure_ascii=False) + "\n")
                total_chunks += 1

    print(f"Generated {total_chunks} chunks -> {output_path}")  # noqa: T201
    return output_path


def main() -> None:
    run()


if __name__ == "__main__":
    main()
