from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode, register_errors
from app.jobs.tasks import end_sessions
from app.modules.workspace import knowledge_service, runtime_settings
from app.modules.workspace.router import router
from app.modules.workspace.schemas import PolishInput


@pytest.fixture
def card_only_mode(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    with monkeypatch.context() as changes:
        changes.setenv("AICARD_CARD_ONLY", "true")
        get_settings.cache_clear()
        yield
    get_settings.cache_clear()


@pytest.mark.parametrize(
    ("method", "path", "data"),
    [
        ("POST", "/public/chat/sessions", {"card_code": "demo"}),
        ("GET", "/public/chat/sessions/1/messages", None),
        ("POST", "/public/chat/sessions/1/messages", {"content": "测试"}),
        ("POST", "/public/messages/1/feedback", {"feedback": "down"}),
        ("POST", "/me/test-chat/sessions", {}),
        ("POST", "/me/test-chat/sessions/1/messages", {"content": "测试"}),
        ("GET", "/me/assistant", None),
        ("GET", "/me/assistant/metrics", None),
        ("GET", "/me/corrections", None),
        ("POST", "/me/assistant/polish", {"text": "测试", "field": "intro"}),
    ],
)
async def test_纯名片版旧接口不可使用(
    card_only_mode: None, method: str, path: str, data: dict[str, str] | None
) -> None:
    app = FastAPI()
    register_errors(app)
    app.include_router(router)
    async with httpx.AsyncClient(
        base_url="http://local.test", transport=httpx.ASGITransport(app=app)
    ) as client:
        response = await client.request(method, f"/api/v1{path}", json=data)
    assert response.status_code == 404
    assert response.json() == {"code": "NOT_FOUND", "message": "此版本不提供 AI 对话功能"}


async def test_纯名片版不创建模型客户端也不读取旧会话(
    card_only_mode: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = MagicMock(side_effect=AssertionError("must not allocate model client"))
    monkeypatch.setattr(runtime_settings, "build_client", provider)
    db = AsyncMock(spec=AsyncSession)
    assert await end_sessions(db) == 0
    db.scalars.assert_not_called()
    with pytest.raises(AppError) as exc:
        runtime_settings.clients(runtime_settings.RuntimeSettings())
    assert exc.value.code == ErrorCode.NOT_FOUND
    with pytest.raises(AppError) as exc:
        await knowledge_service.polish(PolishInput(text="测试", field="intro"), db)
    assert exc.value.code == ErrorCode.NOT_FOUND
    provider.assert_not_called()
