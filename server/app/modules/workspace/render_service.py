"""Derived card documents; generated through KnowledgeStore and private by default."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.modules.workspace import repo
from app.modules.workspace import service as shared
from app.modules.workspace.models import Assistant, Card, Employee, Template


async def documents(db: AsyncSession, card: Card) -> dict[str, str]:
    employee = await repo.one(db, Employee, Employee.id == card.employee_id)
    company = await shared.employee_company(db, employee)
    assistant = await shared.assistant_get(db, card)
    template = (
        await repo.optional(db, Template, Template.id == assistant.template_id)
        if assistant.template_id
        else None
    )
    persona = shared.render(template.persona, employee, company) if template else ""
    profile = "\n".join(
        [
            f"姓名：{employee.name}",
            f"部门：{employee.dept}",
            f"职位：{card.display_title or employee.title}",
            f"公司：{company.name}",
            f"公司介绍：{company.intro}",
            f"负责业务：{employee.business_scope}",
            f"个人简介：{card.intro}",
        ]
    )
    return {"persona": persona + "\n" + assistant.persona_extra, "profile": profile}


async def render_card(db: AsyncSession, card: Card) -> None:
    from app.modules.workspace.knowledge_service import get_store

    store = await get_store()
    values = await documents(db, card)
    for kind, content in values.items():
        file_id = f"{kind}-{card.code}"
        existing = await run_in_threadpool(store.get, file_id)
        if existing and existing["content"] == content:
            continue
        await run_in_threadpool(
            store.upsert,
            file_id,
            "助手人设" if kind == "persona" else "名片资料",
            content,
            scope="card",
            card_code=card.code,
            public=False,
            approved=False,
        )


async def render_all(db: AsyncSession, template_id: int | None = None) -> None:
    """Enqueue derived files in the same transaction as their source change."""
    from uuid import uuid4

    from app.modules.workspace.models import Setting

    stmt = (
        select(Card)
        .join(Employee, Employee.id == Card.employee_id)
        .where(Card.status == "active", Employee.status == "active")
    )
    if template_id is not None:
        stmt = stmt.join(Assistant, Assistant.card_id == Card.id).where(
            Assistant.template_id == template_id
        )
    for card in (await db.scalars(stmt)).all():
        key = f"render_pending-{card.code}"
        row = await repo.optional(db, Setting, Setting.key == key)
        value = {"card_id": card.id, "version": uuid4().hex}
        if row is None:
            db.add(Setting(key=key, value=value))
        else:
            row.value = value


async def template_previews(db: AsyncSession, employee_id: int) -> list[Any]:
    from app.modules.workspace import schemas as s

    employee = await repo.one(db, Employee, Employee.id == employee_id)
    company = await shared.employee_company(db, employee)
    results = []
    for row in await repo.many(db, Template, Template.enabled.is_(True)):
        result = s.TemplateData.model_validate(row)
        result.persona = shared.render(row.persona, employee, company)
        result.opening = shared.render(row.opening, employee, company)
        result.guide_questions = [shared.render(q, employee, company) for q in row.guide_questions]
        results.append(result)
    return results


async def chat_context(
    db: AsyncSession, card: Card, question: str, *, is_test: bool
) -> list[dict[str, Any]]:
    from app.modules.workspace.knowledge_service import get_store

    store = await get_store()
    if not is_test:
        return [
            row
            for row in await run_in_threadpool(store.search, question, card_code=card.code, limit=8)
            if not str(row["file_id"]).startswith(("profile-", "persona-"))
        ][:4]
    # This identity has already passed own-card session_access. Copies are authorized only
    # for this staff preview; the stored public/approved flags remain unchanged.
    rows = await run_in_threadpool(store.list_files, scope="card", card_code=card.code)
    generated = await documents(db, card)
    selected = [
        {**row, "public": True, "approved": True}
        for row in rows
        if str(row["file_id"]).startswith("corrections-")
    ]
    selected.extend(
        {**row, "public": True, "approved": True}
        for row in sorted(
            rows,
            key=lambda row: (
                -(
                    sum(word in row["content"] for word in question.split())
                    + int(question in row["content"])
                )
            ),
        )
        if not str(row["file_id"]).startswith(("profile-", "persona-", "corrections-"))
    )
    if generated["profile"].strip():
        selected.append(
            {
                "file_id": f"profile-{card.code}",
                "title": "profile",
                "content": generated["profile"],
                "scope": "card",
                "public": True,
                "approved": True,
            }
        )
    selected.extend(await run_in_threadpool(store.search, question, card_code=card.code, limit=4))
    return selected[:4]
