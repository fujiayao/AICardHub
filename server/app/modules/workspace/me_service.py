from datetime import UTC, timedelta
from typing import Any, cast
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import utcnow
from app.core.errors import AppError, ErrorCode
from app.modules.workspace import repo
from app.modules.workspace import schemas as s
from app.modules.workspace import service as shared
from app.modules.workspace.models import (
    Card,
    ChatSession,
    Correction,
    Employee,
    Lead,
    Message,
    Notification,
    Visit,
    Visitor,
)


def mask_phone(phone: str) -> str:
    return phone[:3] + "****" + phone[-4:] if len(phone) == 11 else phone


async def create_lead(db: AsyncSession, visitor: Visitor, payload: s.LeadInput) -> s.LeadResult:
    card = await shared.by_code(db, payload.card_code, active=True)
    if payload.session_id is not None:
        await repo.one(
            db,
            ChatSession,
            ChatSession.id == payload.session_id,
            ChatSession.visitor_id == visitor.id,
            ChatSession.card_id == card.id,
            ChatSession.is_test.is_(False),
        )
    from app.modules.workspace.campaign_service import attribution

    visit_id, campaign_id, source = await attribution(
        db,
        card,
        visitor.id,
        visit_id=payload.visit_id,
        campaign_id=payload.campaign_id,
        source=payload.source,
        session_id=payload.session_id,
    )
    # Serialize submissions for the same anonymous identity, including first lead creation.
    await repo.one(db, Visitor, Visitor.id == visitor.id, lock=True)
    lead = await repo.optional(
        db,
        Lead,
        Lead.card_id == card.id,
        Lead.visitor_id == visitor.id,
        Lead.campaign_id == campaign_id,
        Lead.created_at >= utcnow() - timedelta(hours=24),
    )
    owner_id = await shared.lead_owner(db, card)
    values = payload.model_dump(
        exclude={"card_code", "consent", "campaign_id", "visit_id", "source"}
    )
    if lead:
        repo.assign(lead, {key: value for key, value in values.items() if key != "session_id"})
    else:
        lead = Lead(
            **values,
            card_id=card.id,
            visitor_id=visitor.id,
            owner_employee_id=owner_id,
            visit_id=visit_id,
            campaign_id=campaign_id,
            source=source,
        )
        db.add(lead)
        await db.flush()
        db.add(
            Notification(
                employee_id=owner_id,
                type="lead_new",
                title="收到新的客户线索",
                content=f"{payload.name} 提交了联系意向",
                target_type="lead",
                target_id=lead.id,
            )
        )
    visitor.phone = payload.phone
    await db.commit()
    return s.LeadResult(id=lead.id, status=lead.status)


async def leads(
    db: AsyncSession,
    employee_id: int | None,
    page: int,
    page_size: int,
    status: str = "",
    q: str = "",
) -> s.Page[s.LeadData]:
    stmt = select(Lead).order_by(Lead.id.desc())
    if employee_id is not None:
        stmt = stmt.where(Lead.owner_employee_id == employee_id)
    if status:
        stmt = stmt.where(Lead.status == status)
    if q:
        stmt = stmt.where(
            or_(Lead.name.contains(q), Lead.phone.contains(q), Lead.company_name.contains(q))
        )
    result = await repo.page(db, stmt, page, page_size)
    items = [s.LeadData.model_validate(row) for row in result["items"]]
    for item in items:
        item.phone = mask_phone(item.phone)
    return s.Page[s.LeadData](**{**result, "items": items})


async def lead_detail(
    db: AsyncSession, employee_id: int, lead_id: int, payload: s.LeadPatch | None = None
) -> s.LeadData:
    row = await repo.one(
        db,
        Lead,
        Lead.id == lead_id,
        Lead.owner_employee_id == employee_id,
        code=ErrorCode.LEAD_NOT_FOUND,
    )
    if payload:
        repo.assign(row, payload.model_dump(exclude_none=True))
    row.read_at = utcnow()
    await db.execute(
        update(Notification)
        .where(
            Notification.employee_id == employee_id,
            Notification.target_type == "lead",
            Notification.target_id == lead_id,
            Notification.read_at.is_(None),
        )
        .values(read_at=utcnow())
    )
    await db.commit()
    return s.LeadData.model_validate(row)


async def notifications(
    db: AsyncSession, employee_id: int, page: int, page_size: int, status: str = ""
) -> s.Page[s.NotificationData]:
    stmt = (
        select(Notification)
        .where(Notification.employee_id == employee_id)
        .order_by(Notification.id.desc())
    )
    if status == "unread":
        stmt = stmt.where(Notification.read_at.is_(None))
    return s.Page[s.NotificationData](**await repo.page(db, stmt, page, page_size))


