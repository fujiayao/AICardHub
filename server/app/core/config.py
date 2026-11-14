from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).parents[2] / ".env", extra="ignore")
    database_url: str
    test_database_url: str = ""
    jwt_secret: SecretStr
    app_env: str = "local"
    llm_mode: str = "fake"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout: float = 30
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
