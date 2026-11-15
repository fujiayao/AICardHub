"""Real MySQL, real staff JWTs and HTTP; no model or external network calls."""

from collections.abc import AsyncIterator
from datetime import timedelta
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import delete, func, select

from app.core.config import get_settings
from app.core.db import get_db, utcnow
from app.core.errors import register_errors
from app.core.security import issue_token
from app.modules.workspace import media_service as media
from app.modules.workspace import router as routes
from app.modules.workspace import service as shared
from app.modules.workspace.models import Campaign, Employee, Visit

pytest_plugins = ["test_backend_isolation"]


def auth(employee: Employee) -> dict[str, str]:
    return {
        "Authorization": "Bearer "
        + issue_token(str(employee.id), "staff", employee.role, employee.token_version)
    }


@pytest_asyncio.fixture
async def client(db) -> AsyncIterator[httpx.AsyncClient]:
    app = FastAPI()
    register_errors(app)
    app.include_router(routes.router)
    app.include_router(routes.public_redirect)

    async def current_db():
        yield db

    app.dependency_overrides[get_db] = current_db
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as value:
        yield value


@pytest.mark.parametrize("source", ["nfc", "qr", "poster", "link", "sig"])
async def test_本人轻量分享不渲染图片不记录访问(client, db, employees, monkeypatch, source):
    _, employee, _ = employees
    card = await shared.own_card(db, employee.id)
    before = await db.scalar(
        select(func.count()).select_from(Visit).where(Visit.card_id == card.id)
    )

    def unexpected(*args, **kwargs):
        pytest.fail("轻量分享不得触发图片、字体或上传目录")

    monkeypatch.setattr(media, "poster_font", unexpected)
    monkeypatch.setattr(media, "create_share", unexpected)
    monkeypatch.setattr(media, "root", unexpected)
    response = await client.get(
        "/api/v1/me/card/share-link", params={"s": source}, headers=auth(employee)
    )
    assert response.status_code == 200
    assert response.json() == {
        "short_url": f"{get_settings().public_base_url.rstrip('/')}/c/{card.code}?s={source}",
        "source": source,
        "campaign_id": None,
    }
    after = await db.scalar(select(func.count()).select_from(Visit).where(Visit.card_id == card.id))
    assert after == before


async def test_默认普通分享且同事真实token只能拿本人链接(client, db, employees):
    _, employee, colleague = employees
    own = await shared.own_card(db, employee.id)
    other = await shared.own_card(db, colleague.id)
    first = await client.get("/api/v1/me/card/share-link", headers=auth(employee))
    second = await client.get("/api/v1/me/card/share-link", headers=auth(colleague))
    assert first.status_code == second.status_code == 200
    assert first.json()["short_url"].endswith(f"/c/{own.code}?s=link")
    assert second.json()["short_url"].endswith(f"/c/{other.code}?s=link")
    # Even a valid other-staff token cannot select an employee/card or supply a URL.
    for params in [
        {"employee_id": employee.id},
        {"code": own.code},
        {"url": "https://evil.test"},
        {"jwt": "secret"},
    ]:
        response = await client.get(
            "/api/v1/me/card/share-link", params=params, headers=auth(colleague)
        )
        assert response.status_code == 422 and response.json()["code"] == "VALIDATION_ERROR"


async def test_无本人名片返回404不能回退到同事名片(client, db, employees):
    _, employee, colleague = employees
    missing = Employee(
        company_id=employee.company_id,
        name="合成无名片员工",
        phone="138" + str(uuid4().int)[-8:],
        password_hash=employee.password_hash,
        must_change_pwd=False,
        status="active",
        role="employee",
        token_version=0,
    )
    db.add(missing)
    await db.commit()
    missing_id = missing.id
    try:
        response = await client.get("/api/v1/me/card/share-link", headers=auth(missing))
        assert response.status_code == 404
        assert response.json()["code"] == "CARD_NOT_FOUND"
        assert (
            await client.get("/api/v1/me/card/share-link", headers=auth(colleague))
        ).status_code == 200
    finally:
        await db.execute(delete(Employee).where(Employee.id == missing_id))
        await db.commit()