async def unread_count(db: AsyncSession, employee_id: int) -> s.CountData:
    count = await db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.employee_id == employee_id, Notification.read_at.is_(None))
    )
    return s.CountData(count=count or 0)


async def assistant_metrics(db: AsyncSession, employee_id: int) -> s.AssistantMetrics:
    from app.modules.workspace.knowledge_service import notes

    card = await shared.own_card(db, employee_id)
    start = utcnow() - timedelta(days=7)
    sessions = select(ChatSession.id).where(
        ChatSession.card_id == card.id, ChatSession.is_test.is_(False)
    )
    messages = list(
        (
            await db.scalars(
                select(Message).where(
                    Message.session_id.in_(sessions),
                    Message.role == "assistant",
                    Message.created_at >= start,
                )
            )
        ).all()
    )
    personal = await notes(db, employee_id, 1, 1)
    correction_count = await db.scalar(
        select(func.count()).select_from(Correction).where(Correction.card_id == card.id)
    )
    return s.AssistantMetrics(
        answers=len(messages),
        unanswered=sum(row.nokb for row in messages),
        disliked=sum(row.feedback == "down" for row in messages),
        notes=personal.total,
        corrections=correction_count or 0,
    )


async def notification_read(
    db: AsyncSession, employee_id: int, notification_id: int | None
) -> s.OK:
    if notification_id is not None:
        row = await repo.one(
            db,
            Notification,
            Notification.id == notification_id,
            Notification.employee_id == employee_id,
        )
        row.read_at = row.read_at or utcnow()
    else:
        await db.execute(
            update(Notification)
            .where(Notification.employee_id == employee_id, Notification.read_at.is_(None))
            .values(read_at=utcnow())
        )
    await db.commit()
    return s.OK()


async def visitors(
    db: AsyncSession, employee_id: int, page: int, page_size: int
) -> s.Page[s.VisitorData]:
    card_ids = await shared.customer_card_ids(db, employee_id)
    ids = (
        select(Visit.visitor_id)
        .where(Visit.card_id.in_(card_ids))
        .union(
            select(ChatSession.visitor_id).where(
                ChatSession.card_id.in_(card_ids), ChatSession.is_test.is_(False)
            )
        )
    )
    stmt = select(Visitor).where(Visitor.id.in_(ids)).order_by(Visitor.last_seen_at.desc())
    result = await repo.page(db, stmt, page, page_size)
    items = []
    for row in result["items"]:
        item = s.VisitorData.model_validate(row)
        recent_visit = await db.scalar(
            select(Visit)
            .where(Visit.card_id.in_(card_ids), Visit.visitor_id == row.id)
            .order_by(Visit.created_at.desc(), Visit.id.desc())
            .limit(1)
        )
        recent_chat = await db.scalar(
            select(ChatSession)
            .where(
                ChatSession.card_id.in_(card_ids),
                ChatSession.visitor_id == row.id,
                ChatSession.is_test.is_(False),
            )
            .order_by(ChatSession.last_msg_at.desc(), ChatSession.id.desc())
            .limit(1)
        )
        if recent_visit:
            item.source = cast(s.Source, recent_visit.source)
        if recent_chat:
            item.intent_level = cast(Any, recent_chat.intent_level)
        items.append(item)
    return s.Page[s.VisitorData](**{**result, "items": items})


async def visitor_detail(db: AsyncSession, employee_id: int, visitor_id: int) -> s.VisitorDetail:
    from app.modules.workspace.release_mode import card_only

    card_ids = await shared.customer_card_ids(db, employee_id)
    visit = await repo.optional(
        db, Visit, Visit.card_id.in_(card_ids), Visit.visitor_id == visitor_id
    )
    sessions = await repo.many(
        db,
        ChatSession,
        ChatSession.card_id.in_(card_ids),
        ChatSession.visitor_id == visitor_id,
        ChatSession.is_test.is_(False),
    )
    if not visit and not sessions:
        raise AppError(ErrorCode.NOT_FOUND, 404, "访客不存在或无权访问")
    visitor = await repo.one(db, Visitor, Visitor.id == visitor_id)
    details = []
    for session in [] if card_only() else sessions:
        messages = await repo.many(db, Message, Message.session_id == session.id)
        details.append(
            s.VisitorSession(
                id=session.id,
                intent_level=session.intent_level,
                tags=session.tags,
                summary=session.summary,
                messages=[s.MessageData.model_validate(m) for m in messages],
            )
        )
    visits = await repo.many(db, Visit, Visit.card_id.in_(card_ids), Visit.visitor_id == visitor_id)
    return s.VisitorDetail(
        **s.VisitorData.model_validate(visitor).model_dump(),
        sessions=details,
        visits=[s.VisitorVisit.model_validate(row) for row in visits],
    )


