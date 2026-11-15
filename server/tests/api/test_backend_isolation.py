from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.db import Base
from app.core.errors import AppError, ErrorCode
from app.core.ratelimit import hit
from app.modules.workspace import admin_service as admin
from app.modules.workspace import chat_service as chat
from app.modules.workspace import me_service as me
from app.modules.workspace import schemas as s
from app.modules.workspace import service as shared
from app.modules.workspace.models import (
    Card,
    Company,
    Employee,
    Lead,
    Message,
    Notification,
    RateCounter,
    Setting,
    Visitor,
)


@pytest_asyncio.fixture
async def db() -> AsyncIterator[AsyncSession]:
    url = get_settings().test_database_url
    assert make_url(url).database == "aicardhub_test", "仅允许专用测试数据库"
    engine = create_async_engine(url, hide_parameters=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def employees(db: AsyncSession) -> AsyncIterator[tuple[Employee, Employee, Employee]]:
    # Existing demo data is never removed; tests have unique identities and explicit cleanup.
    company = await db.scalar(select(Company))
    added_company = company is None
    if company is None:
        company = Company(name="合成测试企业")
        db.add(company)
        await db.flush()
    values = []
    for role in ["admin", "employee", "employee"]:
        phone = "138" + str(int(uuid4().hex[:9], 16))[-8:].zfill(8)
        row = await shared.create_employee(
            db,
            s.EmployeeInput(
                name="合成测试", phone=phone, password="Test-only-Password42", role=role
            ),
            must_change=False,
        )
        values.append(row)
    await db.commit()
    # Capture scalar identities before tests can rollback/expire ORM instances.
    ids = [r.id for r in values]
    owned_cards = list((await db.scalars(select(Card).where(Card.employee_id.in_(ids)))).all())
    card_ids = [card.id for card in owned_cards]
    pending_keys = [f"render_pending-{card.code}" for card in owned_cards]
    company_id = company.id
    yield values[0], values[1], values[2]
    # Roll back test-created transactions by cleaning only known IDs and their dependants.
    from sqlalchemy import delete

    from app.modules.workspace.models import (
        Assistant,
        AuditLog,
        ChatSession,
        Correction,
        Issue,
        Visit,
    )

    await db.rollback()
    sessions = select(ChatSession.id).where(ChatSession.card_id.in_(card_ids))
    await db.execute(delete(Message).where(Message.session_id.in_(sessions)))
    for model, where in [
        (Setting, Setting.key.in_(pending_keys)),
        (Notification, Notification.employee_id.in_(ids)),
        (Lead, Lead.card_id.in_(card_ids)),
        (Correction, Correction.card_id.in_(card_ids)),
        (Issue, Issue.card_id.in_(card_ids)),
        (Visit, Visit.card_id.in_(card_ids)),
        (ChatSession, ChatSession.card_id.in_(card_ids)),
        (Assistant, Assistant.card_id.in_(card_ids)),
        (AuditLog, AuditLog.operator_id.in_(ids)),
        (Card, Card.employee_id.in_(ids)),
        (Employee, Employee.id.in_(ids)),
    ]:
        await db.execute(delete(model).where(where))
    if added_company:
        await db.execute(delete(Company).where(Company.id == company_id))
    await db.commit()


async def test_员工夹具回滚后仍清理自己的队列且不删除其他队列(db):
    from sqlalchemy import delete

    sentinel_key = f"render_pending-fixture-probe-{uuid4().hex}"
    sentinel = {"card_id": 0, "version": "synthetic-unrelated"}
    db.add(Setting(key=sentinel_key, value=sentinel))
    await db.commit()
    fixture = employees.__wrapped__(db)
    try:
        rows = await anext(fixture)
        ids = [row.id for row in rows]
        codes = list((await db.scalars(select(Card.code).where(Card.employee_id.in_(ids)))).all())
        keys = [f"render_pending-{code}" for code in codes]
        assert len((await db.scalars(select(Setting).where(Setting.key.in_(keys)))).all()) == 3
        # Rollback expires ORM objects; teardown must use saved scalar identities.
        await db.rollback()
        with pytest.raises(StopAsyncIteration):
            await anext(fixture)
        assert await db.scalar(select(Setting.id).where(Setting.key.in_(keys))) is None
        assert await db.scalar(select(Employee.id).where(Employee.id.in_(ids))) is None
        assert await db.scalar(select(Setting.value).where(Setting.key == sentinel_key)) == sentinel
    finally:
        await fixture.aclose()
        await db.execute(delete(Setting).where(Setting.key == sentinel_key))
        await db.commit()


async def test_真实MySQL线索及通知所有权(
    db: AsyncSession, employees: tuple[Employee, Employee, Employee]
) -> None:
    _, employee, colleague = employees
    visitor = Visitor(anon_id=str(uuid4()))
    db.add(visitor)
    await db.commit()
    card = await shared.own_card(db, employee.id)
    session = await chat.session_create(db, card, visitor.id)
    result = await me.create_lead(
        db,
        visitor,
        s.LeadInput(
            card_code=card.code,
            session_id=session.session_id,
            name="合成访客",
            phone="13800009999",
            consent=True,
        ),
    )
    with pytest.raises(AppError) as exc:
        await me.lead_detail(db, colleague.id, result.id)
    assert exc.value.status == 404
    assert (await me.unread_count(db, employee.id)).count == 1
    notification = await db.scalar(
        select(Notification).where(Notification.employee_id == employee.id)
    )
    assert notification is not None
    with pytest.raises(AppError) as exc:
        await me.notification_read(db, colleague.id, notification.id)
    assert exc.value.status == 404
    await me.lead_detail(
        db, employee.id, result.id, s.LeadPatch(status="contacted", remark="已联系")
    )
    assert (await me.unread_count(db, employee.id)).count == 0
    # The fixture removes lead/session first; visitor cleanup is independent.
    visitor.phone = ""


async def test_重复同意留资只更新且不合并手机号身份(
    db: AsyncSession, employees: tuple[Employee, Employee, Employee]
) -> None:
    _, employee, _ = employees
    card = await shared.own_card(db, employee.id)
    visitors = [Visitor(anon_id=str(uuid4())) for _ in range(2)]
    db.add_all(visitors)
    await db.commit()
    payload = s.LeadInput(card_code=card.code, name="合成", phone="13800009999", consent=True)
    first = await me.create_lead(db, visitors[0], payload)
    duplicate = await me.create_lead(
        db, visitors[0], payload.model_copy(update={"need": "修改需求"})
    )
    separate = await me.create_lead(db, visitors[1], payload)
    assert first.id == duplicate.id
    assert separate.id != first.id
    row = await db.get(Lead, first.id)
    assert row is not None and row.need == "修改需求"


async def test_访客与调试会话不能互读且调试不计统计(
    db: AsyncSession, employees: tuple[Employee, Employee, Employee]
) -> None:
    _, employee, colleague = employees
    visitor = Visitor(anon_id=str(uuid4()))
    other = Visitor(anon_id=str(uuid4()))
    db.add_all([visitor, other])
    await db.commit()
    card = await shared.own_card(db, employee.id)
    public = await chat.session_create(db, card, visitor.id)
    debug = await chat.session_create(db, card, None, employee.id)
    for session_id, kwargs in [
        (public.session_id, {"visitor_id": other.id}),
        (debug.session_id, {"visitor_id": visitor.id}),
        (debug.session_id, {"employee_id": colleague.id}),
    ]:
        with pytest.raises(AppError) as exc:
            await chat.session_access(db, session_id, **kwargs)
        assert exc.value.status == 404
    stats = await me.stats(db, employee.id, "7d")
    assert stats.chats == 1
    assert (await me.visitors(db, employee.id, 1, 20)).total == 1


async def test_管理员自身保护与重置使token版本失效(
    db: AsyncSession, employees: tuple[Employee, Employee, Employee]
) -> None:
    actor, employee, _ = employees
    for payload in [s.EmployeeUpdate(role="employee"), s.EmployeeUpdate(status="disabled")]:
        with pytest.raises(AppError) as exc:
            await admin.employee_update(db, actor, actor.id, payload)
        assert exc.value.status == 403
    old_version = employee.token_version
    await admin.employee_reset(
        db, actor, employee.id, s.ResetPassword(password="NewTest-Password42")
    )
    assert employee.token_version == old_version + 1
    assert employee.must_change_pwd


async def test_MySQL原子限流超过阈值拒绝(db: AsyncSession) -> None:
    from sqlalchemy import delete

    key = "test:" + uuid4().hex
    try:
        await hit(db, key, "test", 2)
        await hit(db, key, "test", 2)
        with pytest.raises(AppError) as exc:
            await hit(db, key, "test", 2)
        assert exc.value.code == ErrorCode.RATE_LIMITED
        assert await db.scalar(select(RateCounter.count).where(RateCounter.key == key)) == 3
    finally:
        await db.execute(delete(RateCounter).where(RateCounter.key == key))
        await db.commit()
