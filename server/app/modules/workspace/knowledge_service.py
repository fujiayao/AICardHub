from collections.abc import Callable
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.modules.workspace import repo
from app.modules.workspace import schemas as s
from app.modules.workspace import service as shared
from app.modules.workspace.models import Card, Correction, Employee, Issue, KnowledgeFile, Message


def store() -> Any:
    from app.kb.store import KnowledgeStore

    return KnowledgeStore(get_settings().kb_root)


async def get_store() -> Any:
    return await run_in_threadpool(store)


async def notes(
    db: AsyncSession, employee_id: int | None, page: int, page_size: int
) -> s.Page[s.NoteData]:
    card = await shared.own_card(db, employee_id) if employee_id is not None else None
    rows = await run_in_threadpool(
        (await get_store()).list_files,
        scope="card" if card else None,
        card_code=card.code if card else None,
    )
    items = [
        s.NoteData.model_validate(row)
        for row in rows
        if not str(row["file_id"]).startswith(("profile-", "persona-", "corrections-", "rules-"))
    ]
    return s.Page[s.NoteData](
        items=items[(page - 1) * page_size : page * page_size],
        total=len(items),
        page=page,
        page_size=page_size,
    )


async def note_get(db: AsyncSession, employee_id: int | None, file_id: str) -> dict[str, Any]:
    row = await run_in_threadpool((await get_store()).get, file_id)
    if row is None:
        raise AppError(ErrorCode.NOT_FOUND, 404)
    if employee_id is not None:
        card = await shared.own_card(db, employee_id)
        if row.get("scope") != "card" or row.get("card_code") != card.code:
            raise AppError(ErrorCode.NOT_FOUND, 404)
    return dict(row)


async def note_save(
    db: AsyncSession,
    actor: Employee,
    payload: s.NoteInput,
    *,
    employee_id: int | None = None,
    file_id: str | None = None,
) -> s.NoteData:
    card = await shared.own_card(db, employee_id) if employee_id is not None else None
    if file_id:
        old = await note_get(db, employee_id, file_id)
        scope, card_code = old.get("scope", "company"), old.get("card_code")
    else:
        file_id = "note-" + uuid4().hex
        scope, card_code = ("card", card.code) if card else ("company", None)
    # Any employee edit revokes approval until explicitly reviewed again.
    approved = payload.approved if employee_id is None else False
    result = await run_in_threadpool(
        (await get_store()).upsert,
        file_id,
        payload.title,
        payload.content,
        public=payload.public,
        approved=approved,
        scope=scope,
        card_code=card_code,
    )
    index = await repo.optional(db, KnowledgeFile, KnowledgeFile.file_id == file_id)
    if index is None:
        index = KnowledgeFile(file_id=file_id)
        db.add(index)
    repo.assign(
        index,
        dict(
            title=payload.title,
            public=payload.public,
            approved=approved,
            scope=scope,
            card_code=card_code,
            revision=result["revision"],
        ),
    )
    await shared.audit(db, actor.id, "knowledge.save", file_id)
    await db.commit()
    return s.NoteData.model_validate(result)


async def note_delete(
    db: AsyncSession, actor: Employee, employee_id: int | None, file_id: str
) -> s.OK:
    await note_get(db, employee_id, file_id)
    await run_in_threadpool((await get_store()).delete, file_id)
    index = await repo.optional(db, KnowledgeFile, KnowledgeFile.file_id == file_id)
    if index:
        await db.delete(index)
    await shared.audit(db, actor.id, "knowledge.delete", file_id)
    await db.commit()
    return s.OK()


async def note_history(db: AsyncSession, file_id: str) -> list[s.HistoryData]:
    await note_get(db, None, file_id)
    rows = await run_in_threadpool((await get_store()).history, file_id)
    return [s.HistoryData.model_validate(row) for row in rows]


async def note_rollback(
    db: AsyncSession, actor: Employee, file_id: str, revision: int
) -> s.NoteData:
    await note_get(db, None, file_id)
    try:
        result = await run_in_threadpool((await get_store()).rollback, file_id, revision)
    except (ValueError, KeyError) as exc:
        raise AppError(ErrorCode.NOT_FOUND, 404, "历史版本不存在") from exc
    await shared.audit(db, actor.id, "knowledge.rollback", file_id, {"revision": revision})
    await db.commit()
    return s.NoteData.model_validate(result)


async def corrections(
    db: AsyncSession, employee_id: int, page: int, page_size: int
) -> s.Page[s.CorrectionData]:
    card = await shared.own_card(db, employee_id)
    return s.Page[s.CorrectionData](
        **await repo.page(
            db,
            select(Correction).where(Correction.card_id == card.id).order_by(Correction.id.desc()),
            page,
            page_size,
        )
    )


