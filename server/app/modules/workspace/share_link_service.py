"""Public share URLs without image rendering or filesystem side effects."""

from dataclasses import dataclass
from html import escape
from urllib.parse import parse_qs, quote, urlencode, urlsplit, urlunsplit

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
    preview_html: str = ""


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


def _absolute_asset(value: str) -> str:
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value
    base = urlsplit(get_settings().public_base_url)
    prefix = base.path.rstrip("/")
    path = value if prefix and value.startswith(prefix + "/") else prefix + "/" + value.lstrip("/")
    return urlunsplit((base.scheme, base.netloc, path, "", ""))


def share_preview_html(card: s.PublicCard, location: str) -> str:
    """Crawler-readable preview that keeps the normal short-link redirect intact."""
    role = "｜".join(value for value in (card.title, card.dept) if value)
    brand = card.company.short_name or card.company.name
    title = " · ".join(value for value in (card.name, role, brand) if value) or "数科商务数字名片"
    description = (
        card.business_scope or card.intro or "了解业务方向与合作方式，查看商务数字名片"
    ).strip()[:120]
    safe_title = escape(title)
    safe_description = escape(description)
    # location already includes root_path; append it to the configured origin only.
    base = urlsplit(get_settings().public_base_url)
    absolute_location = urlunsplit((base.scheme, base.netloc, "", "", "")) + location
    event = parse_qs(urlsplit(location).query).get("e", [""])[0]
    campaign_id = int(event) if event.isascii() and event.isdecimal() else None
    image = short_url(card.code, "poster", campaign_id).replace("?", "?image=1&", 1)
    safe_location = escape(absolute_location, quote=True)
    safe_image = escape(image, quote=True)
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{safe_title}</title><meta name="description" content="{safe_description}">'
        f'<meta property="og:type" content="profile"><meta property="og:title" content="{safe_title}">'
        f'<meta property="og:description" content="{safe_description}"><meta property="og:url" content="{safe_location}">'
        f'<meta property="og:image" content="{safe_image}"><meta property="og:site_name" content="{escape(brand)}">'
        '<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:title" content="{safe_title}"><meta name="twitter:description" content="{safe_description}">'
        f'<meta name="twitter:image" content="{safe_image}">'
        f'<meta http-equiv="refresh" content="0;url={safe_location}"></head>'
        '<body style="margin:0;background:#06090c;color:#e7eef5;font-family:system-ui,-apple-system, sans-serif">'
        f'<main style="max-width:480px;margin:0 auto;padding:48px 24px;background:linear-gradient(160deg,#0f161d,#06090c);min-height:100vh">'
        f'<div style="color:#2fd6b4;letter-spacing:.12em;font-size:12px">{escape(brand)}</div>'
        f'<h1 style="font-size:28px;margin:24px 0 8px">{escape(card.name or "商务联系人")}</h1>'
        f'<p style="color:#93a7b6;margin:0;line-height:1.6">{escape(role or "商务合作")}</p>'
        f'<p style="margin-top:32px;line-height:1.7">{safe_description}</p>'
        f'<a href="{safe_location}" style="display:inline-block;margin-top:24px;color:#06090c;background:#2fd6b4;padding:12px 20px;border-radius:12px;text-decoration:none;font-weight:700">打开名片</a>'
        "</main></body></html>"
    )


async def resolve_short_link(
    db: AsyncSession,
    code: str,
    root_path: str,
    source: s.Source = "link",
    campaign_id: int | None = None,
    accept: str = "",
    preview: bool = False,
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
    location = prefix + card_path(code, source, campaign_id, short=False)
    if preview:
        card = await shared.public_card(db, code, campaign_id)
        if card.status != "active":
            return ShortLinkResult(location=location)
        return ShortLinkResult(location=location, preview_html=share_preview_html(card, location))
    return ShortLinkResult(location=location)
