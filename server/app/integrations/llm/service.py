"""Chat policy, bounded context and streaming failover; no DB or HTTP framework.

The caller supplies fresh store.search(question, card_code) results, owns auth,
rate limits, lead persistence and adds message_id when persisting a done event.
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import AsyncIterator, Sequence
from typing import Any

from app.integrations.llm.client import LLMClient, managed_stream
from app.integrations.llm.stream_filter import NOKBFilter
from app.integrations.llm.tool_protocol import ToolLimitError, ToolUnsupportedError, tool_loop
from app.kb.prompt import build_messages
from app.kb.tools import ToolRuntime

logger = logging.getLogger(__name__)
PHONE = re.compile(r"(?<![0-9])(?:\+?86[- ]?)?1[3-9][0-9]{9}(?![0-9])")
UNKNOWN = "这个问题我需要确认一下，目前没有足够的批准公开资料。请联系名片本人确认，我也可以提示您留下联系方式。"


def _event(name: str, **data: Any) -> dict[str, Any]:
    return {"event": name, "data": data}


def _model(client: LLMClient) -> str:
    return str(getattr(client, "model", type(client).__name__))


class ChatEngine:
    def __init__(
        self,
        client: LLMClient,
        fallback: LLMClient | None = None,
        *,
        fallbacks: Sequence[LLMClient] | None = None,
    ):
        if fallback is not None and fallbacks is not None:
            raise ValueError("Use fallback or fallbacks, not both")
        backups = (
            list(fallbacks)
            if fallbacks is not None
            else ([fallback] if fallback is not None else [])
        )
        if len(backups) > 2:
            raise ValueError("At most two fallback clients are supported")
        self.client, self.fallback = client, fallback
        self.fallbacks = backups

    async def stream(
        self,
        question: str,
        knowledge: list[dict[str, Any]],
        history: list[dict[str, Any]],
        persona: str = "",
        *,
        public_card: dict[str, Any] | None = None,
        tools: ToolRuntime | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        if not isinstance(question, str) or not question.strip() or len(question) > 8000:
            yield _event(
                "error",
                code="INVALID_QUESTION",
                message="请输入有效问题（最多8000字）。",
            )
            return
        phone_found = PHONE.search(question) is not None
        if phone_found:
            yield _event("lead_prompt", reason="phone", title="如需跟进，请确认并提交联系方式")
        selected: list[dict[str, Any]] = []
        messages = await build_messages(
            question, selected, history, persona, public_card=public_card
        )
        clients = [self.client, *self.fallbacks]
        deadline = asyncio.get_running_loop().time() + float(getattr(self.client, "timeout", 30))
        for index, client in enumerate(clients):
            received = False
            marker_filter = NOKBFilter()
            output_chars = 0
            try:
                # First *nonempty provider content*, even a buffered marker, commits
                # this attempt. This is stricter than first customer-visible delta.
                source = (
                    tool_loop(client, messages, tools)
                    if tools is not None
                    else client.stream(messages)
                )
                async with asyncio.timeout_at(deadline), managed_stream(source) as iterator:
                    async with asyncio.timeout(
                        None
                        if tools is not None
                        else float(getattr(client, "first_token_timeout", 15))
                    ):
                        while True:
                            first = await anext(iterator)
                            if first:
                                break
                    received = True
                    text = marker_filter.feed(first)
                    if len(text) > 6000:
                        raise ToolLimitError("Visible output limit")
                    if text:
                        output_chars += len(text)
                        yield _event("delta", text=text)
                    async for chunk in iterator:
                        if not isinstance(chunk, str):
                            raise TypeError("Provider returned non-text content")
                        text = marker_filter.feed(chunk)
                        if output_chars + len(text) > 6000:
                            raise ToolLimitError("Visible output limit")
                        if text:
                            output_chars += len(text)
                            yield _event("delta", text=text)
                marker_filter.finish()
                if output_chars == 0:
                    yield _event("delta", text=UNKNOWN)
                    marker_filter.nokb = True
                yield _event(
                    "done",
                    kb_refs=(
                        list(tools.refs) if tools is not None and not marker_filter.nokb else []
                    ),
                    nokb=marker_filter.nokb,
                    model=_model(client),
                )
                return
            except asyncio.CancelledError:
                raise
            except (ToolLimitError, ToolUnsupportedError):
                yield _event(
                    "error",
                    code="LLM_TOOL_ERROR",
                    message="工具能力不可用或已达本轮限制，请稍后重试。",
                )
                return
            except Exception:  # noqa: BLE001 - provider boundary, safe SSE error, cancellation propagated above
                # Never expose provider error bodies, credentials or request content.
                logger.warning(
                    "LLM attempt failed content_started=%s attempt=%d",
                    received,
                    index + 1,
                )
                if (
                    not received
                    and not (tools and tools.committed)
                    and index + 1 < len(clients)
                    and asyncio.get_running_loop().time() < deadline
                ):
                    continue
                yield _event(
                    "error",
                    code="LLM_STREAM_INTERRUPTED" if received else "LLM_UNAVAILABLE",
                    message="回答中断，请联系名片本人。"
                    if received
                    else "暂时无法回答，请稍后重试或联系名片本人。",
                )
                return
