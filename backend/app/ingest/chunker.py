from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class TextChunk:
    """Represents a slice of a larger document ready for indexing."""

    content: str
    word_count: int


def chunk_text(
    text: str,
    *,
    max_words: int = 220,
    overlap_words: int = 40,
) -> List[TextChunk]:
    """Split text into overlapping word windows suitable for embedding.

    Args:
        text: Normalised string input (paragraphs separated by newlines).
        max_words: Maximum number of words per chunk.
        overlap_words: How many trailing words to repeat in the next chunk.

    Returns:
        Ordered list of `TextChunk` instances.
    """

    if max_words <= 0:
        raise ValueError("max_words must be > 0")
    if overlap_words < 0:
        raise ValueError("overlap_words must be >= 0")

    paragraphs = [line.strip() for line in text.splitlines() if line.strip()]
    if not paragraphs:
        return []

    chunks: list[TextChunk] = []
    carryover: list[str] = []

    for paragraph in paragraphs:
        words = paragraph.split()
        carryover.extend(words)

        while len(carryover) >= max_words:
            slice_words = carryover[:max_words]
            chunk_text_value = " ".join(slice_words)
            chunks.append(TextChunk(content=chunk_text_value, word_count=len(slice_words)))

            carryover = carryover[max_words - overlap_words if overlap_words else max_words :]

    if carryover:
        chunk_text_value = " ".join(carryover)
        chunks.append(TextChunk(content=chunk_text_value, word_count=len(carryover)))

    return chunks


def iter_chunks_for_documents(
    documents: Iterable[str],
    *,
    max_words: int = 220,
    overlap_words: int = 40,
) -> Iterable[List[TextChunk]]:
    """Utility generator that yields chunks for each provided document."""
    for document in documents:
        yield chunk_text(document, max_words=max_words, overlap_words=overlap_words)
