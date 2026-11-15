import os
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import qrcode
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from qrcode.image.pil import PilImage
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.modules.workspace import schemas as s
from app.modules.workspace import service as shared
from app.modules.workspace.models import Card

POSTER_FONT_PATHS = (
    "C:/Windows/Fonts/msyh.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/source-han-sans/SourceHanSansSC-Regular.otf",
    "/usr/share/fonts/adobe-source-han-sans/SourceHanSansSC-Regular.otf",
)


def poster_font(size: int = 36) -> ImageFont.FreeTypeFont:
    """Administrator-owned local CJK font; never a request path or network download.

    An explicit override fails closed if misconfigured. Administrators must install
    a Chinese font (e.g. fonts-noto-cjk) or point the override to a CJK font file.
    """
    configured = os.environ.get("AICARD_POSTER_FONT_PATH", "").strip()
    candidates = (configured,) if configured else POSTER_FONT_PATHS
    for value in candidates:
        # Only local, absolute paths. Do not resolve URLs or network shares.
        if "://" in value or value.startswith(("//", "\\\\")):
            continue
        path = Path(value)
        try:
            if not path.is_file():
                continue
            if configured and not path.is_absolute():
                continue
            return ImageFont.truetype(str(path), size)
        except (OSError, ValueError):
            continue
    raise AppError(
        ErrorCode.INTERNAL_ERROR,
        503,
        "海报中文字体不可用，请管理员安装Noto/思源中文字体或配置AICARD_POSTER_FONT_PATH",
    )


def root() -> Path:
    path = Path(get_settings().upload_root)
    path.mkdir(parents=True, exist_ok=True)
    return path


def process_photo(content: bytes) -> tuple[str, str]:
    try:
        with Image.open(BytesIO(content)) as opened:
            if (
                opened.format not in ("JPEG", "PNG", "WEBP")
                or opened.width * opened.height > 25000000
            ):
                raise ValueError("invalid image")
            image = opened.convert("RGB")
            image.thumbnail((750, 1200))
            name = uuid4().hex
            image.save(root() / f"{name}.jpg", quality=88)
            image.thumbnail((390, 700))
            image.save(root() / f"{name}-bg.jpg", quality=80)
        return f"/files/{name}.jpg", f"/files/{name}-bg.jpg"
    except (UnidentifiedImageError, ValueError, OSError, Image.DecompressionBombError) as exc:
        raise AppError(
            ErrorCode.VALIDATION_ERROR, 422, "图片格式无效，仅支持JPEG、PNG、WebP"
        ) from exc


async def photo(db: AsyncSession, card: Card, content: bytes) -> s.PhotoData:
    if len(content) > 5 * 1024 * 1024:
        raise AppError(ErrorCode.VALIDATION_ERROR, 413, "图片不可超过5MB")
    card.photo_url, card.photo_bg_url = await run_in_threadpool(process_photo, content)
    await db.commit()
    return s.PhotoData(photo_url=card.photo_url, photo_bg_url=card.photo_bg_url)


def create_share(
    card: s.CardData, source: str = "link", campaign_id: int | None = None
) -> s.ShareData:
    # Validate before writing either image; never report a garbled poster as success.
    font = poster_font()
    base = get_settings().public_base_url.rstrip("/")
    suffix = f"&e={campaign_id}" if campaign_id is not None else ""
    short = f"{base}/c/{card.code}?s={source}{suffix}"
    token = f"{card.code}-{uuid4().hex[:10]}"
    qr_name, poster_name = f"{token}-qr.png", f"{token}-poster.jpg"
    qr = (
        qrcode.make(f"{base}/c/{card.code}?s=qr{suffix}", image_factory=PilImage)
        .get_image()
        .convert("RGB")
    )
    qr.save(root() / qr_name)
    poster = Image.new("RGB", (750, 1100), "#f0f4fa")
    draw = ImageDraw.Draw(poster)
    draw.text((60, 70), card.name, fill="#14263d", font=font)
    draw.text((60, 140), card.display_title, fill="#14263d", font=font)
    if card.photo_url.startswith("/files/"):
        photo_path = root() / Path(card.photo_url).name
        if photo_path.is_file():
            with Image.open(photo_path) as image:
                image.thumbnail((630, 400))
                poster.paste(image, (60, 230))
    poster_qr = (
        qrcode.make(f"{base}/c/{card.code}?s=poster{suffix}", image_factory=PilImage)
        .get_image()
        .convert("RGB")
    )
    poster.paste(poster_qr.resize((300, 300)), (225, 700))
    draw.text((60, 1020), "扫描二维码，了解更多", fill="#14263d", font=font)
    poster.save(root() / poster_name, quality=88)
    return s.ShareData(
        short_url=short, qr_url=f"/files/{qr_name}", poster_url=f"/files/{poster_name}"
    )


async def share(
    db: AsyncSession, card: Card, source: str = "link", campaign_id: int | None = None
) -> s.ShareData:
    return await run_in_threadpool(
        create_share, await shared.card_data(db, card), source, campaign_id
    )


def escape_vcard(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace("\r", "")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


async def vcard(db: AsyncSession, code: str) -> str:
    card = await shared.public_card(db, code)
    if card.status != "active":
        raise AppError(ErrorCode.CARD_DISABLED, 409)
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"FN:{escape_vcard(card.name or '')}",
        f"ORG:{escape_vcard(card.company.name)}",
        f"TITLE:{escape_vcard(card.title or '')}",
        f"TEL;TYPE=CELL:{escape_vcard(card.mobile or '')}",
        f"EMAIL:{escape_vcard(card.email or '')}",
        "END:VCARD",
        "",
    ]
    return "\r\n".join(lines)


def process_wechat_qr(content: bytes) -> str:
    try:
        with Image.open(BytesIO(content)) as source:
            if (
                source.format not in ("JPEG", "PNG", "WEBP")
                or source.width * source.height > 25000000
            ):
                raise ValueError("invalid image")
            image = source.convert("RGB")
            image.thumbnail((1200, 1200))
            filename = uuid4().hex + "-wechat.png"
            image.save(root() / filename, format="PNG")
            return "/files/" + filename
    except (UnidentifiedImageError, ValueError, OSError, Image.DecompressionBombError) as exc:
        raise AppError(ErrorCode.VALIDATION_ERROR, 422, "二维码图片格式无效") from exc


async def wechat_qr(db: AsyncSession, card: Card, content: bytes) -> s.WechatQRData:
    if len(content) > 5 * 1024 * 1024:
        raise AppError(ErrorCode.VALIDATION_ERROR, 413, "图片不可超过5MB")
    card.wechat_qr_url = await run_in_threadpool(process_wechat_qr, content)
    await db.commit()
    return s.WechatQRData(wechat_qr_url=card.wechat_qr_url)
