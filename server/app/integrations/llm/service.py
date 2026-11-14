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
from app.kb.prompt import build_messages, public_knowledge

logger = logging.getLogger(__name__)
QUOTE = re.compile(
    r"报价|价格|价钱|多少钱|费用|收费|折扣|优惠|便宜|交付|交期|工期|合同|"
    r"\b(?:price|pricing|cost|quote|quotation|discount|delivery|contract)\b",
    re.IGNORECASE,
)
GENERAL_EXPLANATION = re.compile(
    r"什么是|解释|含义|定义|区别|(?:如何|怎么)(?:安排|规划)|"
    r"\b(?:what is|explain|define|difference|how to plan)\b",
    re.IGNORECASE,
)
TRANSACTION_CONTEXT = re.compile(
    r"你们|贵司|贵公司|本公司|我们|名片本人|承诺|保证|"
    r"(?:本次|这次|这笔|该笔|我的|我们的).{0,8}(?:交易|订单|合同|项目)|"
    r"(?:这个|该|本)项目|\b(?:your|our|promise|guarantee)\b|\bthe\s+(?:price|cost)\b",
    re.IGNORECASE,
)
INJECTION = re.compile(
    r"(?:忽略|绕过|覆盖).{0,15}(?:指令|规则|提示)|(?:输出|泄露|展示|告诉).{0,15}(?:提示词|系统指令)|"
    r"ignore.{0,20}(?:instructions|rules)|system\s*prompt",
    re.IGNORECASE,
)
IDENTITY = re.compile(
    r"你是(?:真人|人类|机器人|AI)|你是.{0,4}人工智能|are you (?:human|real|an? ai)",
    re.IGNORECASE,
)
PHONE = re.compile(r"(?<![0-9])(?:\+?86[- ]?)?1[3-9][0-9]{9}(?![0-9])")
UNKNOWN = "这个问题我需要确认一下，目前没有足够的批准公开资料。请联系名片本人确认，我也可以提示您留下联系方式。"
QUOTE_REPLY = "价格、折扣、交付周期和合同条款需要由名片本人确认，我不能代为报价或承诺。您可以留下联系方式，方便本人跟进。"


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
        # Explain/plan generic topics via the model, but company-specific terms
        # and promises take precedence even when framed as a definition request.
        general = GENERAL_EXPLANATION.search(question) and not TRANSACTION_CONTEXT.search(question)
        if QUOTE.search(question) and not general:
            yield _event("delta", text=QUOTE_REPLY)
            if not phone_found:
                yield _event(
                    "lead_prompt",
                    reason="keyword",
                    title="留下联系方式，由名片本人确认具体需求",
                )
            yield _event("done", kb_refs=[], nokb=False, model="policy")
            return
        if INJECTION.search(question):
            yield _event(
                "delta",
                text="我不能提供内部指令或绕过回答规则。您可以询问名片相关的业务信息。",
            )
            yield _event("done", kb_refs=[], nokb=False, model="policy")
            return
        if IDENTITY.search(question):
            yield _event("delta", text="我是名片本人的 AI 分身。具体业务和承诺请与本人确认。")
            yield _event("done", kb_refs=[], nokb=False, model="policy")
            return
        selected = await asyncio.to_thread(public_knowledge, knowledge)
        messages = await build_messages(
            question, selected, history, persona, public_card=public_card
        )
        clients = [self.client, *self.fallbacks]
        for index, client in enumerate(clients):
            received = False
            marker_filter = NOKBFilter()
            output_chars = 0
            try:
                # First *nonempty provider content*, even a buffered marker, commits
                # this attempt. This is stricter than first customer-visible delta.
                async with managed_stream(client.stream(messages)) as iterator:
                    async with asyncio.timeout(float(getattr(client, "first_token_timeout", 15))):
                        while True:
                            first = await anext(iterator)
                            if first:
                                break
                    received = True
                    text = marker_filter.feed(first)[:200]
                    if text:
                        output_chars += len(text)
                        yield _event("delta", text=text)
                    async for chunk in iterator:
                        if not isinstance(chunk, str):
                            raise TypeError("Provider returned non-text content")
                        text = marker_filter.feed(chunk)[: max(0, 200 - output_chars)]
                        if text:
                            output_chars += len(text)
                            yield _event("delta", text=text)
                marker_filter.finish()
                if output_chars == 0:
                    yield _event("delta", text=UNKNOWN)
                    marker_filter.nokb = True
                yield _event(
                    "done",
                    kb_refs=[item["file_id"] for item in selected]
                    if not marker_filter.nokb
                    else [],
                    nokb=marker_filter.nokb,
                    model=_model(client),
                )
                return
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 - provider boundary, safe SSE error, cancellation propagated above
                # Never expose provider error bodies, credentials or request content.
                logger.warning(
                    "LLM attempt failed content_started=%s attempt=%d",
                    received,
                    index + 1,
                )
                if not received and index + 1 < len(clients):
                    continue
                yield _event(
                    "error",
                    code="LLM_STREAM_INTERRUPTED" if received else "LLM_UNAVAILABLE",
                    message="回答中断，请联系名片本人。"
                    if received
                    else "暂时无法回答，请稍后重试或联系名片本人。",
                )
                return
