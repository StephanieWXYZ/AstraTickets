from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AstraTickets API"
    database_url: str = "sqlite:///./astratickets.db"
    secret_key: str = Field(
        default="local-development-key-change-before-production",
        min_length=32,
    )
    access_token_expire_minutes: int = Field(default=30, gt=0)
    chroma_path: str = "./chroma_data"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    knowledge_min_score: float = Field(default=0.4, ge=0, le=1)
    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None
    llm_timeout_seconds: float = Field(default=30, gt=0, le=120)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
