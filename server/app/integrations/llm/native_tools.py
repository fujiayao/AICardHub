"""Native streaming provider tool turns; no prompt-encoded pseudo tools."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from app.integrations.llm.tool_protocol import ToolCall, ToolTurn


async def chat_turn(
    sdk: Any, model: str, messages: list[dict[str, Any]], definitions: list[dict[str, Any]]
) -> AsyncIterator[str | ToolTurn]:
    response = await sdk.chat.completions.create(
        model=model,
        messages=messages,
        tools=definitions,
        tool_choice="auto",
        stream=True,
        max_tokens=4096,
    )
    calls: dict[int, ToolCall] = {}
    text = ""
    async with response:
        async for chunk in response:
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            if choice.delta.content:
                text += choice.delta.content
                yield choice.delta.content
            for delta in getattr(choice.delta, "tool_calls", None) or []:
                if delta.index not in calls:
                    if len(calls) >= 8:
                        raise RuntimeError("Too many tool calls")
                    calls[delta.index] = ToolCall("", "", "")
                call = calls[delta.index]
                call.call_id += delta.id or ""
                if delta.function:
                    call.name += delta.function.name or ""
                    call.arguments += delta.function.arguments or ""
                if len(call.arguments.encode("utf-8")) > 4096:
                    # Keep parsing terminal frames without retaining unbounded payloads.
                    raise RuntimeError("Tool arguments too large")
                if len(call.call_id) > 200 or len(call.name) > 100:
                    raise RuntimeError("Tool identifier too large")
            reason = choice.finish_reason
            if reason is not None:
                if reason == "tool_calls" and calls:
                    values = list(calls.values())
                    yield ToolTurn(
                        values,
                        [
                            {
                                "role": "assistant",
                                "content": text or None,
                                "tool_calls": [
                                    {
                                        "id": c.call_id,
                                        "type": "function",
                                        "function": {"name": c.name, "arguments": c.arguments},
                                    }
                                    for c in values
                                ],
                            }
                        ],
                    )
                    return
                if reason == "stop" and text and not calls:
                    return
                raise RuntimeError("Native chat unsuccessful completion")
    raise RuntimeError("Native chat missing completion")


async def responses_turn(
    sdk: Any, model: str, messages: list[dict[str, Any]], definitions: list[dict[str, Any]]
) -> AsyncIterator[str | ToolTurn]:
    instructions = "\n\n".join(m["content"] for m in messages if m.get("role") == "system")
    inputs = [m for m in messages if m.get("role") != "system"]
    tools = [{"type": "function", **d["function"]} for d in definitions]
    response = await sdk.responses.create(
        model=model,
        instructions=instructions,
        input=inputs,
        tools=tools,
        tool_choice="auto",
        stream=True,
        store=False,
        max_output_tokens=4096,
    )
    has_text = False
    async with response:
        async for event in response:
            if event.type == "response.output_text.delta" and event.delta:
                has_text = True
                yield event.delta
            elif event.type in {"response.failed", "response.incomplete", "error"}:
                raise RuntimeError("Native Responses reported failure")
            elif event.type == "response.completed":
                if event.response.status != "completed":
                    raise RuntimeError("Native Responses unsuccessful completion")
                if len(event.response.output) > 32:
                    raise RuntimeError("Too many response output items")
                output = [item.model_dump(exclude_none=True) for item in event.response.output]
                if sum(len(str(item)) for item in output) > 64000:
                    raise RuntimeError("Response output too large")
                calls = [
                    ToolCall(item["call_id"], item["name"], item["arguments"])
                    for item in output
                    if item["type"] == "function_call"
                ]
                if calls:
                    yield ToolTurn(calls, output)
                    return
                if has_text:
                    return
                raise RuntimeError("Native Responses empty completion")
    raise RuntimeError("Native Responses missing completion")