@pytest.mark.parametrize(
    "query", ["s=other", "s=https://evil.test", "e=0", "e=-1", "e=1.5", "e=text"]
)
async def test_来源与活动参数错误返回422(client, employees, query):
    _, employee, _ = employees
    response = await client.get("/api/v1/me/card/share-link?" + query, headers=auth(employee))
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


async def test_未登录无效令牌和访客令牌不能取员工分享链接(client):
    for headers in [
        {},
        {"Authorization": "Bearer invalid"},
        {"Authorization": "Bearer " + issue_token("synthetic", "visitor")},
    ]:
        response = await client.get("/api/v1/me/card/share-link?s=nfc", headers=headers)
        assert response.status_code == 401


async def test_停用名片拒绝新分享且公开短链仍进入停用页(client, db, employees):
    _, employee, _ = employees
    card = await shared.own_card(db, employee.id)
    card.status = "disabled"
    await db.commit()
    response = await client.get("/api/v1/me/card/share-link?s=nfc", headers=auth(employee))
    assert response.status_code == 409 and response.json()["code"] == "CARD_DISABLED"
    redirect = await client.get(f"/c/{card.code}?s=nfc")
    assert redirect.status_code == 302
    assert redirect.headers["cache-control"] == "no-store"
    assert redirect.headers["location"] == f"/card/{card.code}?s=nfc"
    public = await client.get(f"/api/v1/public/cards/{card.code}")
    assert public.status_code == 200 and public.json()["status"] == "disabled"
    assert "mobile" not in public.json()
    employee.status = "disabled"
    await db.commit()
    response = await client.get("/api/v1/me/card/share-link?s=nfc", headers=auth(employee))
    assert response.status_code == 401 and response.json()["code"] == "AUTH_DISABLED"


@pytest.mark.parametrize("state", ["active", "draft", "ended", "expired", "future"])
async def test_轻量分享和旧分享及短链使用相同活动有效期(client, db, employees, state):
    _, employee, _ = employees
    now = utcnow()
    event = Campaign(
        name="合成NFC活动",
        status=state if state in ("draft", "ended") else "active",
        start_at=now + timedelta(hours=1) if state == "future" else now - timedelta(hours=2),
        end_at=now - timedelta(hours=1) if state == "expired" else now + timedelta(hours=2),
    )
    db.add(event)
    await db.commit()
    event_id = event.id
    card = await shared.own_card(db, employee.id)
    try:
        response = await client.get(
            f"/api/v1/me/card/share-link?s=nfc&e={event_id}", headers=auth(employee)
        )
        redirect = await client.get(f"/c/{card.code}?s=nfc&e={event_id}")
        if state == "active":
            assert response.status_code == 200
            assert response.json()["campaign_id"] == event_id
            assert response.json()["short_url"].endswith(f"?s=nfc&e={event_id}")
            assert redirect.status_code == 302
            assert redirect.headers["location"].endswith(f"?s=nfc&e={event_id}")
            assert redirect.headers["cache-control"] == "no-store"
        else:
            legacy = await client.get(
                f"/api/v1/me/card/share?s=nfc&e={event_id}", headers=auth(employee)
            )
            assert response.status_code == redirect.status_code == legacy.status_code == 404
            assert (
                response.json()["code"]
                == redirect.json()["code"]
                == legacy.json()["code"]
                == "NOT_FOUND"
            )
    finally:
        await db.execute(delete(Campaign).where(Campaign.id == event_id))
        await db.commit()
    missing = await client.get(
        f"/api/v1/me/card/share-link?s=nfc&e={event_id}", headers=auth(employee)
    )
    assert missing.status_code == 404 and missing.json()["code"] == "NOT_FOUND"


