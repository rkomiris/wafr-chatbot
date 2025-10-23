from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_title: str = "WAFR Chatbot API"
    api_description: str = (
        "Backend service for the AWS Well-Architected Framework chatbot."
    )
    api_version: str = "0.1.0"

    # CORS
    frontend_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Scraper configuration
    scraper_output_dir: Path = Path(__file__).resolve().parents[2] / "data" / "raw"
    scraper_concurrency: int = 3
    scraper_request_timeout: float = 15.0

    # Retrieval + embeddings
    embeddings_file: Path = (
        Path(__file__).resolve().parents[2] / "data" / "processed" / "wafr_chunks_with_embeddings.jsonl"
    )
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    retrieval_top_k: int = 4

    # LLM (DeepSeek)
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: HttpUrl = "https://api.deepseek.com/v1"
    deepseek_model_name: str = "deepseek-chat"
    deepseek_temperature: float = 0.2
    deepseek_max_output_tokens: int = 600

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("frontend_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
