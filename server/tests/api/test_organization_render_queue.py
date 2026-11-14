"""Organization writes enqueue private rendering without touching the Git-backed store."""

from sqlalchemy import delete, select

from app.modules.workspace import admin_service as admin
from app.modules.workspace import knowledge_service as knowledge
from app.modules.workspace import schemas as s
from app.modules.workspace import service as shared
from app.modules.workspace.models import Assistant, AuditLog, Card, Employee, Setting

pytest_plugins = ["test_backend_isolation"]


async def test_创建与保存只入队单卡且不访问知识Git(db, employees, monkeypatch):
    actor, employee, colleague = employees

    async def fail_if_store_is_opened():
        raise AssertionError("organization save must not open Git-backed knowledge store")

    monkeypatch.setattr(knowledge, "get_store", fail_if_store_is_opened)
    created = await admin.employee_create(db, actor, s.EmployeeInput(name="合成无电话队列名片"))
    created_id = created.id
    created_card = await shared.own_card(db, created_id)
    created_card_id = created_card.id
    existing_card = await shared.own_card(db, employee.id)
    other_card = await shared.own_card(db, colleague.id)
    key = f"render_pending-{existing_card.code}"
    own_pending_key = f"render_pending-{created_card.code}"
    other_key = f"render_pending-{other_card.code}"
    try:
        pending = await db.scalar(select(Setting).where(Setting.key == own_pending_key))
        assert pending is not None and pending.value["card_id"] == created_card.id
        assert created.phone is None and not created.login_enabled
        other_pending = await db.scalar(select(Setting).where(Setting.key == other_key))
        assert other_pending is not None
        other_version = other_pending.value["version"]
        await shared.update_card(db, existing_card, s.CardInput(intro="合成即时名片简介"))
        pending = await db.scalar(select(Setting).where(Setting.key == key))
        assert pending is not None
        previous_version = pending.value["version"]
        assert (await shared.public_card(db, existing_card.code)).intro == "合成即时名片简介"
        await shared.assistant_update(db, existing_card, s.AssistantInput(opening="合成即时开场白"))
        pending = await db.scalar(select(Setting).where(Setting.key == key))
        assert pending is not None and pending.value["version"] != previous_version
        assert (
            await shared.public_card(db, existing_card.code)
        ).assistant.opening == "合成即时开场白"
        await admin.employee_update(db, actor, employee.id, s.EmployeeUpdate(name="合成新姓名"))
        assert (await shared.public_card(db, existing_card.code)).name == "合成新姓名"
        assert other_pending.value["version"] == other_version
        assert len((await db.scalars(select(Setting).where(Setting.key == key))).all()) == 1
    finally:
        await db.commit()
        await db.execute(delete(Setting).where(Setting.key.in_([key, own_pending_key, other_key])))
        await db.execute(delete(AuditLog).where(AuditLog.target == str(created_id)))
        await db.execute(delete(Assistant).where(Assistant.card_id == created_card_id))
        await db.execute(delete(Card).where(Card.id == created_card_id))
        await db.execute(delete(Employee).where(Employee.id == created_id))
        await db.commit()
