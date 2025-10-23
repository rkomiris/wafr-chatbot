from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, get_settings
from .schemas import ChatRequest, ChatResponse
from .services.chat_service import RetrievalAugmentedChatService
from .ingest.model_loader import get_embedding_model
from .retrieval.in_memory_store import InMemoryVectorStore
from .services.llm.deepseek import DeepSeekClient


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

    store = None
    try:
        store = InMemoryVectorStore(settings.embeddings_file)
    except (FileNotFoundError, ValueError):
        store = None

    embedder = get_embedding_model(settings.embedding_model_name)

    llm_client = None
    if settings.deepseek_api_key:
        llm_client = DeepSeekClient(
            api_key=settings.deepseek_api_key,
            base_url=str(settings.deepseek_base_url),
            model=settings.deepseek_model_name,
            temperature=settings.deepseek_temperature,
            max_output_tokens=settings.deepseek_max_output_tokens,
        )

    chat_service = RetrievalAugmentedChatService(
        settings=settings,
        embedder=embedder,
        store=store,
        llm_client=llm_client,
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
