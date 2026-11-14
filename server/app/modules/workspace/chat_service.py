import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import timedelta
from time import monotonic
from typing import Any, cast
from uuid import uuid4

from loguru import logger
from sqlalchemy import CursorResult, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SessionLocal, utcnow
from app.core.errors import AppError, ErrorCode
from app.core.ratelimit import hit
from app.modules.chat.stream_filter import MarkerFilter
from app.modules.workspace import repo
from app.modules.workspace import schemas as s
from app.modules.workspace import service as shared
from app.modules.workspace.models import (
    Card,
    ChatSession,
    Issue,
    Message,
    Setting,
)


async def session_create(
    db: AsyncSession, card: Card, visitor_id: int | None, employee_id: int | None = None
) -> s.SessionResult:
    assistant = await shared.assistant_get(db, card)
    row = ChatSession(
        card_id=card.id,
        visitor_id=visitor_id,
        employee_id=employee_id,
        is_test=employee_id is not None,
    )
    db.add(row)
    await db.commit()
    return s.SessionResult(
        session_id=row.id, opening=assistant.opening, guide_questions=assistant.guide_questions
    )


async def session_access(
    db: AsyncSession,
    session_id: int,
    visitor_id: int | None = None,
    employee_id: int | None = None,
    *,
    lock: bool = False,
) -> ChatSession:
    where = [ChatSession.id == session_id]
    if employee_id is not None:
        card = await shared.own_card(db, employee_id)
        where.extend(
            [
                ChatSession.employee_id == employee_id,
                ChatSession.card_id == card.id,
                ChatSession.is_test.is_(True),
            ]
        )
    else:
        where.extend([ChatSession.visitor_id == visitor_id, ChatSession.is_test.is_(False)])
    return await repo.one(db, ChatSession, *where, lock=lock)


async def messages(
    db: AsyncSession, session_id: int, visitor_id: int, page: int, page_size: int
) -> s.Page[s.MessageData]:
    await session_access(db, session_id, visitor_id)
    return s.Page[s.MessageData](
        **await repo.page(
            db,
            select(Message).where(Message.session_id == session_id).order_by(Message.id),
            page,
            page_size,
        )
    )


def frame(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream(
    session_id: int,
    question: str,
    disconnected: Callable[[], Awaitable[bool]],
    visitor_id: int | None = None,
    employee_id: int | None = None,
) -> AsyncIterator[str]:
    from app.integrations.llm.service import ChatEngine
    from app.modules.workspace.render_service import chat_context
    from app.modules.workspace.runtime_settings import clients, load

    async with SessionLocal() as db:
        row = await session_access(db, session_id, visitor_id, employee_id, lock=True)
        card = await repo.one(db, Card, Card.id == row.card_id)
        await shared.by_code(db, card.code, active=True)
        if row.rounds >= 30:
            yield frame(
                "error", {"code": "RATE_LIMITED", "message": "本会话已达30轮，请直接联系员工"}
            )
            return
        settings = await load(db)
        window = utcnow().date().isoformat()
        if not row.is_test:
            try:
                await hit(db, f"visitor:{visitor_id}", window, settings.visitor_daily_limit)
                await hit(db, f"card:{card.id}", window, settings.card_daily_limit)
                await hit(db, "global", window, settings.global_daily_limit)
            except AppError as exc:
                yield frame("error", {"code": exc.code.value, "message": exc.message})
                return
        if any(word in question for word in settings.sensitive_words):
            yield frame(
                "error", {"code": "VALIDATION_ERROR", "message": "该问题暂无法回答，请直接联系员工"}
            )
            return
        history_rows = (
            await db.scalars(
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.id.desc())
                .limit(12)
            )
        ).all()
        history = [{"role": r.role, "content": r.content} for r in reversed(history_rows)]
        from app.modules.workspace.render_service import documents

        persona = (await documents(db, card))["persona"] if row.is_test else ""
        rules = await repo.optional(db, Setting, Setting.key == "answer_rules")
        if rules:
            persona = str(rules.value) + "\n" + persona
        knowledge = await chat_context(db, card, question, is_test=row.is_test)
        if not row.is_test:
            # Staff-controlled free text can guide voice, but never supply unapproved facts.
            persona = str(rules.value) if rules else ""
        user_message = Message(session_id=session_id, role="user", content=question)
        db.add(user_message)
        row.rounds += 1
        row.last_msg_at = utcnow()
        row.ended_at = None
        await db.commit()
        client, fallback = clients(settings)
        engine = ChatEngine(client, fallback)
        parts: list[str] = []
        done: dict[str, Any] = {}
        filter_ = MarkerFilter()
        started = monotonic()
        interrupted = False
        error_data: dict[str, Any] | None = None
        iterator = engine.stream(question, knowledge, history, persona)
        cancellation: BaseException | None = None
        try:
            async for event in iterator:
                if await disconnected():
                    interrupted = True
                    break
                name, data = event["event"], event["data"]
                if name == "delta":
                    text = filter_.feed(data["text"])
                    if text:
                        parts.append(text)
                        yield frame("delta", {"text": text})
                elif name == "done":
                    done = dict(data)
                elif name == "lead_prompt":
                    if row.lead_prompts < 2:
                        row.lead_prompts += 1
                        yield frame(name, data)
                elif name == "error":
                    error_data = dict(data)
                    break
            tail = filter_.feed("", final=True)
            if tail:
                parts.append(tail)
                if not interrupted:
                    yield frame("delta", {"text": tail})
        except (asyncio.CancelledError, GeneratorExit) as exc:
            interrupted = True
            cancellation = exc
        except Exception as exc:
            logger.error(
                "Chat generation failed session={} type={}", session_id, type(exc).__name__
            )
            error_data = {"code": "LLM_ERROR", "message": "对话暂时不可用，请直接联系员工"}
        finally:

            async def close_upstream() -> bool:
                failed = False
                for resource in (iterator, client, fallback):
                    close = getattr(resource, "aclose", None)
                    if close is not None:
                        try:
                            await close()
                        except asyncio.CancelledError:
                            failed = True
                            logger.warning(
                                "Upstream cleanup cancelled resource={}", type(resource).__name__
                            )
                        except Exception as exc:
                            failed = True
                            logger.warning(
                                "Upstream cleanup failed resource={} type={}",
                                type(resource).__name__,
                                type(exc).__name__,
                            )
                return failed

            close_task = asyncio.create_task(close_upstream())
            try:
                close_failed = await asyncio.shield(close_task)
            except asyncio.CancelledError as exc:
                interrupted = True
                cancellation = cancellation or exc
                close_failed = await close_task
            if close_failed and error_data is None:
                error_data = {
                    "code": "LLM_ERROR",
                    "message": "回答连接关闭异常，已生成内容已保存，请稍后重试",
                }
        response = Message(
            session_id=session_id,
            role="assistant",
            content="".join(parts),
            kb_refs=done.get("kb_refs", []),
            nokb=bool(done.get("nokb", False) or filter_.nokb),
            model=str(done.get("model", settings.llm_mode)),
            latency_ms=int((monotonic() - started) * 1000),
        )
        db.add(response)
        if response.nokb and not row.is_test:
            issue = await repo.optional(
                db,
                Issue,
                Issue.card_id == card.id,
                Issue.question == question,
                Issue.type == "nokb",
            )
            if issue:
                issue.count += 1
            else:
                db.add(Issue(card_id=card.id, question=question, type="nokb"))
        await asyncio.shield(db.commit())
        if cancellation is not None:
            raise cancellation
        if error_data:
            yield frame("error", error_data)
        elif not interrupted:
            yield frame(
                "done",
                {
                    "message_id": response.id,
                    "kb_refs": response.kb_refs,
                    "nokb": response.nokb,
                    "model": response.model,
                },
            )


