"""Public share URLs without image rendering or filesystem side effects."""

from dataclasses import dataclass
from html import escape
from urllib.parse import quote, urlencode

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings, normalize_root_path
from app.core.errors import AppError, ErrorCode
from app.modules.workspace import campaign_service
from app.modules.workspace import schemas as s
from app.modules.workspace import service as shared


def card_path(
    code: str, source: s.Source = "link", campaign_id: int | None = None, *, short: bool = True
) -> str:
    query: dict[str, str | int] = {"s": source}
    if campaign_id is not None:
        query["e"] = campaign_id
    section = "c" if short else "card"
    return f"/{section}/{quote(code, safe='')}?{urlencode(query)}"


def short_url(code: str, source: s.Source = "link", campaign_id: int | None = None) -> str:
    return get_settings().public_base_url.rstrip("/") + card_path(code, source, campaign_id)


async def validate_campaign(db: AsyncSession, campaign_id: int | None) -> None:
    if campaign_id is not None:
        await campaign_service.get(db, campaign_id, public=True)


async def share_link(
    db: AsyncSession, employee_id: int, source: s.Source = "link", campaign_id: int | None = None
) -> s.ShareLinkData:
    card = await shared.own_card(db, employee_id)
    if card.status != "active":
        raise AppError(ErrorCode.CARD_DISABLED, 409, "该名片已停用，请联系公司")
    await validate_campaign(db, campaign_id)
    return s.ShareLinkData(
        short_url=short_url(card.code, source, campaign_id), source=source, campaign_id=campaign_id
    )


@dataclass(frozen=True)
class ShortLinkResult:
    location: str = ""
    recovery_html: str = ""


def accepts_html(accept: str) -> bool:
    for item in accept.split(","):
        media_type, *parameters = item.strip().lower().split(";")
        if media_type.strip() != "text/html":
            continue
        quality = 1.0
        for parameter in parameters:
            key, separator, value = parameter.strip().partition("=")
            if separator and key == "q":
                try:
                    quality = float(value)
                except ValueError:
                    quality = 0.0
        if 0 < quality <= 1:
            return True
    return False


def campaign_recovery_html(location: str) -> str:
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>活动链接已失效</title></head><body><main>"
        "<h1>活动链接已失效</h1><p>该活动不存在、尚未开始或已经结束。</p>"
        "<p>您仍可查看这位员工的普通名片。</p>"
        f'<p><a href="{escape(location, quote=True)}">打开普通名片</a></p>'
        "</main></body></html>"
    )


async def resolve_short_link(
    db: AsyncSession,
    code: str,
    root_path: str,
    source: s.Source = "link",
    campaign_id: int | None = None,
    accept: str = "",
) -> ShortLinkResult:
    # Disabled cards still reach the H5 disabled state; no personal data is returned here.
    await shared.by_code(db, code)
    prefix = normalize_root_path(root_path)
    try:
        await validate_campaign(db, campaign_id)
    except AppError as exc:
        if campaign_id is None or exc.code != ErrorCode.NOT_FOUND or not accepts_html(accept):
            raise
        location = prefix + card_path(code, source, short=False)
        return ShortLinkResult(recovery_html=campaign_recovery_html(location))
    return ShortLinkResult(location=prefix + card_path(code, source, campaign_id, short=False))
