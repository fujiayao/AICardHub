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
    ):
        if chunk_size < 1 or delay < 0 or (fail_after is not None and fail_after < 0):
            raise ValueError("Invalid fake streaming configuration")
        self.chunks = (
            list(chunks)
            if chunks is not None
            else [
                reply[index : index + chunk_size]
                for index in range(0, len(reply), chunk_size)
            ]
        )
        self.fail_after, self.error, self.delay = fail_after, error, delay
        self.calls: list[list[dict[str, str]]] = []
        self.closed_streams = 0

    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        self.calls.append([dict(message) for message in messages])
        emitted = 0
        try:
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


class OpenAILLMClient:
    """One OpenAI streaming attempt; ChatEngine owns fallback before first content.

    timeout is the total request deadline, first content also has a 15s deadline.
    Provider settings are constructor arguments, never imported from shared core.
    """

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 30):
        if not base_url or not api_key or not model or timeout <= 0:
            raise ValueError(
                "Complete provider configuration and positive timeout required"
            )
        self.model, self.timeout = model, timeout
        self.first_token_timeout = min(15.0, timeout)
        self._client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=0,
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

    async def _stream_content(
        self, messages: list[dict[str, str]]
    ) -> AsyncIterator[str]:
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=cast(list[ChatCompletionMessageParam], messages),
            stream=True,
        )
        async with response:
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

    async def aclose(self) -> None:
        await self._client.close()


def _setting(settings: object, name: str, default: Any = None) -> Any:
    if isinstance(settings, Mapping):
        value = settings.get(name, default)
    else:
        value = getattr(settings, name, default)
    if hasattr(value, "get_secret_value"):
        return value.get_secret_value()
    return value


def build_client(settings: object) -> LLMClient:
    """Settings keys: llm_mode, llm_base_url, llm_api_key, llm_model, llm_timeout.

    Missing/invalid production configuration raises instead of silently using demo.
    Fallback uses a separately configured client passed to ChatEngine.
    """
    mode = _setting(settings, "llm_mode")
    if mode == "fake":
        return FakeLLMClient()
    if mode != "openai":
        raise ValueError("llm_mode must be fake or openai")
    return OpenAILLMClient(
        base_url=_setting(settings, "llm_base_url", ""),
        api_key=_setting(settings, "llm_api_key", ""),
        model=_setting(settings, "llm_model", ""),
        timeout=float(_setting(settings, "llm_timeout", 30)),
    )
