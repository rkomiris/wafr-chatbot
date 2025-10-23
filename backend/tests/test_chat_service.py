from app.schemas import ChatRequest
from app.services.chat_service import ChatService


def test_chat_service_echoes_prompt() -> None:
    service = ChatService(canned_sources=["source-a"])
    payload = ChatRequest(query="Explain the security pillar.")

    response = service.answer(payload)

    assert "security pillar" in response.answer
    assert response.sources == ["source-a"]
    assert response.answer.startswith("Thanks for trying out")
