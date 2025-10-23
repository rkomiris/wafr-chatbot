from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role such as 'user' or 'assistant'.")
    content: str = Field(..., description="Message text.")


class ChatRequest(BaseModel):
    query: str = Field(..., description="Natural language question from the user.")
    history: Optional[List[ChatMessage]] = Field(
        default=None, description="Optional chat history for context."
    )


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Assistant answer for the query.")
    sources: List[str] = Field(
        default_factory=list,
        description="List of document identifiers or URLs used for the answer.",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="UTC timestamp for the response."
    )
