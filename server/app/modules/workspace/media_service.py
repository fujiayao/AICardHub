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
    font_path = Path("C:/Windows/Fonts/msyh.ttc")
    font = (
        ImageFont.truetype(str(font_path), 36)
        if font_path.exists()
        else ImageFont.load_default(size=36)
    )
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