@pytest.mark.parametrize("prefix", ["", "/aicardhub"])
async def test_真实短链保持部署前缀且不接受开放跳转(client, db, employees, prefix):
    _, employee, _ = employees
    card = await shared.own_card(db, employee.id)
    app = client._transport.app
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, root_path=prefix), base_url="http://test"
    ) as scoped:
        response = await scoped.get(
            f"/c/{card.code}?s=nfc&redirect=https://evil.test&url=//evil.test"
        )
        assert response.status_code == 302
        assert response.headers["location"] == f"{prefix}/card/{card.code}?s=nfc"
        assert response.headers["cache-control"] == "no-store"
        missing = await scoped.get("/c/nonexistent-nfc-synthetic?s=nfc")
        assert missing.status_code == 404 and missing.json()["code"] == "CARD_NOT_FOUND"


@pytest.mark.parametrize("prefix", ["", "/aicardhub"])
@pytest.mark.parametrize("state", ["draft", "ended", "expired", "future", "missing"])
async def test_浏览器失效活动显示安全普通名片恢复且保留来源(client, db, employees, prefix, state):
    _, employee, _ = employees
    card = await shared.own_card(db, employee.id)
    now = utcnow()
    event = Campaign(
        name="合成NFC恢复活动",
        status=state if state in ("draft", "ended") else "active",
        start_at=now + timedelta(hours=1) if state == "future" else now - timedelta(hours=2),
        end_at=now - timedelta(hours=1) if state == "expired" else now + timedelta(hours=2),
    )
    db.add(event)
    await db.commit()
    event_id = event.id
    if state == "missing":
        await db.execute(delete(Campaign).where(Campaign.id == event_id))
        await db.commit()
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=client._transport.app, root_path=prefix),
            base_url="http://test",
        ) as browser:
            response = await browser.get(
                f"/c/{card.code}?s=nfc&e={event_id}&redirect=https://evil.test",
                headers={"Accept": "text/html,application/xhtml+xml,*/*;q=0.8"},
            )
            assert response.status_code == 404
            assert response.headers["content-type"].startswith("text/html")
            assert response.headers["cache-control"] == "no-store"
            assert response.headers["vary"] == "Accept"
            assert "活动链接已失效" in response.text and "打开普通名片" in response.text
            target = f"{prefix}/card/{card.code}?s=nfc"
            assert f'href="{target}"' in response.text
            assert "evil.test" not in response.text and "&e=" not in response.text
            # The H5 route is outside this ASGI app; validate the same plain card via public API.
            public = await browser.get(f"/api/v1/public/cards/{card.code}")
            assert public.status_code == 200 and public.json()["status"] == "active"
            for accept in [None, "application/json", "*/*", "text/html;q=0"]:
                api = await browser.get(
                    f"/c/{card.code}?s=nfc&e={event_id}",
                    headers={"Accept": accept} if accept is not None else {},
                )
                assert api.status_code == 404 and api.json()["code"] == "NOT_FOUND"
            unknown = await browser.get(
                f"/c/unknown-nfc-recovery?s=nfc&e={event_id}", headers={"Accept": "text/html"}
            )
            assert unknown.status_code == 404 and unknown.json()["code"] == "CARD_NOT_FOUND"
            assert "打开普通名片" not in unknown.text
    finally:
        await db.execute(delete(Campaign).where(Campaign.id == event_id))
        await db.commit()


async def test_浏览器无活动二维码仍正常跳转且保持来源(client, db, employees):
    _, employee, _ = employees
    card = await shared.own_card(db, employee.id)
    response = await client.get(f"/c/{card.code}?s=qr", headers={"Accept": "text/html"})
    assert response.status_code == 302
    assert response.headers["location"] == f"/card/{card.code}?s=qr"
    assert response.headers["cache-control"] == "no-store"
