"""Authorization and progressive disclosure independent of provider semantics."""

import json

import pytest

from app.kb.store import KnowledgeStore
from app.kb.tools import ToolRuntime


@pytest.fixture
def store(tmp_path):
    result = KnowledgeStore(tmp_path / "kb")
    for file_id, flags in [
        ("approved", {"public": True, "approved": True}),
        ("draft", {"public": True, "approved": False}),
        ("private", {"public": False, "approved": True}),
        ("other", {"public": True, "approved": True, "scope": "card", "card_code": "other"}),
    ]:
        result.upsert(
            file_id, file_id, "BODY_SENTINEL_" + file_id, description="目录说明_" + file_id, **flags
        )
    return result


async def test_目录只含批准元数据且说明参与模型选择(store):
    runtime = ToolRuntime(store, "current")
    output = await runtime.invoke("list_public_knowledge", "{}")
    encoded = json.dumps(output, ensure_ascii=False)
    assert output["ok"] is True
    assert "目录说明_approved" in encoded
    assert "BODY_SENTINEL" not in encoded
    assert "目录说明_draft" not in encoded and "目录说明_private" not in encoded
    assert "目录说明_other" not in encoded
    assert runtime.refs == []


async def test_检索后撤销不允许正文读取(store):
    runtime = ToolRuntime(store, "current")
    found = await runtime.invoke("search_public_knowledge", '{"query":"approved"}')
    assert found["ok"] is True
    store.upsert("approved", "approved", "REVOKED_SECRET", public=True, approved=False)
    denied = await runtime.invoke("read_public_knowledge", '{"file_id":"approved"}')
    assert denied["ok"] is False and "REVOKED_SECRET" not in json.dumps(denied)


@pytest.mark.parametrize(
    ("name", "arguments"),
    [
        ("shell", '{"command":"whoami"}'),
        ("get_public_card", '{"card_code":"other"}'),
        ("read_public_knowledge", '{"file_id":"../secret"}'),
        ("read_public_knowledge", '{"file_id":"other"}'),
        ("read_public_knowledge", '{"file_id":"private"}'),
        ("read_public_knowledge", '{"file_id":"draft"}'),
        ("read_public_knowledge", "[]"),
        ("read_public_knowledge", "{"),
        ("search_public_knowledge", json.dumps({"query": "x" * 4097})),
    ],
)
async def test_非法工具路径范围参数不执行不泄露(store, name, arguments):
    runtime = ToolRuntime(store, "current")
    result = await runtime.invoke(name, arguments)
    assert result["ok"] is False
    assert "BODY_SENTINEL" not in json.dumps(result)
    assert runtime.refs == []


async def test_审计仅记录安全工具统计不含参数内容(store, caplog):
    runtime = ToolRuntime(store, "current")
    with caplog.at_level("INFO"):
        await runtime.invoke("search_public_knowledge", '{"query":"PRIVATE_PHONE_SENTINEL"}')
        await runtime.invoke("SECRET_UNKNOWN_TOOL", "{}")
    assert "search_public_knowledge" in caplog.text
    assert "PRIVATE_PHONE_SENTINEL" not in caplog.text
    assert "SECRET_UNKNOWN_TOOL" not in caplog.text


async def test_员工预览只可读自己草稿且不更改批准状态(store):
    store.upsert("own-draft", "草稿", "OWN_DRAFT", scope="card", card_code="current")
    preview = ToolRuntime(store, "current", preview=True)
    public = ToolRuntime(store, "current")
    allowed = await preview.invoke("read_public_knowledge", '{"file_id":"own-draft"}')
    assert allowed["ok"] and allowed["documents"][0]["preview"]
    assert not (await public.invoke("read_public_knowledge", '{"file_id":"own-draft"}'))["ok"]
    assert not (await preview.invoke("read_public_knowledge", '{"file_id":"other"}'))["ok"]
    assert not store.get("own-draft")["approved"]


async def test_取消后的只读线程结果不得补写引用(store, monkeypatch):
    import asyncio
    import threading

    runtime = ToolRuntime(store, "current")
    started, release = threading.Event(), threading.Event()
    original = runtime._documents

    def slow(name, value):
        started.set()
        release.wait(3)
        return original(name, value)

    monkeypatch.setattr(runtime, "_documents", slow)
    task = asyncio.create_task(runtime.invoke("read_public_knowledge", '{"file_id":"approved"}'))
    await asyncio.to_thread(started.wait, 3)
    task.cancel()
    try:
        with pytest.raises(asyncio.CancelledError):
            await task
    finally:
        release.set()
    await asyncio.sleep(0.05)
    assert runtime.refs == [] and runtime.count == 1
