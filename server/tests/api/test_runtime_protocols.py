"""Offline regression for controlled multi-protocol runtime configuration."""

import asyncio
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import delete, select

from app.core.config import get_settings
from app.core.errors import AppError
from app.integrations.llm.client import FakeLLMClient
from app.jobs.tasks import summarize
from app.modules.workspace import runtime_settings as runtime
from app.modules.workspace.models import Setting

pytest_plugins = ["test_backend_isolation"]


@pytest_asyncio.fixture
async def isolated_settings(db, monkeypatch):
    monkeypatch.setattr(get_settings(), "llm_mode", "fake")
    existing = {row.key: row.value for row in (await db.scalars(select(Setting))).all()}
    keys = list(runtime.RuntimeSettings.model_fields)
    await db.execute(delete(Setting).where(Setting.key.in_(keys)))
    await db.commit()
    yield
    await db.execute(delete(Setting).where(Setting.key.in_(keys)))
    db.add_all([Setting(key=key, value=value) for key, value in existing.items() if key in keys])
    await db.commit()


def configured(**changes):
    values = dict(
        llm_mode="openai",
        llm_api_mode="responses",
        llm_base_url="https://primary.invalid/v1",
        llm_model="synthetic-primary",
        llm_api_key="synthetic-key",
        llm_timeout=120.0,
        llm_fallback_enabled=True,
        llm_fallback_api_mode="responses",
        llm_fallback_base_url="https://secondary.invalid/v1",
        llm_fallback_model="synthetic-secondary",
        llm_fallback_api_key="synthetic-key-2",
        llm_tertiary_enabled=True,
        llm_tertiary_api_mode="chat_completions",
        llm_tertiary_base_url="https://tertiary.invalid/v1",
        llm_tertiary_model="synthetic-tertiary",
        llm_tertiary_api_key="synthetic-key-3",
    )
    values.update(changes)
    return runtime.validate(values)


def test_三级协议白名单类型与完整启用校验():
    settings = configured()
    assert runtime.generation_lease_seconds(settings) == 390
    assert runtime.generation_lease_seconds(configured(llm_tertiary_enabled=False)) == 270
    for key, value in [
        ("llm_api_mode", "auto"),
        ("llm_fallback_api_mode", "completions"),
        ("llm_tertiary_api_mode", "anything"),
        ("llm_tertiary_enabled", 1),
        ("llm_tertiary_api_key", ""),
        ("llm_tertiary_base_url", "javascript:evil"),
    ]:
        with pytest.raises(AppError):
            configured(**{key: value})
    with pytest.raises(AppError):
        runtime.require_key("arbitrary_secret")


def test_构造主备兜底严格顺序协议和共享超时(monkeypatch):
    built = []

    def build(settings):
        data = settings if isinstance(settings, dict) else settings.model_dump()
        built.append(data)
        return FakeLLMClient()

    monkeypatch.setattr(runtime, "build_client", build)
    primary, fallbacks = runtime.clients(configured())
    assert isinstance(primary, FakeLLMClient) and len(fallbacks) == 2
    assert [row["llm_model"] for row in built] == [
        "synthetic-primary",
        "synthetic-secondary",
        "synthetic-tertiary",
    ]
    assert [row["llm_api_mode"] for row in built] == ["responses", "responses", "chat_completions"]
    assert all(row["llm_timeout"] == 120 for row in built)
    built.clear()
    _, fallbacks = runtime.clients(configured(llm_mode="fake"))
    assert len(built) == 1 and fallbacks == []


async def test_兜底密钥加密掩码保留显式清空且读取支持env回退(
    db, employees, isolated_settings, monkeypatch
):
    actor = employees[0]
    key = "synthetic-" + uuid4().hex
    monkeypatch.setattr(get_settings(), "llm_tertiary_model", "synthetic-env-tertiary")
    assert (await runtime.load(db)).llm_tertiary_model == "synthetic-env-tertiary"
    assert await runtime.save(db, actor, "llm_tertiary_api_key", key) == runtime.MASK
    stored = await db.scalar(select(Setting.value).where(Setting.key == "llm_tertiary_api_key"))
    assert key not in str(stored)
    for value in [runtime.MASK, ""]:
        await runtime.save(db, actor, "llm_tertiary_api_key", value)
        assert (await runtime.load(db)).llm_tertiary_api_key == key
    assert await runtime.save(db, actor, "llm_tertiary_api_key", None, clear_secret=True) == ""
    assert (await runtime.load(db)).llm_tertiary_api_key == ""
    for key in ["llm_api_mode", "llm_fallback_api_mode", "llm_tertiary_api_mode"]:
        assert await runtime.save(db, actor, key, "responses") == "responses"
    for key in ["llm_api_key", "llm_fallback_api_key", "llm_tertiary_api_key"]:
        await runtime.save(db, actor, key, "synthetic-test-key")
        assert await runtime.get_value(db, key) == runtime.MASK


async def test_摘要首内容前依序降级三级且不重放部分输出():
    primary = FakeLLMClient(fail_after=0)
    secondary = FakeLLMClient(fail_after=0)
    tertiary = FakeLLMClient(reply='{"summary":"合成三级摘要","intent_level":"B","tags":[]}')
    result = await summarize(primary, [], [secondary, tertiary])
    assert result.intent_level == "B"
    assert [len(client.calls) for client in [primary, secondary, tertiary]] == [1, 1, 1]
    partial = FakeLLMClient(chunks=["部分输出"], fail_after=1)
    untouched = FakeLLMClient(reply="{}")
    result = await summarize(partial, [], [untouched])
    assert result.intent_level == "C" and untouched.calls == []


async def test_摘要取消向上游传播不降级():
    primary = FakeLLMClient(delay=10)
    secondary = FakeLLMClient()
    task = asyncio.create_task(summarize(primary, [], [secondary]))
    await primary.stream_started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert primary.closed_streams == 1 and secondary.calls == []


async def test_后台知识先排除空派生文件而保留可审批笔记与纠错(db, employees, monkeypatch, tmp_path):
    from starlette.concurrency import run_in_threadpool

    from app.modules.workspace import knowledge_service as kb
    from app.modules.workspace import schemas as s
    from app.modules.workspace import service as shared

    monkeypatch.setattr(get_settings(), "kb_root", str(tmp_path / "kb"))
    actor, employee, _ = employees
    card = await shared.own_card(db, employee.id)
    store = await kb.get_store()
    await run_in_threadpool(
        store.upsert, f"persona-{card.code}", "空人设", "", scope="card", card_code=card.code
    )
    await run_in_threadpool(
        store.upsert,
        f"profile-{card.code}",
        "资料",
        "内部派生内容",
        scope="card",
        card_code=card.code,
    )
    note = await kb.note_save(
        db,
        employee,
        s.NoteInput(title="待批准笔记", content="合成内部笔记"),
        employee_id=employee.id,
    )
    await kb.correction_create(
        db, employee.id, s.CorrectionInput(question="合成问题", correct_answer="纠错内容")
    )
    result = await kb.notes(db, None, 1, 100)
    ids = {row.file_id for row in result.items}
    assert note.file_id in ids and f"corrections-{card.code}" in ids
    assert f"persona-{card.code}" not in ids and f"profile-{card.code}" not in ids
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        s.NoteInput(title="正文必须非空", content="")
