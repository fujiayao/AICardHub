"""General explanations are not promises on behalf of the card owner."""

import pytest

from app.integrations.llm import ChatEngine, FakeLLMClient


@pytest.mark.parametrize(
    "question",
    ["什么是合同条款", "合同和协议有什么区别", "如何安排工期", "什么是合同？简单解释"],
)
async def test_商务术语的通用解释不本地拒答(question):
    fake = FakeLLMClient(reply="合成通用解释")
    events = [event async for event in ChatEngine(fake).stream(question, [], [])]
    assert len(fake.calls) == 1
    assert events[-1]["data"]["model"] == fake.model


@pytest.mark.parametrize(
    "question",
    [
        "你们合同条款是什么",
        "你们价格是多少",
        "可以承诺明天交付吗",
        "解释一下你们合同条款",
        "什么是你们的交付承诺",
        "解释一下贵司合同条款",
        "如何安排这次项目的工期",
        "什么是合同，能保证明天交付吗",
    ],
)
async def test_公司具体交易条款不可作承诺(question):
    fake = FakeLLMClient(reply="公开资料不足，需要确认，不作承诺")
    events = [event async for event in ChatEngine(fake).stream(question, [], [])]
    assert len(fake.calls) == 1
    assert events[-1]["data"]["model"] == fake.model
