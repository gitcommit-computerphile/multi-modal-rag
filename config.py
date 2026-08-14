from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""
    openai_api_key: str = ""

    database_url: str = "postgresql+psycopg://rag:rag@localhost:5432/multimodal_rag"

    vlm_provider: str = "anthropic"
    vlm_model: str = "claude-sonnet-5"
    vlm_model_cheap: str = "claude-haiku-4-5"

    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536

    storage_dir: str = "./data"
    api_base_url: str = "http://localhost:8000"

    @property
    def pages_dir(self) -> Path:
        return Path(self.storage_dir) / "pages"

    @property
    def crops_dir(self) -> Path:
        return Path(self.storage_dir) / "crops"

    @property
    def uploads_dir(self) -> Path:
        return Path(self.storage_dir) / "uploads"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    for d in (settings.pages_dir, settings.crops_dir, settings.uploads_dir):
        d.mkdir(parents=True, exist_ok=True)
    return settings