async def feedback(db: AsyncSession, visitor_id: int, message_id: int) -> s.OK:
    message = await repo.one(db, Message, Message.id == message_id, Message.role == "assistant")
    session = await session_access(db, message.session_id, visitor_id)
    if message.feedback != "down":
        message.feedback = "down"
        db.add(Issue(card_id=session.card_id, question=message.content, type="dislike"))
    await db.commit()
    return s.OK()


async def validate_active(db: AsyncSession, session: ChatSession) -> None:
    card = await repo.one(db, Card, Card.id == session.card_id)
    await shared.by_code(db, card.code, active=True)


async def claim_generation(
    db: AsyncSession, session_id: int, visitor_id: int | None = None, employee_id: int | None = None
) -> str:
    from app.modules.workspace.runtime_settings import load

    row = await session_access(db, session_id, visitor_id, employee_id)
    if row.rounds >= 30:
        raise AppError(ErrorCode.RATE_LIMITED, 429, "本会话已达30轮，请直接联系员工")
    runtime = await load(db)
    lease_seconds = int(runtime.llm_timeout * 2) + 30
    token = str(uuid4())
    claimed = await db.execute(
        update(ChatSession)
        .where(
            ChatSession.id == session_id,
            ChatSession.rounds < 30,
            or_(
                ChatSession.generation_token.is_(None), ChatSession.generation_expires_at < utcnow()
            ),
        )
        .values(
            generation_token=token,
            generation_expires_at=utcnow() + timedelta(seconds=lease_seconds),
        )
    )
    if cast(CursorResult[Any], claimed).rowcount != 1:
        raise AppError(ErrorCode.CONFLICT, 409, "该会话已有回答正在生成，请等待完成")
    await db.commit()
    return token


async def release_generation(session_id: int, token: str) -> None:
    async with SessionLocal() as db:
        await db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id, ChatSession.generation_token == token)
            .values(generation_token=None, generation_expires_at=None)
        )
        await db.commit()


async def safe_stream(
    session_id: int,
    question: str,
    disconnected: Callable[[], Awaitable[bool]],
    visitor_id: int | None = None,
    employee_id: int | None = None,
) -> AsyncIterator[str]:
    token: str | None = None
    iterator = None
    try:
        async with SessionLocal() as db:
            token = await claim_generation(db, session_id, visitor_id, employee_id)
        iterator = stream(session_id, question, disconnected, visitor_id, employee_id)
        async for text in iterator:
            yield text
    except AppError as exc:
        yield frame("error", {"code": exc.code.value, "message": exc.message})
    except Exception as exc:
        logger.error("Streaming boundary failed type={}", type(exc).__name__)
        yield frame("error", {"code": "LLM_ERROR", "message": "知识或模型暂不可用，请直接联系员工"})
    finally:

        async def cleanup() -> None:
            if iterator is not None:
                close = getattr(iterator, "aclose", None)
                if close is not None:
                    try:
                        await close()
                    except asyncio.CancelledError:
                        logger.warning("Cancelled stream cleanup")
                    except Exception as exc:
                        logger.warning("Stream cleanup failed type={}", type(exc).__name__)
            if token is not None:
                try:
                    await release_generation(session_id, token)
                except Exception as exc:
                    logger.warning(
                        "Lease release failed type={}; expiry remains bounded", type(exc).__name__
                    )

        await asyncio.shield(cleanup())
