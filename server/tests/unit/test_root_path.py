"""Subpath redirects with synthetic dependencies, no DB/network access."""

import httpx
import pytest
from fastapi import FastAPI

from app.core.config import Settings, normalize_root_path
from app.core.db import get_db
from app.modules.workspace import router as routes


@pytest.mark.parametrize(
    ("value", "expected"),
    [("", ""), ("/", ""), ("/aicardhub/", "/aicardhub"), ("/apps/cards", "/apps/cards")],
)
def test_根目录规范化(value, expected):
    assert normalize_root_path(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "//evil.test",
        "https://evil.test",
        "/../evil",
        "/a//b",
        "/a?x=1",
        "/a#b",
        "/a\\b",
        "/%2f%2fevil",
        "/a\nb",
        "relative",
    ],
)
def test_危险根目录拒绝(value):
    with pytest.raises(ValueError):
        normalize_root_path(value)


def test_环境变量控制且默认空路径(monkeypatch):
    monkeypatch.delenv("AICARD_ROOT_PATH", raising=False)
    assert (
        Settings(_env_file=None, database_url="synthetic", jwt_secret="synthetic").aicard_root_path
        == ""
    )
    monkeypatch.setenv("AICARD_ROOT_PATH", "/aicardhub/")
    assert (
        Settings(_env_file=None, database_url="synthetic", jwt_secret="synthetic").aicard_root_path
        == "/aicardhub"
    )


@pytest.mark.parametrize("prefix", ["", "/aicardhub"])
@pytest.mark.parametrize("query", ["", "?s=nfc&e=7", "?s=qr&redirect=https://evil.test"])
async def test_短链保留来源展会且忽略外部跳转参数(monkeypatch, prefix, query):
    app = FastAPI()
    app.include_router(routes.public_redirect)

    async def db():
        yield object()

    async def by_code(db, code):
        assert code == "synthetic"

    async def campaign(db, id, public):
        assert id == 7 and public

    from app.modules.workspace import campaign_service

    monkeypatch.setattr(routes.shared, "by_code", by_code)
    monkeypatch.setattr(campaign_service, "get", campaign)
    app.dependency_overrides[get_db] = db
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, root_path=prefix), base_url="http://test"
    ) as client:
        response = await client.get("/c/synthetic" + query)
    expected = "?s=nfc&e=7" if "nfc" in query else "?s=qr" if "qr" in query else "?s=link"
    assert response.status_code == 302
    assert response.headers["location"] == prefix + "/card/synthetic" + expected
