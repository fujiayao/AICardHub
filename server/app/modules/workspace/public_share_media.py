"""Public business-card image, rendered from the same public projection as the H5."""

import re
from io import BytesIO
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError
from qrcode.image.pil import PilImage
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.modules.workspace import media_service, schemas, service, share_link_service

# Mirrors the visitor dark-card palette. No external images or fonts are downloaded.
BACKGROUND = "#06090c"
SURFACE = "#0f161d"
MINT = "#2fd6b4"
TEXT = "#e7eef5"
MUTED = "#93a7b6"
LINE = "#24383e"


def lines(draw: ImageDraw.ImageDraw, value: str, size: int, width: int, count: int) -> list[str]:
    font = media_service.poster_font(size)
    result: list[str] = []
    line = ""
    for char in " ".join(value.split()):
        if draw.textlength(line + char, font=font) > width:
            result.append(line)
            line = char
            if len(result) == count:
                result[-1] = result[-1][:-1] + "…"
                return result
        else:
            line += char
    if line:
        result.append(line)
    return result


def text_block(
    draw: ImageDraw.ImageDraw,
    value: str,
    x: int,
    y: int,
    size: int,
    width: int,
    count: int = 1,
    color: str = TEXT,
) -> int:
    for line in lines(draw, value, size, width, count):
        draw.text((x, y), line, font=media_service.poster_font(size), fill=color)
        y += size + 12
    return y


def portrait(card: schemas.PublicCard, size: int) -> Image.Image | None:
    value = card.photo_url or ""
    match = re.fullmatch(r"/files/([0-9a-f]{32}(?:-bg)?\.jpg)", value)
    if not match:
        return None
    root = Path(get_settings().upload_root).resolve()
    path = (root / match.group(1)).resolve()
    if path.parent != root or not path.is_file():
        return None
    try:
        with Image.open(path) as source:
            if source.width * source.height > 25_000_000:
                return None
            return ImageOps.fit(source.convert("RGB"), (size, size), centering=(0.5, 0.25))
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError):
        return None


def render(card: schemas.PublicCard, url: str) -> bytes:
    if card.status != "active":
        raise AppError(ErrorCode.CARD_DISABLED, 409)
    image = Image.new("RGB", (900, 1160), BACKGROUND)
    draw = ImageDraw.Draw(image)
    for y in range(490):
        weight = (1 - y / 490) ** 2
        draw.line(
            (0, y, 900, y), fill=(int(6 + 12 * weight), int(9 + 43 * weight), int(12 + 40 * weight))
        )
    draw.rounded_rectangle((46, 44, 54, 74), radius=4, fill=MINT)
    text_block(draw, card.company.short_name or card.company.name, 72, 38, 26, 760, color=MINT)
    draw.ellipse((644, 135, 838, 329), fill=LINE, outline=MINT, width=2)
    photo = portrait(card, 180)
    if photo:
        mask = Image.new("L", (180, 180), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 179, 179), fill=255)
        image.paste(photo, (651, 142), mask)
    else:
        draw.text(
            (708, 188), (card.name or "名")[:1], font=media_service.poster_font(66), fill=MINT
        )
    text_block(draw, card.name or "商务名片", 54, 132, 60, 550, count=2)
    text_block(draw, card.title or card.dept or "", 56, 300, 28, 770, count=2, color=TEXT)
    text_block(draw, card.company.name, 56, 390, 25, 770, count=2, color=MINT)
    draw.line((56, 485, 844, 485), fill=LINE, width=2)
    summary = card.business_scope or card.intro or ""
    if summary:
        text_block(draw, "业务与合作", 56, 518, 21, 770, color=MINT)
        text_block(draw, summary, 56, 564, 27, 770, count=3, color=TEXT)
    if card.mobile:
        text_block(draw, f"电话  {card.mobile}", 56, 710, 25, 770, color=MUTED)
    draw.rounded_rectangle((40, 800, 860, 1118), radius=28, fill=SURFACE, outline=LINE, width=2)
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=7, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    qr_image = qr.make_image(image_factory=PilImage).get_image().convert("RGB")
    qr_image = ImageOps.contain(qr_image, (260, 260), method=Image.Resampling.NEAREST)
    image.paste(qr_image, (70, 826))
    text_block(draw, "长按识别 · 查看名片", 368, 858, 28, 440, count=2)
    text_block(draw, "了解业务与合作方向", 368, 960, 22, 430, color=MUTED)
    text_block(draw, "保存联系方式 · 与 AI 助手交流", 368, 1000, 21, 430, count=2, color=MINT)
    output = BytesIO()
    image.save(output, "JPEG", quality=92, optimize=True)
    return output.getvalue()


async def public_image(db: AsyncSession, code: str, campaign_id: int | None) -> bytes:
    card = await service.public_card(db, code, campaign_id)
    if card.status != "active":
        raise AppError(ErrorCode.CARD_DISABLED, 409)
    await share_link_service.validate_campaign(db, campaign_id)
    url = share_link_service.short_url(code, "poster", campaign_id)
    return await run_in_threadpool(render, card, url)