async def sync_corrections(db: AsyncSession, card: Card) -> None:
    rows = await repo.many(db, Correction, Correction.card_id == card.id)
    content = (
        "\n\n".join(f"问题：{r.question}\n正确回答：{r.correct_answer}" for r in rows)
        or "暂无纠错记录。"
    )
    # Staff-generated corrections are private until an administrator approves the revision.
    await run_in_threadpool(
        (await get_store()).upsert,
        f"corrections-{card.code}",
        "个人纠错",
        content,
        public=False,
        approved=False,
        scope="card",
        card_code=card.code,
    )


async def correction_create(
    db: AsyncSession, employee_id: int, payload: s.CorrectionInput
) -> s.CorrectionData:
    card = await shared.own_card(db, employee_id)
    if payload.message_id:
        from app.modules.workspace.models import ChatSession

        message = await repo.one(db, Message, Message.id == payload.message_id)
        await repo.one(
            db, ChatSession, ChatSession.id == message.session_id, ChatSession.card_id == card.id
        )
    row = Correction(card_id=card.id, **payload.model_dump())
    db.add(row)
    await db.flush()
    await sync_corrections(db, card)
    await db.commit()
    return s.CorrectionData.model_validate(row)


async def correction_delete(db: AsyncSession, employee_id: int, correction_id: int) -> s.OK:
    card = await shared.own_card(db, employee_id)
    row = await repo.one(
        db, Correction, Correction.id == correction_id, Correction.card_id == card.id
    )
    await db.delete(row)
    await db.flush()
    await sync_corrections(db, card)
    await db.commit()
    return s.OK()


async def issue_create(db: AsyncSession, employee_id: int, payload: s.IssueInput) -> s.IssueData:
    card = await shared.own_card(db, employee_id)
    row = Issue(card_id=card.id, employee_id=employee_id, question=payload.question)
    db.add(row)
    await db.commit()
    return s.IssueData.model_validate(row)


async def polish(payload: s.PolishInput) -> s.TextData:
    # Preserve factual content: ask the configured model only for expression changes.
    from app.integrations.llm.client import build_client

    client = build_client(get_settings())
    if get_settings().llm_mode == "fake":
        return s.TextData(text=payload.text.strip())
    parts = []
    iterator = client.stream(
        [
            {"role": "system", "content": "只润色表达，禁止新增事实。只返回润色后的原文。"},
            {"role": "user", "content": payload.text},
        ]
    )
    try:
        async for part in iterator:
            parts.append(part)
    finally:
        close_stream = getattr(iterator, "aclose", None)
        if close_stream is not None:
            await close_stream()
        close_client = getattr(client, "aclose", None)
        if close_client is not None:
            await close_client()
    return s.TextData(text="".join(parts))


def extract_document(content: bytes, filename: str) -> str:
    from io import BytesIO

    suffix = filename.lower().rsplit(".", 1)[-1]
    if suffix == "pdf":
        import pymupdf

        opener = cast(Callable[..., Any], pymupdf.open)
        with opener(stream=content, filetype="pdf") as doc:
            return "\n".join(page.get_text() for page in doc)
    if suffix == "docx":
        from docx import api

        factory = cast(Callable[[BytesIO], Any], api.Document)
        return "\n".join(p.text for p in factory(BytesIO(content)).paragraphs)
    if suffix in ("md", "txt"):
        return content.decode("utf-8-sig")
    raise AppError(ErrorCode.VALIDATION_ERROR, 422, "仅支持PDF、Word、Markdown、文本文件")


async def import_document(content: bytes, filename: str) -> s.ImportResult:
    if len(content) > 20 * 1024 * 1024:
        raise AppError(ErrorCode.VALIDATION_ERROR, 413, "文件不可超过20MB")
    try:
        text = await run_in_threadpool(extract_document, content, filename)
    except (ValueError, UnicodeError) as exc:
        raise AppError(ErrorCode.VALIDATION_ERROR, 422, "文件无法解析") from exc
    if not text.strip():
        raise AppError(ErrorCode.VALIDATION_ERROR, 422, "未提取到正文")
    return s.ImportResult(drafts=[s.Draft(title=filename.rsplit(".", 1)[0], content=text[:100000])])


async def rules_get(db: AsyncSession) -> s.RulesData:
    from app.modules.workspace.admin_service import setting_get

    result = await setting_get(db, "answer_rules")
    return s.RulesData(content=str(result.value or ""))


async def rules_update(db: AsyncSession, actor: Employee, payload: s.RulesData) -> s.RulesData:
    from app.modules.workspace.admin_service import setting_update

    await run_in_threadpool(
        (await get_store()).upsert,
        "rules-answer",
        "回答规则",
        payload.content or "仅使用批准公开的资料，不编造事实。",
        public=False,
        approved=False,
    )
    await setting_update(db, actor, "answer_rules", s.SettingInput(value=payload.content))
    return payload
