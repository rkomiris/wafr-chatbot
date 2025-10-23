from app.ingest.chunker import TextChunk, chunk_text


def test_chunk_text_basic_split() -> None:
    text = "Paragraph one.\n\nParagraph two with extra words for testing the limit."
    chunks = chunk_text(text, max_words=5, overlap_words=1)
    contents = [chunk.content for chunk in chunks]
    assert contents[0].split() == ["Paragraph", "one.", "Paragraph", "two", "with"]
    assert contents[1].split()[0] == "with"
    assert sum(chunk.word_count for chunk in chunks) >= 9


def test_chunk_text_empty_returns_empty_list() -> None:
    assert chunk_text("") == []
