"""Validated operational configuration. Every load sees committed MySQL values."""

import base64
import hashlib
from typing import Any, Literal
from urllib.parse import urlsplit

from cryptography.fernet import Fernet, InvalidToken
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.integrations.llm.client import LLMClient, build_client
from app.modules.workspace.models import AuditLog, Employee, Setting
from app.modules.workspace.release_mode import require_ai

MASK = "********"
SECRET_KEYS = frozenset({"llm_api_key", "llm_fallback_api_key", "llm_tertiary_api_key"})


class RuntimeSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    llm_mode: Literal["fake", "openai"] = "fake"
    llm_base_url: str = Field(default="", max_length=500)
    llm_model: str = Field(default="", max_length=160)
    llm_api_key: str = Field(default="", max_length=4096, repr=False)
    llm_api_mode: Literal["chat_completions", "responses"] = "chat_completions"
    llm_timeout: float = Field(default=30, ge=1, le=120)
    llm_fallback_enabled: bool = False
    llm_fallback_base_url: str = Field(default="", max_length=500)
    llm_fallback_model: str = Field(default="", max_length=160)
    llm_fallback_api_key: str = Field(default="", max_length=4096, repr=False)
    llm_fallback_api_mode: Literal["chat_completions", "responses"] = "chat_completions"
    llm_tertiary_enabled: bool = False
    llm_tertiary_base_url: str = Field(default="", max_length=500)
    llm_tertiary_model: str = Field(default="", max_length=160)
    llm_tertiary_api_key: str = Field(default="", max_length=4096, repr=False)
    llm_tertiary_api_mode: Literal["chat_completions", "responses"] = "chat_completions"
    visitor_daily_limit: int = Field(default=50, ge=1, le=100000)
    card_daily_limit: int = Field(default=10000, ge=1, le=10000000)
    global_daily_limit: int = Field(default=100000, ge=1, le=100000000)
    test_retention_days: int = Field(default=7, ge=1, le=3650)
    notification_retention_days: int = Field(default=90, ge=1, le=3650)
    visitor_retention_days: int = Field(default=180, ge=1, le=3650)
    sensitive_words: list[str] = Field(default_factory=list, max_length=200)


def cipher() -> Fernet:
    digest = hashlib.sha256(get_settings().jwt_secret.get_secret_value().encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def defaults() -> dict[str, Any]:
    env = get_settings()
    return {key: getattr(env, key) for key in RuntimeSettings.model_fields if hasattr(env, key)}


def validate(values: dict[str, Any]) -> RuntimeSettings:
    try:
        result = RuntimeSettings.model_validate(values)
        for key in ("llm_base_url", "llm_fallback_base_url", "llm_tertiary_base_url"):
            value = getattr(result, key)
            if value:
                parsed = urlsplit(value)
                if (
                    parsed.scheme not in ("http", "https")
                    or not parsed.hostname
                    or parsed.username
                    or parsed.password
                    or parsed.query
                    or parsed.fragment
                    or any(ord(c) < 32 for c in value)
                    or "\\" in value
                ):
                    raise ValueError("invalid provider URL")
        if any(not word.strip() or len(word) > 100 for word in result.sensitive_words):
            raise ValueError("invalid sensitive words")
        if result.llm_mode == "openai":
            if not all((result.llm_base_url, result.llm_model.strip(), result.llm_api_key.strip())):
                raise ValueError("incomplete primary provider")
            for prefix in ("llm_fallback", "llm_tertiary"):
                if getattr(result, f"{prefix}_enabled") and not all(
                    getattr(result, f"{prefix}_{field}").strip()
                    for field in ("base_url", "model", "api_key")
                ):
                    raise ValueError("incomplete enabled provider")
        return result
    except (ValidationError, ValueError) as exc:
        # Never return pydantic's input_value, provider URL credentials or key text.
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            422,
            "配置值类型或范围无效；启用真实模型前需完整配置所有已启用的连接",
        ) from exc


async def load(db: AsyncSession) -> RuntimeSettings:
    values = defaults()
    rows = (
        await db.scalars(select(Setting).where(Setting.key.in_(RuntimeSettings.model_fields)))
    ).all()
    for row in rows:
        value = row.value
        if row.key in SECRET_KEYS:
            try:
                value = cipher().decrypt(str(value).encode()).decode() if value else ""
            except (InvalidToken, UnicodeError) as exc:
                raise AppError(
                    ErrorCode.VALIDATION_ERROR, 503, "模型密钥无法解密，请管理员重新配置"
                ) from exc
        values[row.key] = value
    return validate(values)


def require_key(key: str) -> None:
    if key not in RuntimeSettings.model_fields:
        raise AppError(ErrorCode.VALIDATION_ERROR, 422, "不支持的运行配置项")


async def get_value(db: AsyncSession, key: str) -> Any:
    require_key(key)
    values = await load(db)
    value = getattr(values, key)
    return MASK if key in SECRET_KEYS and value else value


async def save(
    db: AsyncSession, actor: Employee, key: str, value: Any, *, clear_secret: bool = False
) -> Any:
    require_key(key)
    if clear_secret and key not in SECRET_KEYS:
        raise AppError(ErrorCode.VALIDATION_ERROR, 422, "仅密钥支持显式清空")
    if key in SECRET_KEYS and not clear_secret and value in (MASK, ""):
        return await get_value(db, key)
    if clear_secret:
        if value not in (None, "", MASK):
            raise AppError(ErrorCode.VALIDATION_ERROR, 422, "清空密钥时不可同时提交新值")
        value = ""
    current = await load(db)
    candidate = current.model_dump()
    candidate[key] = value
    validate(candidate)
    row = await db.scalar(select(Setting).where(Setting.key == key))
    encoded = cipher().encrypt(value.encode()).decode() if key in SECRET_KEYS and value else value
    if row is None:
        db.add(Setting(key=key, value=encoded))
    else:
        row.value = encoded
    db.add(
        AuditLog(
            operator_id=actor.id,
            action="setting.update",
            target=key,
            detail={"cleared": clear_secret},
        )
    )
    await db.commit()
    return await get_value(db, key)


def clients(settings: RuntimeSettings) -> tuple[LLMClient, list[LLMClient]]:
    require_ai()
    # Validate the entire chain before allocating any HTTP transport.
    settings = validate(settings.model_dump())
    primary = build_client(settings)
    fallbacks: list[LLMClient] = []
    if settings.llm_mode == "openai":
        for prefix in ("llm_fallback", "llm_tertiary"):
            if getattr(settings, f"{prefix}_enabled"):
                fallbacks.append(
                    build_client(
                        {
                            "llm_mode": "openai",
                            "llm_api_mode": getattr(settings, f"{prefix}_api_mode"),
                            "llm_base_url": getattr(settings, f"{prefix}_base_url"),
                            "llm_model": getattr(settings, f"{prefix}_model"),
                            "llm_api_key": getattr(settings, f"{prefix}_api_key"),
                            "llm_timeout": settings.llm_timeout,
                        }
                    )
                )
    return primary, fallbacks


def generation_lease_seconds(settings: RuntimeSettings) -> int:
    attempts = 1 + (
        int(settings.llm_fallback_enabled) + int(settings.llm_tertiary_enabled)
        if settings.llm_mode == "openai"
        else 0
    )
    return int(settings.llm_timeout * attempts) + 30


async def close_client(client: LLMClient | None) -> None:
    close = getattr(client, "aclose", None)
    if close is not None:
        await close()
