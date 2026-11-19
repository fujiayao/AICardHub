"""Deployment-owned switch; an account or an admin database setting cannot bypass it."""

from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode


def card_only() -> bool:
    return get_settings().aicard_card_only


def require_ai() -> None:
    if card_only():
        raise AppError(ErrorCode.NOT_FOUND, 404, "此版本不提供 AI 对话功能")
