from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Asterism Memory API"
    environment: str = "development"
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/asterism",
        alias="DATABASE_URL",
    )
    default_workspace_id: str = "demo"
    default_context_tokens: int = 2000
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="openai/gpt-4o-mini", alias="OPENROUTER_MODEL")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
