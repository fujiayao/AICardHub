"""Offline model-decided tool regressions; no provider or shared database."""

import json

import pytest

from app.integrations.llm import ChatEngine, FakeLLMClient
from app.integrations.llm.tool_protocol import ToolCall, ToolTurn
from app.kb.tools import ToolRuntime


async def test_模型决定调用名片工具且无伪造引用():
    fake = FakeLLMClient(
        tool_rounds=[ToolTurn([ToolCall("call-1", "get_public_card", "{}")]), "已读取公开名片"]
    )
    runtime = ToolRuntime(
        None, "card-a", public_card={"name": "合成人员", "mobile": "公开手机", "phone": "SECRET"}
    )
    events = [e async for e in ChatEngine(fake).stream("联系方式", [], [], tools=runtime)]
    assert events[-1]["event"] == "done"
    assert events[-1]["data"]["kb_refs"] == []
    assert len(fake.tool_invocations) == 2
    transcript = json.dumps(fake.tool_invocations[-1], ensure_ascii=False)
    assert "公开手机" in transcript and "SECRET" not in transcript
    assert "tool_call_id" in transcript


async def test_普通问题不自动检索或引用():
    fake = FakeLLMClient(tool_rounds=["正常写代码"])
    events = [
        e
        async for e in ChatEngine(fake).stream("写代码", [], [], tools=ToolRuntime(None, "card-a"))
    ]
    assert events[-1]["data"]["kb_refs"] == []
    assert len(fake.tool_invocations) == 1


async def test_循环耗尽不得假成功():
    turn = ToolTurn([ToolCall("call-1", "get_public_card", "{}")])
    fake = FakeLLMClient(tool_rounds=[turn] * 5)
    events = [
        e async for e in ChatEngine(fake).stream("继续", [], [], tools=ToolRuntime(None, "card-a"))
    ]
    assert events[-1]["event"] == "error"
    assert not any(e["event"] == "done" for e in events)


async def test_工具执行后失败不能备用重放():
    primary = FakeLLMClient(
        tool_rounds=[ToolTurn([ToolCall("a", "get_public_card", "{}")]), RuntimeError("fail")]
    )
    backup = FakeLLMClient(reply="不得重放")
    runtime = ToolRuntime(None, "card-a", public_card={"name": "合成"})
    events = [e async for e in ChatEngine(primary, backup).stream("联系", [], [], tools=runtime)]
    assert events[-1]["event"] == "error" and runtime.count == 1
    assert not backup.calls and not backup.tool_invocations


async def test_工具阶段不被纯文本首token超时误切换():
    primary = FakeLLMClient(
        tool_rounds=[ToolTurn([ToolCall("a", "get_public_card", "{}")]), "完成"], delay=0.03
    )
    primary.first_token_timeout = 0.01
    primary.timeout = 1
    events = [
        e
        async for e in ChatEngine(primary).stream(
            "联系", [], [], tools=ToolRuntime(None, "card-a", public_card={"name": "合成"})
        )
    ]
    assert events[-1]["event"] == "done"


@pytest.mark.parametrize("args", ["{}", '{"different":true}'])
async def test_重复工具调用ID不重复执行(args):
    fake = FakeLLMClient(
        tool_rounds=[
            ToolTurn([ToolCall("same", "get_public_card", "{}")]),
            ToolTurn([ToolCall("same", "get_public_card", args)]),
        ]
    )
    runtime = ToolRuntime(None, "card-a", public_card={"name": "合成"})
    events = [e async for e in ChatEngine(fake).stream("联系", [], [], tools=runtime)]
    assert events[-1]["event"] == "error" and runtime.count == 1


async def test_工具总期限取消上游():
    fake = FakeLLMClient(tool_rounds=["不应输出"], delay=1)
    fake.timeout = 0.02
    events = [
        e async for e in ChatEngine(fake).stream("你好", [], [], tools=ToolRuntime(None, "a"))
    ]
    assert events[-1]["event"] == "error" and fake.closed_streams == 1


async def test_长文不截200而超6000明确错误():
    for size, terminal in [(600, "done"), (6001, "error")]:
        fake = FakeLLMClient(reply="文" * size)
        events = [e async for e in ChatEngine(fake).stream("写方案", [], [])]
        assert events[-1]["event"] == terminal
        if terminal == "done":
            assert len("".join(e["data"]["text"] for e in events if e["event"] == "delta")) == size


async def test_NOKB抑制已有工具引用():
    runtime = ToolRuntime(None, "a")
    runtime.refs = ["approved"]
    fake = FakeLLMClient(tool_rounds=["资料不足<<NOKB>>"])
    events = [e async for e in ChatEngine(fake).stream("公司事实", [], [], tools=runtime)]
    assert events[-1]["data"]["nokb"] is True
    assert events[-1]["data"]["kb_refs"] == []
