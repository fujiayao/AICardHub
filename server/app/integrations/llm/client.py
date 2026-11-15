"""OpenAI-compatible streaming with no SDK retries that could duplicate output."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Mapping, Sequence
from contextlib import asynccontextmanager
from typing import Any, Protocol, cast

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from openai.types.responses import ResponseInputParam

logger = logging.getLogger(__name__)
DEMO_MODEL = "本地演示模型"
DEMO_REPLY = "【本地演示模型】这是合成演示答复，仅用于验证对话流程，不代表真实公司业务。请联系名片本人确认具体信息。"


class LLMClient(Protocol):
    def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        """Yield content only; cancellation must propagate and release resources."""
        ...


@asynccontextmanager
async def managed_stream(
    iterator: AsyncIterator[str],
) -> AsyncIterator[AsyncIterator[str]]:
    """Close async generators, while accepting any iterator in the frozen protocol."""
    try:
        yield iterator
    finally:
        close = getattr(iterator, "aclose", None)
        if close is not None:
            await close()


class FakeLLMClient:
    """Deterministic offline client with controllable stream and failure boundaries.

    fail_after counts nonempty chunks yielded; zero fails before first output.
    Custom replies are test fixtures, not assertions about real company facts.
    """

    model = DEMO_MODEL

    def __init__(
        self,
        reply: str = DEMO_REPLY,
        *,
        chunks: Sequence[str] | None = None,
        chunk_size: int = 12,
        fail_after: int | None = None,
        error: Exception | None = None,
        delay: float = 0,
        tool_rounds: Sequence[Any] | None = None,
    ):
        if chunk_size < 1 or delay < 0 or (fail_after is not None and fail_after < 0):
            raise ValueError("Invalid fake streaming configuration")
        self.chunks = (
            list(chunks)
            if chunks is not None
            else [reply[index : index + chunk_size] for index in range(0, len(reply), chunk_size)]
        )
        self.fail_after, self.error, self.delay = fail_after, error, delay
        self.calls: list[list[dict[str, str]]] = []
        self.tool_rounds = list(tool_rounds) if tool_rounds is not None else None
        self.tool_invocations: list[dict[str, Any]] = []
        self.closed_streams = 0
        self.stream_started = asyncio.Event()

    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        self.calls.append([dict(message) for message in messages])
        emitted = 0
        try:
            self.stream_started.set()
            for chunk in self.chunks:
                if self.delay:
                    await asyncio.sleep(self.delay)
                if self.fail_after is not None and emitted >= self.fail_after:
                    raise self.error or ConnectionError("Synthetic provider failure")
                yield chunk
                emitted += bool(chunk)
            if self.fail_after is not None and emitted >= self.fail_after:
                raise self.error or ConnectionError("Synthetic provider failure")
        finally:
            self.closed_streams += 1

    async def stream_tools(
        self, messages: list[dict[str, Any]], definitions: list[dict[str, Any]]
    ) -> AsyncIterator[Any]:
        from copy import deepcopy

        self.tool_invocations.append(
            deepcopy({"messages": messages, "tools": definitions, "tool_choice": "auto"})
        )
        if self.tool_rounds is None:
            async with managed_stream(
                self.stream(cast(list[dict[str, str]], messages))
            ) as iterator:
                async for text in iterator:
                    yield text
            return
        self.stream_started.set()
        try:
            if self.delay:
                await asyncio.sleep(self.delay)
            index = len(self.tool_invocations) - 1
            if index >= len(self.tool_rounds):
                raise RuntimeError("Fake script exhausted")
            part = self.tool_rounds[index]
            if isinstance(part, BaseException):
                raise part
            yield part
        finally:
            self.closed_streams += 1


class OpenAILLMClient:
    """One OpenAI streaming attempt; ChatEngine owns fallback before first content.

    timeout is the total request deadline, first content also has a 15s deadline.
    Chat completion requires text and a stop frame; partial failures propagate.
    Provider settings are constructor arguments, never imported from shared core.
    """

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 30):
        if not base_url or not api_key or not model or timeout <= 0:
            raise ValueError("Complete provider configuration and positive timeout required")
        self.model, self.timeout = model, timeout
        self.first_token_timeout = min(15.0, timeout)
        self._client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=0,
            default_headers={"User-Agent": "AICardHub/0.1"},
        )

    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        started = time.monotonic()
        emitted = False
        try:
            async with asyncio.timeout(self.timeout):
                async with managed_stream(self._stream_content(messages)) as iterator:
                    # Empty/role-only provider frames do not satisfy this deadline.
                    async with asyncio.timeout(self.first_token_timeout):
                        first = await anext(iterator)
                    emitted = True
                    yield first
                    async for text in iterator:
                        yield text
        finally:
            logger.info(
                "LLM stream finished model=%s elapsed_ms=%d content_started=%s",
                self.model,
                int((time.monotonic() - started) * 1000),
                emitted,
            )

    async def _stream_content(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=cast(list[ChatCompletionMessageParam], messages),
            stream=True,
        )
        has_text = False
        async with response:
            async for chunk in response:
                # Usage-only frames have no choices and are not terminal events.
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                if choice.delta.content:
                    has_text = True
                    yield choice.delta.content
                finish_reason = getattr(choice, "finish_reason", None)
                if finish_reason is not None:
                    if finish_reason != "stop":
                        raise RuntimeError("Chat stream reported unsuccessful completion")
                    if not has_text:
                        raise RuntimeError("Chat completion has no valid text")
                    return
        raise RuntimeError("Chat stream ended without completion")

    async def stream_tools(
        self, messages: list[dict[str, Any]], definitions: list[dict[str, Any]]
    ) -> AsyncIterator[Any]:
        from app.integrations.llm.native_tools import chat_turn, responses_turn

        method = responses_turn if isinstance(self, ResponsesLLMClient) else chat_turn
        iterator = method(self._client, self.model, messages, definitions)
        try:
            async for part in iterator:
                yield part
        finally:
            close = getattr(iterator, "aclose", None)
            if close is not None:
                await close()

    async def aclose(self) -> None:
        await self._client.close()


class ResponsesLLMClient(OpenAILLMClient):
    """Native Responses API with the same deadlines and lifecycle as chat.

    Only output_text.delta contributes content; a terminal completed event is
    mandatory. Failed/incomplete/error, empty completion and premature EOF raise
    without exposing provider payloads. No request retries or text replay.
    """

    async def _stream_content(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        instructions: list[str] = []
        inputs: ResponseInputParam = []
        for message in messages:
            role, content = message.get("role"), message.get("content")
            if not isinstance(content, str):
                raise ValueError("Responses messages require text content")
            if role == "system":
                instructions.append(content)
            elif role == "user":
                inputs.append({"role": "user", "content": content, "type": "message"})
            elif role == "assistant":
                inputs.append({"role": "assistant", "content": content, "type": "message"})
            else:
                raise ValueError("Unsupported Responses message role")
        response = await self._client.responses.create(
            model=self.model,
            instructions="\n\n".join(instructions),
            input=inputs,
            stream=True,
            store=False,
            max_output_tokens=1024,
        )
        has_text = False
        async with response:
            async for event in response:
                if event.type == "response.output_text.delta":
                    if event.delta:
                        has_text = True
                        yield event.delta
                elif event.type in {"response.failed", "response.incomplete", "error"}:
                    raise RuntimeError("Responses stream reported failure")
                elif event.type == "response.completed":
                    if event.response.status != "completed" or not has_text:
                        raise RuntimeError("Responses completion has no valid text")
                    return
        raise RuntimeError("Responses stream ended without completion")


def _setting(settings: object, name: str, default: Any = None) -> Any:
    if isinstance(settings, Mapping):
        value = settings.get(name, default)
    else:
        value = getattr(settings, name, default)
    if hasattr(value, "get_secret_value"):
        return value.get_secret_value()
    return value


def build_client(settings: object) -> LLMClient:
    """Settings: llm_mode, llm_api_mode, llm_base_url/api_key/model/timeout.

    Missing/invalid production configuration raises instead of silently using demo.
    Fallback uses a separately configured client passed to ChatEngine.
    """
    mode = _setting(settings, "llm_mode")
    if mode == "fake":
        return FakeLLMClient()
    if mode != "openai":
        raise ValueError("llm_mode must be fake or openai")
    api_mode = _setting(settings, "llm_api_mode", "chat_completions")
    if api_mode not in {"chat_completions", "responses"}:
        raise ValueError("llm_api_mode must be chat_completions or responses")
    client_type = ResponsesLLMClient if api_mode == "responses" else OpenAILLMClient
    return client_type(
        base_url=_setting(settings, "llm_base_url", ""),
        api_key=_setting(settings, "llm_api_key", ""),
        model=_setting(settings, "llm_model", ""),
        timeout=float(_setting(settings, "llm_timeout", 30)),
    )
