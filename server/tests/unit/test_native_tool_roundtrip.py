"""Protocol-level two-request provider loops, all SDK IO simulated locally."""

from copy import deepcopy
from types import SimpleNamespace as NS

import pytest

from app.integrations.llm import ChatEngine, OpenAILLMClient, ResponsesLLMClient
from app.kb.tools import ToolRuntime


class Stream:
    def __init__(self, events):
        self.events = iter(events)
        self.closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.closed = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.events)
        except StopIteration:
            raise StopAsyncIteration from None


class SDK:
    def __init__(self, rounds):
        self.rounds = iter(rounds)
        self.requests = []
        self.streams = []
        self.chat = NS(completions=self)
        self.responses = self

    async def create(self, **kwargs):
        self.requests.append(deepcopy(kwargs))
        result = Stream(next(self.rounds))
        self.streams.append(result)
        return result

    async def close(self):
        pass


def chat_event(content=None, calls=None, reason=None):
    return NS(choices=[NS(delta=NS(content=content, tool_calls=calls), finish_reason=reason)])


class Item:
    def __init__(self, **fields):
        self.fields = fields

    def model_dump(self, **kwargs):
        return self.fields


@pytest.mark.parametrize("protocol", ["chat", "responses"])
async def test_真实原生工具请求与结果ID闭环而非提示词伪工具(monkeypatch, protocol):
    from app.integrations.llm import client as module

    if protocol == "chat":
        rounds = [
            [
                chat_event(
                    calls=[
                        NS(
                            index=0,
                            id="call-A",
                            function=NS(name="get_public_card", arguments="{}"),
                        )
                    ],
                    reason="tool_calls",
                )
            ],
            [chat_event("公开联系邮箱已返回", reason="stop")],
        ]
        cls = OpenAILLMClient
    else:
        reasoning = Item(type="reasoning", id="rs-A", summary=[])
        call = Item(
            type="function_call",
            id="fc-A",
            call_id="call-A",
            name="get_public_card",
            arguments="{}",
            status="completed",
        )
        rounds = [
            [
                NS(
                    type="response.completed",
                    response=NS(status="completed", output=[reasoning, call]),
                )
            ],
            [
                NS(type="response.output_text.delta", delta="公开联系邮箱已返回"),
                NS(type="response.completed", response=NS(status="completed", output=[])),
            ],
        ]
        cls = ResponsesLLMClient
    sdk = SDK(rounds)
    monkeypatch.setattr(module, "AsyncOpenAI", lambda **kwargs: sdk)
    client = cls("https://synthetic.invalid/v1", "synthetic", "synthetic")
    runtime = ToolRuntime(None, "card-a", public_card={"email": "public@example.invalid"})
    events = [event async for event in ChatEngine(client).stream("怎么联系", [], [], tools=runtime)]
    assert events[-1]["event"] == "done", events
    assert events[-1]["data"]["kb_refs"] == []
    assert len(sdk.requests) == 2 and all(s.closed for s in sdk.streams)
    assert sdk.requests[0]["tool_choice"] == "auto"
    assert sdk.requests[0]["tools"]
    if protocol == "chat":
        messages = sdk.requests[1]["messages"]
        assistant = next(m for m in messages if m.get("tool_calls"))
        result = next(m for m in messages if m.get("role") == "tool")
        assert assistant["tool_calls"][0]["id"] == result["tool_call_id"] == "call-A"
        assert "public@example.invalid" in result["content"]
        assert not any(m.get("type") == "function_call_output" for m in messages)
    else:
        inputs = sdk.requests[1]["input"]
        result = next(m for m in inputs if m.get("type") == "function_call_output")
        assert result["call_id"] == "call-A" and "public@example.invalid" in result["output"]
        assert any(m.get("type") == "reasoning" and m["id"] == "rs-A" for m in inputs)
        assert sdk.requests[1]["store"] is False
