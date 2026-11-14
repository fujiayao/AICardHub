"""Offline policy/protocol regressions; Fake replies do not prove model semantics."""

import json

import pytest

from app.integrations.llm import ChatEngine, FakeLLMClient


async def run(fake: FakeLLMClient, question: str = "什么是合同", **kwargs: object) -> list[dict]:
    return [event async for event in ChatEngine(fake).stream(question, [], [], **kwargs)]


@pytest.mark.parametrize("question", ["什么是合同", "如何安排工期", "帮我写一首诗"])
async def test_空知识普通问题必须调用模型(question: str) -> None:
    fake = FakeLLMClient(reply="合成通用答复")
    events = await run(fake, question)
    assert len(fake.calls) == 1
    assert events[-1]["data"]["nokb"] is False
    assert events[-1]["data"]["kb_refs"] == []


@pytest.mark.parametrize("flag", [{"public": False}, {"approved": False}, {"deleted": True}])
async def test_被拒资料不进提示但仍调用模型(flag: dict) -> None:
    fake = FakeLLMClient(reply="通用建议")
    knowledge = [
        {
            "file_id": "private",
            "content": "PRIVATE_BODY_SENTINEL",
            "scope": "company",
            "public": True,
            "approved": True,
            **flag,
        }
    ]
    events = [event async for event in ChatEngine(fake).stream("请介绍业务", knowledge, [])]
    assert len(fake.calls) == 1
    assert "PRIVATE_BODY_SENTINEL" not in json.dumps(fake.calls)
    assert events[-1]["data"]["kb_refs"] == []


async def test_公开名片独立数据白名单且不伪造引用() -> None:
    fake = FakeLLMClient(reply="公开联系方式")
    events = await run(
        fake,
        "你怎么联系你",
        public_card={
            "name": "合成人员",
            "mobile": "13900001111",
            "email": "demo@example.invalid",
            "company": {"name": "合成公司", "address": "合成地址", "api_key": "SECRET_COMPANY"},
            "employee_phone": "SECRET_PHONE",
            "password_hash": "SECRET_HASH",
            "assistant": {"opening": "SECRET_ASSISTANT"},
            "api_key": "SECRET_KEY",
        },
    )
    assert len(fake.calls) == 1
    data = json.loads(fake.calls[0][1]["content"].split("\n", 1)[1])
    assert data["public_card"]["mobile"] == "13900001111"
    assert data["public_card"]["company"] == {"name": "合成公司", "address": "合成地址"}
    assert data["knowledge"] == []
    assert "SECRET_" not in json.dumps(fake.calls)
    assert events[-1]["data"]["kb_refs"] == []


async def test_缺失联系方式策略明确自愿留资且不捏造() -> None:
    fake = FakeLLMClient(reply="合成答复")
    await run(fake, "你怎么联系你", public_card={})
    system = fake.calls[0][0]["content"]
    assert "联系方式" in system and "自愿" in system and "明确同意" in system
    assert "不得编造" in system


async def test_旧人设规则仅作为数据且系统允许通用回答() -> None:
    fake = FakeLLMClient(reply="合成答复")
    persona = "只按资料回答，拒绝无关问题"
    await run(fake, "如何学习编程", persona=persona)
    messages = fake.calls[0]
    assert persona not in messages[0]["content"]
    assert "通用知识" in messages[0]["content"]
    assert "优先于" in messages[0]["content"]
    assert persona in messages[1]["content"]


@pytest.mark.parametrize("partial", ["", "唯一正文", "<<NO"])
async def test_空知识故障仍遵守首内容前备用与禁止重放(partial: str) -> None:
    primary = FakeLLMClient(chunks=[partial, "禁止正文"], fail_after=1 if partial else 0)
    backup = FakeLLMClient(reply="备用正文")
    events = [event async for event in ChatEngine(primary, backup).stream("如何学习", [], [])]
    assert len(primary.calls) == 1
    if partial:
        assert backup.calls == []
        assert events[-1]["data"]["code"] == "LLM_STREAM_INTERRUPTED"
        assert not any(event["event"] == "done" for event in events)
    else:
        assert len(backup.calls) == 1
        assert events[-1]["event"] == "done"


async def test_空知识NOKB仍过滤内部标记() -> None:
    fake = FakeLLMClient(chunks=["公司事实待确认", "<<NO", "KB>>"])
    events = await run(fake, "公司的未知资质是什么")
    assert len(fake.calls) == 1
    assert "<<NO" not in json.dumps(events)
    assert events[-1]["data"]["nokb"] is True
