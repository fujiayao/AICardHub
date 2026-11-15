"""Small provider-neutral read-only tool protocol and bounded orchestration."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from app.kb.tools import ToolRuntime


@dataclass
class ToolCall:
    call_id: str
    name: str
    arguments: str


@dataclass
class ToolTurn:
    calls: list[ToolCall]
    # Native Responses output items include reasoning and function_call IDs.
    output: list[dict[str, Any]] = field(default_factory=list)


class ToolLimitError(RuntimeError):
    pass


class ToolUnsupportedError(RuntimeError):
    pass


async def tool_loop(
    client: Any, messages: list[dict[str, str]], runtime: ToolRuntime
) -> AsyncIterator[str]:
    method = getattr(client, "stream_tools", None)
    if method is None:
        raise ToolUnsupportedError("Provider does not support native tools")
    transcript: list[dict[str, Any]] = [dict(m) for m in messages]
    count = 0
    seen: set[str] = set()
    for _ in range(4):
        turn: ToolTurn | None = None
        text_seen = False
        iterator = method(transcript, runtime.definitions)
        try:
            async for part in iterator:
                if isinstance(part, str):
                    text_seen |= bool(part)
                    yield part
                elif isinstance(part, ToolTurn) and turn is None:
                    turn = part
                else:
                    raise RuntimeError("Invalid native tool stream")
        finally:
            await iterator.aclose()
        if turn is None:
            if not text_seen:
                raise RuntimeError("Empty tool completion")
            return
        if not turn.calls or any(not c.call_id for c in turn.calls):
            raise RuntimeError("Invalid tool call identifiers")
        for call in turn.calls:
            if (
                not isinstance(call.call_id, str)
                or len(call.call_id) > 200
                or not isinstance(call.name, str)
                or len(call.name) > 100
                or not isinstance(call.arguments, str)
                or len(call.arguments.encode("utf-8")) > 4096
                or call.call_id in seen
            ):
                raise ToolLimitError("Invalid, duplicate or oversized tool call")
            seen.add(call.call_id)
        count += len(turn.calls)
        if count > 8:
            raise ToolLimitError("Tool call budget exhausted")
        if turn.output:
            transcript.extend(turn.output)
        else:
            transcript.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": c.call_id,
                            "type": "function",
                            "function": {"name": c.name, "arguments": c.arguments},
                        }
                        for c in turn.calls
                    ],
                }
            )
        for call in turn.calls:
            result = await runtime.invoke(call.name, call.arguments)
            encoded = json.dumps(result, ensure_ascii=False)
            if turn.output and "type" in turn.output[0]:
                transcript.append(
                    {"type": "function_call_output", "call_id": call.call_id, "output": encoded}
                )
            else:
                transcript.append(
                    {"role": "tool", "tool_call_id": call.call_id, "content": encoded}
                )
    raise ToolLimitError("Tool round budget exhausted")
