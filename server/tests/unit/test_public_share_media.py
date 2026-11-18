"""Image response and public-data boundary for visitor sharing."""

from io import BytesIO

import httpx
import pytest
from fastapi import FastAPI
from PIL import Image

from app.core.db import get_db
from app.core.errors import AppError, register_errors
from app.modules.workspace import public_share_media as media
from app.modules.workspace import router as routes
from app.modules.workspace import schemas as s


@pytest.mark.parametrize("status", ["active", "disabled"])
async def test_公开图片返回真实JPEG且拒绝停用卡(monkeypatch, status):
    app = FastAPI()
    register_errors(app)
    app.include_router(routes.public_redirect)

    async def database():
        yield object()

    async def public_card(db, code, campaign_id):
        return s.PublicCard(
            code=code,
            status=status,
            name="测试姓名",
            title="经理",
            company=s.CompanyData(name="测试企业"),
        )

    app.dependency_overrides[get_db] = database
    monkeypatch.setattr(media.service, "public_card", public_card)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://test"
    ) as client:
        result = await client.get("/c/synthetic?image=1&s=poster")
    if status == "disabled":
        assert result.status_code == 409
        assert result.json()["code"] == "CARD_DISABLED"
    else:
        assert result.status_code == 200
        assert result.headers["content-type"] == "image/jpeg"
        assert result.headers["cache-control"] == "no-store"
        with Image.open(BytesIO(result.content)) as image:
            assert image.size == (900, 1160)
            assert image.getpixel((5, 1100))[0] < 20


def test_图片渲染入口也拒绝停用个人数据():
    card = s.PublicCard(
        code="disabled", status="disabled", name="PRIVATE", company=s.CompanyData(name="企业")
    )
    with pytest.raises(AppError):
        media.render(card, "https://cards.example/c/disabled")


def test_头像不读取外部网址或越界文件(monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("拒绝的头像地址不得读取配置、文件或图片")

    monkeypatch.setattr(media, "get_settings", unexpected)
    monkeypatch.setattr(media.Image, "open", unexpected)
    # PublicCard permits valid HTTPS assets; this renderer intentionally accepts local UUID JPEGs only.
    external = s.PublicCard(
        code="test",
        status="active",
        photo_url="https://private.example/portrait.jpg",
        company=s.CompanyData(name="企业"),
    )
    assert media.portrait(external, 180) is None
    with pytest.raises(ValueError, match="unsafe file URL"):
        s.PublicCard(
            code="test",
            status="active",
            photo_url="/files/../../secret.jpg",
            company=s.CompanyData(name="企业"),
        )
    # Defense in depth if invalid historical data bypassed schema validation.
    legacy = external.model_copy(update={"photo_url": "/files/../../secret.jpg"})
    assert media.portrait(legacy, 180) is None
