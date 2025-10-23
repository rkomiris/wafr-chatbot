from __future__ import annotations

from typing import Iterable

from ..schemas import ChatRequest, ChatResponse


class ChatService:
    """Placeholder chat service until retrieval + LLM are integrated."""

    def __init__(self, canned_sources: Iterable[str] | None = None) -> None:
        self._sources = list(canned_sources or [])

    def answer(self, payload: ChatRequest) -> ChatResponse:
        prompt_preview = payload.query.strip()
        if not prompt_preview:
            raise ValueError("Query must not be empty.")

        history_hint = ""
        if payload.history:
            history_hint = (
                f" I've also received {len(payload.history)} prior message(s) "
                "in this conversation."
            )

        answer = (
            "Thanks for trying out the WAFR chatbot UI. Retrieval-Augmented Generation "
            "is not wired up yet, but this endpoint is functioning. "
            "Ask about the AWS Well-Architected Framework and I'll echo your question "
            f"back for now: '{prompt_preview}'.{history_hint}"
        )

        return ChatResponse(answer=answer, sources=self._sources)
