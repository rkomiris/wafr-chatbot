import json
from pathlib import Path

import numpy as np

from app.config import Settings
from app.retrieval.in_memory_store import InMemoryVectorStore
from app.schemas import ChatMessage, ChatRequest
from app.services.chat_service import RetrievalAugmentedChatService


class DummyEmbedder:
    def encode(self, sentences, convert_to_numpy=True):
        vectors = []
        for text in sentences:
            if "operational" in text.lower():
                vectors.append(np.array([1.0, 0.0], dtype=np.float32))
            else:
                vectors.append(np.array([0.0, 1.0], dtype=np.float32))
        return vectors


class StubLLM:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    def generate(self, prompt: str, *, system_prompt: str | None = None) -> str:
        self.calls.append((prompt, system_prompt))
        return "final answer"


def _write_chunks_file(tmp_path: Path) -> Path:
    records = [
        {
            "chunk_id": "chunk-1",
            "document_id": "doc-1",
            "source": "https://example.com/1",
            "pillar": "Operational Excellence",
            "chunk_index": 1,
            "text": "Operational excellence focuses on continuous improvement.",
            "word_count": 8,
            "summary": "Operational excellence focuses on continuous improvement.",
            "doc_type": "html",
            "embedding": [1.0, 0.0],
        },
        {
            "chunk_id": "chunk-2",
            "document_id": "doc-2",
            "source": "https://example.com/2",
            "pillar": "Security",
            "chunk_index": 1,
            "text": "Security pillar enforces least privilege.",
            "word_count": 6,
            "summary": "Security pillar guidance.",
            "doc_type": "html",
            "embedding": [0.0, 1.0],
        },
    ]

    path = tmp_path / "embeddings.jsonl"
    with path.open("w", encoding="utf-8") as stream:
        for item in records:
            stream.write(json.dumps(item) + "\n")
    return path


def test_chat_service_without_llm_returns_preview(tmp_path) -> None:
    chunks_file = _write_chunks_file(tmp_path)
    settings = Settings(
        embeddings_file=chunks_file,
        deepseek_api_key=None,
        retrieval_top_k=1,
    )

    service = RetrievalAugmentedChatService(
        settings=settings,
        embedder=DummyEmbedder(),
        store=InMemoryVectorStore(chunks_file),
        llm_client=None,
    )

    response = service.answer(ChatRequest(query="Tell me about operational excellence"))

    assert "DeepSeek API key not configured" in response.answer
    assert response.sources == ["https://example.com/1"]


def test_chat_service_with_llm(tmp_path) -> None:
    chunks_file = _write_chunks_file(tmp_path)
    settings = Settings(
        embeddings_file=chunks_file,
        deepseek_api_key="dummy",
        retrieval_top_k=2,
    )
    llm = StubLLM()

    service = RetrievalAugmentedChatService(
        settings=settings,
        embedder=DummyEmbedder(),
        store=InMemoryVectorStore(chunks_file),
        llm_client=llm,
    )

    response = service.answer(
        ChatRequest(
            query="Operational improvements",
            history=[ChatMessage(role="user", content="Hi"), ChatMessage(role="assistant", content="Hello")],
        )
    )

    assert response.answer == "final answer"
    assert response.sources == ["https://example.com/1", "https://example.com/2"]
    assert llm.calls, "LLM should have been invoked"
