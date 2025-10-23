from __future__ import annotations

from typing import Iterable, Optional, Protocol

from sentence_transformers import SentenceTransformer

from ..config import Settings
from ..schemas import ChatMessage, ChatRequest, ChatResponse
from ..retrieval.in_memory_store import InMemoryVectorStore, RetrievedChunk


class LLMClient(Protocol):
    def generate(self, prompt: str, *, system_prompt: Optional[str] = None) -> str:
        ...


class RetrievalAugmentedChatService:
    """Retrieval-Augmented Generation pipeline using an in-memory vector store."""

    def __init__(
        self,
        *,
        settings: Settings,
        embedder: SentenceTransformer,
        store: Optional[InMemoryVectorStore],
        llm_client: Optional[LLMClient],
    ) -> None:
        self._settings = settings
        self._embedder = embedder
        self._store = store
        self._llm_client = llm_client

    def _format_history(self, history: Iterable[ChatMessage] | None) -> str:
        if not history:
            return ""
        snippets = []
        for message in history:
            role = message.role
            snippets.append(f"{role.capitalize()}: {message.content}")
        return "\n".join(snippets)

    def _build_prompt(self, query: str, context_chunks: list[RetrievedChunk], history: str) -> str:
        context_lines = []
        for idx, chunk in enumerate(context_chunks, start=1):
            label = chunk.source or chunk.chunk_id
            context_lines.append(f"[{idx}] Source: {label}\n{chunk.text}")
        context_block = "\n\n".join(context_lines)

        prompt_parts = [
            "You are an assistant that answers questions about the AWS Well-Architected Framework.",
            "Use the provided context strictly. Cite the source labels (e.g., [1]) when referencing information.",
            "If the answer is not contained in the context, state that explicitly.",
        ]
        if history:
            prompt_parts.append("Conversation so far:\n" + history)
        prompt_parts.append("Context:\n" + context_block)
        prompt_parts.append("Question:\n" + query)
        return "\n\n".join(prompt_parts)

    def answer(self, payload: ChatRequest) -> ChatResponse:
        query = payload.query.strip()
        if not query:
            raise ValueError("Query must not be empty.")

        query_vector = self._embedder.encode(
            [query],
            convert_to_numpy=True,
        )[0]

        if not self._store:
            return ChatResponse(
                answer=(
                    "Embeddings store is not initialised. Generate embeddings first "
                    "using the ingestion pipeline, then restart the backend."
                ),
                sources=[],
            )

        retrieved = self._store.search(query_vector, top_k=self._settings.retrieval_top_k)
        sources = []
        for chunk in retrieved:
            if chunk.source and chunk.source not in sources:
                sources.append(chunk.source)

        history_text = self._format_history(payload.history)

        if not retrieved:
            return ChatResponse(
                answer="I could not retrieve any relevant context for that query yet. "
                "Please ensure the ingestion pipeline has populated the embeddings file.",
                sources=[],
            )

        if not self._llm_client:
            preview_lines = [
                "DeepSeek API key not configured. Showing top matches instead:",
            ]
            for idx, chunk in enumerate(retrieved, start=1):
                preview_lines.append(
                    f"{idx}. {chunk.summary or chunk.text[:120]} "
                    f"(source: {chunk.source or chunk.chunk_id})"
                )
            return ChatResponse(answer="\n".join(preview_lines), sources=sources)

        prompt = self._build_prompt(query, retrieved, history_text)
        answer = self._llm_client.generate(
            prompt,
            system_prompt="You are an AWS Well-Architected Framework assistant.",
        )

        return ChatResponse(answer=answer, sources=sources)