async def stats(
    db: AsyncSession, employee_id: int | None, range_value: str
) -> s.StatsData | s.AdminStats:
    days = {"7d": 7, "30d": 30, "today": 1}.get(range_value)
    if days is None:
        raise AppError(ErrorCode.VALIDATION_ERROR, 422, "统计范围支持today、7d、30d")
    now = utcnow()
    business_tz = ZoneInfo("Asia/Shanghai")
    today_start = (
        now.astimezone(business_tz)
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .astimezone(UTC)
    )
    start = today_start - timedelta(days=days - 1)
    fetch_start = min(start, today_start - timedelta(days=1))
    card_ids = select(Card.id)
    if employee_id is not None:
        card_ids = card_ids.where(Card.id.in_(await shared.customer_card_ids(db, employee_id)))
    visit_rows = (
        await db.scalars(
            select(Visit).where(Visit.card_id.in_(card_ids), Visit.created_at >= fetch_start)
        )
    ).all()
    chat_rows = (
        await db.scalars(
            select(ChatSession).where(
                ChatSession.card_id.in_(card_ids),
                ChatSession.is_test.is_(False),
                ChatSession.created_at >= fetch_start,
            )
        )
    ).all()
    lead_stmt = select(Lead).where(Lead.created_at >= fetch_start)
    if employee_id is not None:
        lead_stmt = lead_stmt.where(Lead.owner_employee_id == employee_id)
    lead_rows = (await db.scalars(lead_stmt)).all()
    day_metrics = []
    for offset in (0, 1):
        lower = today_start - timedelta(days=offset)
        upper = lower + timedelta(days=1)
        vv = [r for r in visit_rows if lower <= r.created_at < upper]
        cc = [r for r in chat_rows if lower <= r.created_at < upper]
        ll = [r for r in lead_rows if lower <= r.created_at < upper]
        day_metrics.append(
            s.DayMetrics(
                visits=len(vv),
                visitors=len(
                    {r.visitor_id for r in vv} | {r.visitor_id for r in cc if r.visitor_id}
                ),
                chats=len(cc),
                leads=len(ll),
            )
        )
    visit_rows = [r for r in visit_rows if r.created_at >= start]
    chat_rows = [r for r in chat_rows if r.created_at >= start]
    lead_rows = [r for r in lead_rows if r.created_at >= start]
    daily = []
    for offset in range(days):
        date = (start + timedelta(days=offset)).astimezone(business_tz).date()
        daily.append(
            s.DailyStat(
                date=date.isoformat(),
                visits=sum(r.created_at.astimezone(business_tz).date() == date for r in visit_rows),
                chats=sum(r.created_at.astimezone(business_tz).date() == date for r in chat_rows),
                leads=sum(r.created_at.astimezone(business_tz).date() == date for r in lead_rows),
            )
        )
    visitor_count = len(
        {r.visitor_id for r in visit_rows} | {r.visitor_id for r in chat_rows if r.visitor_id}
    )
    values: dict[str, Any] = dict(
        visits=len(visit_rows),
        visitors=visitor_count,
        chats=len(chat_rows),
        leads=len(lead_rows),
        conversion_rate=round(len(lead_rows) / visitor_count, 4) if visitor_count else 0,
        daily=daily,
        today=day_metrics[0],
        yesterday=day_metrics[1],
        source_breakdown=[
            s.TrafficSource(
                source=source,
                visits=sum(r.source == source for r in visit_rows),
                visitors=len({r.visitor_id for r in visit_rows if r.source == source}),
                chats=sum(r.source == source for r in chat_rows),
                leads=sum(r.source == source for r in lead_rows),
            )
            for source in sorted(
                {"nfc", "qr", "poster", "link", "sig"}
                | {r.source for r in visit_rows}
                | {r.source for r in chat_rows}
                | {r.source for r in lead_rows}
            )
        ],
    )
    if employee_id is None:
        values["employees"] = await db.scalar(select(func.count()).select_from(Employee)) or 0
        values["cards"] = await db.scalar(select(func.count()).select_from(Card)) or 0
        values["overdue_leads"] = (
            await db.scalar(
                select(func.count())
                .select_from(Lead)
                .where(Lead.status == "new", Lead.created_at < now - timedelta(hours=24))
            )
            or 0
        )
        return s.AdminStats(**values)
    return s.StatsData(**values)
