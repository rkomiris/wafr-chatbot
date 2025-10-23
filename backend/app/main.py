from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, get_settings
from .schemas import ChatRequest, ChatResponse
from .services.chat_service import ChatService


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    chat_service = ChatService(
        canned_sources=[
            "https://docs.aws.amazon.com/wellarchitected/latest/framework",
            "https://docs.aws.amazon.com/wellarchitected/latest/userguide",
        ]
    )

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/chat", response_model=ChatResponse, tags=["chat"])
    def chat_endpoint(
        payload: ChatRequest, service: ChatService = Depends(lambda: chat_service)
    ) -> ChatResponse:
        try:
            return service.answer(payload)
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc

    return app


def get_app() -> FastAPI:
    return create_app(get_settings())


app = get_app()
