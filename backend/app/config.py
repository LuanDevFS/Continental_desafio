from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # proveedor de IA opcional: si hay API key se usa OpenAI (o un endpoint
    # compatible vía OPENAI_BASE_URL), si no, el asistente extractivo local
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    llm_model: str = "gpt-4o-mini"

    # retrieval
    retrieval_top_k: int = 4
    min_similarity: float = 0.12

    max_upload_bytes: int = 5 * 1024 * 1024
    cors_origins: str = "*"
    frontend_dir: str = str(_REPO_ROOT / "frontend")


@lru_cache
def get_settings() -> Settings:
    return Settings()
