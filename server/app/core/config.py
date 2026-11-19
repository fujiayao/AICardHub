import re
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_root_path(value: str) -> str:
    """An origin-relative deployment prefix, never an external redirect target."""
    if value in ("", "/"):
        return ""
    normalized = value.removesuffix("/")
    if not re.fullmatch(r"(?:/[A-Za-z0-9_-]+)+", normalized):
        raise ValueError("AICARD_ROOT_PATH must be a local absolute path prefix")
    return normalized


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).parents[2] / ".env", extra="ignore")
    database_url: str
    test_database_url: str = ""
    jwt_secret: SecretStr
    app_env: str = "local"
    aicard_root_path: str = ""
    aicard_card_only: bool = False

    @field_validator("aicard_root_path")
    @classmethod
    def valid_root_path(cls, value: str) -> str:
        return normalize_root_path(value)

    llm_mode: str = "fake"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_api_mode: Literal["chat_completions", "responses"] = "chat_completions"
    llm_timeout: float = 30
    llm_fallback_enabled: bool = False
    llm_fallback_base_url: str = ""
    llm_fallback_model: str = ""
    llm_fallback_api_key: str = ""
    llm_fallback_api_mode: Literal["chat_completions", "responses"] = "chat_completions"
    llm_tertiary_enabled: bool = False
    llm_tertiary_base_url: str = ""
    llm_tertiary_model: str = ""
    llm_tertiary_api_key: str = ""
    llm_tertiary_api_mode: Literal["chat_completions", "responses"] = "chat_completions"
    kb_root: str = "../data/kb"
    upload_root: str = "../data/uploads"
    public_base_url: str = "http://127.0.0.1:5173"
    visitor_daily_limit: int = 50
    card_daily_limit: int = 10000
    global_daily_limit: int = 100000
    test_retention_days: int = 7
    notification_retention_days: int = 90
    visitor_retention_days: int = 180


@lru_cache
def get_settings() -> Settings:
    return Settings()
