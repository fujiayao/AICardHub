"""Exercise the real password gate over HTTP without connecting to a database."""

from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI

from app.core import deps
from app.core.db import get_db
from app.core.errors import register_errors


@pytest.fixture
def gate_app(monkeypatch):
    app = FastAPI()
    register_errors(app)
    employee = SimpleNamespace(
        id=7,
        status="active",
        phone="synthetic",
        password_hash="synthetic",
        token_version=3,
        must_change_pwd=True,
        role="staff",
    )

    async def database():
        yield object()

    async def optional(*args):
        return employee

    def decode(token, purpose):
        assert token == "synthetic" and purpose == "staff"
        return {"sub": "7", "version": 3}

    app.dependency_overrides[get_db] = database
    monkeypatch.setattr(deps.repo, "optional", optional)
    monkeypatch.setattr(deps, "decode_token", decode)

    async def protected(staff: deps.StaffDep):
        return {"id": staff.id}

    for path in (
        "/api/v1/me/profile",
        "/api/v1/auth/change-password",
        "/api/v1/me/card",
        "/spoof/api/v1/me/profile",
        "/spoof/api/v1/auth/change-password",
        "/api/v1/me/profile/extra",
        "/api/v1/auth/change-password/extra",
        "/aicardhub-extra/api/v1/me/profile",
    ):
        app.add_api_route(path, protected, methods=["GET", "POST", "PUT", "DELETE"])
    return app, employee


@pytest.mark.parametrize("prefix", ["", "/aicardhub", "/nested/aicardhub"])
@pytest.mark.parametrize(
    ("method", "path", "allowed"),
    [
        ("GET", "/api/v1/me/profile", True),
        ("POST", "/api/v1/auth/change-password", True),
        ("POST", "/api/v1/me/profile", False),
        ("PUT", "/api/v1/me/profile", False),
        ("GET", "/api/v1/auth/change-password", False),
        ("DELETE", "/api/v1/auth/change-password", False),
        ("GET", "/api/v1/me/card", False),
        ("GET", "/spoof/api/v1/me/profile", False),
        ("POST", "/spoof/api/v1/auth/change-password", False),
        ("GET", "/api/v1/me/profile/extra", False),
        ("POST", "/api/v1/auth/change-password/extra", False),
        ("GET", "/aicardhub-extra/api/v1/me/profile", False),
    ],
)
async def test_首次改密精确方法路径且兼容部署前缀(gate_app, prefix, method, path, allowed):
    app, _ = gate_app
    transport = httpx.ASGITransport(app=app, root_path=prefix)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.request(
            method,
            prefix + path,
            headers={"Authorization": "Bearer synthetic"},
        )
    assert response.status_code == (200 if allowed else 403)
    if not allowed:
        assert response.json()["code"] == "PASSWORD_CHANGE_REQUIRED"


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("status", "disabled", "AUTH_DISABLED"),
        ("phone", "", "AUTH_INVALID"),
        ("password_hash", "", "AUTH_INVALID"),
        ("token_version", 4, "AUTH_REQUIRED"),
    ],
)
async def test_允许改密路径仍验证账号和令牌(gate_app, field, value, code):
    app, employee = gate_app
    setattr(employee, field, value)
    transport = httpx.ASGITransport(app=app, root_path="/aicardhub")
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/aicardhub/api/v1/auth/change-password",
            headers={"Authorization": "Bearer synthetic"},
        )
    assert response.status_code == 401
    assert response.json()["code"] == code
