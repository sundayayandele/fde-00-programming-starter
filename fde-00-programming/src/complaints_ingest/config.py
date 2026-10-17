"""Runtime settings, read from environment variables (and .env for local runs)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    service_name: str = "fde-00-programming"
    environment: str = "local"
    log_level: str = "INFO"

    # SQLite locally; Postgres in Compose, Kubernetes and the clouds, e.g.
    # postgresql+psycopg://complaints:password@db:5432/complaints
    database_url: str = "sqlite:///artifacts/complaints.db"

    cfpb_api_url: str = (
        "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
    )
    cfpb_page_size: int = 500

    # Kept from the template for later phases; this repo makes no LLM calls.
    llm_provider: str = "mistral"
    llm_providers_file: str = "config/providers.yaml"
    llm_timeout_seconds: float = 30.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
