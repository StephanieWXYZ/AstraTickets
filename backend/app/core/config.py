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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
