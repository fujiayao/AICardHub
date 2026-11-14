"""Tests-first MySQL regressions for optional hints and canonical session attribution.

Call real services without mocks, network requests, streaming, or LLM clients.
The imported db fixture permits only aicardhub_test; all cleanup is fixture-owned.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import utcnow
from app.core.errors import AppError
from app.modules.workspace import chat_service as chat
from app.modules.workspace import me_service as me
from app.modules.workspace import schemas as s
from app.modules.workspace import service as shared
from app.modules.workspace.models import (
    Campaign,
    Card,
    ChatSession,
    Lead,
    Message,
    Notification,
    Visit,
    Visitor,
)

pytest_plugins = ["test_backend_isolation"]

# Valid positive BIGINT hints, explicitly checked absent before use.
MISSING_ID = 2**63 - 1
OPERATIONS = ["chat", "lead", "session_lead"]


@dataclass
class AttributionCase:
    card: Card
    other_card: Card
    visitor: Visitor
    other_visitor: Visitor
    active: Campaign
    other_active: Campaign
    draft: Campaign
    expired: Campaign
    deleted_visit_id: int
    foreign_visits: dict[str, Visit]


def attribution(row: ChatSession | Lead | s.SessionResult) -> tuple[int | None, int | None, str]:
    return row.visit_id, row.campaign_id, row.source


@pytest_asyncio.fixture
async def case(db: AsyncSession, employees) -> AsyncIterator[AttributionCase]:
    _, employee, colleague = employees
    card = await shared.own_card(db, employee.id)
    other_card = await shared.own_card(db, colleague.id)
    visitors = [Visitor(anon_id=str(uuid4())) for _ in range(2)]
    now = utcnow()
    events = [
        Campaign(
            name=f"optional-attribution-{uuid4().hex}",
            status=status,
            start_at=now - timedelta(days=2),
            end_at=now + timedelta(days=1) if status != "expired" else now - timedelta(days=1),
            opening_override=f"synthetic-event-opening-{index}",
            guide_override=[f"synthetic-event-guide-{index}"],
        )
        for index, status in enumerate(["active", "active", "draft", "expired"])
    ]
    # Expired means an active campaign whose time window has elapsed, not an
    # unrecognised lifecycle status.
    events[-1].status = "active"
    db.add_all([*visitors, *events])
    await db.flush()
    visitor_ids = [row.id for row in visitors]
    campaign_ids = [row.id for row in events]
    card_ids = [card.id, other_card.id]
    try:
        for model in (Visit, Campaign, ChatSession):
            assert await db.get(model, MISSING_ID) is None
        deleted = Visit(card_id=card.id, visitor_id=visitors[0].id, source="qr")
        db.add(deleted)
        await db.flush()
        deleted_visit_id = deleted.id
        await db.delete(deleted)
        foreign = {
            "foreign_visitor": Visit(
                card_id=card.id,
                visitor_id=visitors[1].id,
                source="nfc",
                campaign_id=events[1].id,
            ),
            "foreign_card": Visit(
                card_id=other_card.id,
                visitor_id=visitors[0].id,
                source="qr",
                campaign_id=events[1].id,
            ),
            "foreign_both": Visit(
                card_id=other_card.id,
                visitor_id=visitors[1].id,
                source="sig",
                campaign_id=events[1].id,
            ),
        }
        db.add_all(foreign.values())
        await db.commit()
        yield AttributionCase(
            card,
            other_card,
            visitors[0],
            visitors[1],
            *events,
            deleted_visit_id,
            foreign,
        )
    finally:
        await db.rollback()
        for employee in employees:
            await db.refresh(employee)
        # These cards belong exclusively to employees created by the imported
        # fixture. Include committed service side effects even after assertions fail.
        lead_ids = select(Lead.id).where(Lead.card_id.in_(card_ids))
        session_ids = select(ChatSession.id).where(ChatSession.card_id.in_(card_ids))
        await db.execute(
            delete(Notification).where(
                Notification.target_type == "lead", Notification.target_id.in_(lead_ids)
            )
        )
        await db.execute(delete(Message).where(Message.session_id.in_(session_ids)))
        await db.execute(delete(Lead).where(Lead.card_id.in_(card_ids)))
        await db.execute(delete(ChatSession).where(ChatSession.card_id.in_(card_ids)))
        await db.execute(delete(Visit).where(Visit.visitor_id.in_(visitor_ids)))
        await db.execute(delete(Campaign).where(Campaign.id.in_(campaign_ids)))
        await db.execute(delete(Visitor).where(Visitor.id.in_(visitor_ids)))
        await db.commit()


def visit_hint(case: AttributionCase, kind: str) -> int | None:
    if kind == "absent":
        return None
    if kind == "missing":
        return MISSING_ID
    if kind == "deleted":
        return case.deleted_visit_id
    return case.foreign_visits[kind].id


async def exercise_optional_hint(
    db: AsyncSession,
    case: AttributionCase,
    operation: str,
    visit_id: int | None,
    campaign_id: int | None = None,
) -> tuple[int | None, int | None, str]:
    if operation == "chat":
        result = await chat.session_create(
            db,
            case.card,
            case.visitor.id,
            visit_id=visit_id,
            campaign_id=campaign_id,
            source="poster",
        )
        row = await db.get(ChatSession, result.session_id, populate_existing=True)
        assert row is not None
        assert (row.card_id, row.visitor_id, row.is_test) == (
            case.card.id,
            case.visitor.id,
            False,
        )
        assert attribution(result) == attribution(row)
        assistant = await shared.assistant_get(db, case.card)
        assert result.opening == assistant.opening
        assert result.guide_questions == assistant.guide_questions
        return attribution(row)

    session_id = None
    if operation == "session_lead":
        session = await chat.session_create(db, case.card, case.visitor.id, source="poster")
        session_id = session.session_id
    result = await me.create_lead(
        db,
        case.visitor,
        s.LeadInput(
            card_code=case.card.code,
            session_id=session_id,
            visit_id=visit_id,
            campaign_id=campaign_id,
            source="poster",
            name="合成可选归因访客",
            phone="13800009997",
            consent=True,
        ),
    )
    row = await db.get(Lead, result.id, populate_existing=True)
    assert row is not None
    assert (row.card_id, row.visitor_id, row.session_id) == (
        case.card.id,
        case.visitor.id,
        session_id,
    )
    return attribution(row)


@pytest.mark.parametrize("operation", OPERATIONS)
@pytest.mark.parametrize(
    "kind",
    [
        "absent",
        "missing",
        "deleted",
        "foreign_visitor",
        "foreign_card",
        "foreign_both",
    ],
)
async def test_无效或外来访问提示与缺失访问完全同效且不泄露归因(
    db: AsyncSession,
    case: AttributionCase,
    operation: str,
    kind: str,
) -> None:
    # Compare real service outcomes, not merely a status code. Foreign campaign
    # and source must never be copied into either response or persisted record.
    actual = await exercise_optional_hint(db, case, operation, visit_hint(case, kind))
    assert actual == (None, None, "poster")


@pytest.mark.parametrize("operation", OPERATIONS)
@pytest.mark.parametrize("visit_kind", ["absent", "missing", "deleted"])
@pytest.mark.parametrize("campaign_kind", ["expired", "draft", "missing"])
async def test_过期草稿或不存在的活动提示不阻断会话或留资且不成为归因(
    db: AsyncSession,
    case: AttributionCase,
    operation: str,
    visit_kind: str,
    campaign_kind: str,
) -> None:
    campaign_id = MISSING_ID if campaign_kind == "missing" else getattr(case, campaign_kind).id
    assert await exercise_optional_hint(
        db,
        case,
        operation,
        visit_hint(case, visit_kind),
        campaign_id,
    ) == (None, None, "poster")


async def canonical_session(db: AsyncSession, case: AttributionCase, with_campaign: bool):
    visit = await shared.create_visit(
        db,
        case.visitor,
        s.VisitInput(
            card_code=case.card.code,
            source="qr",
            campaign_id=case.active.id if with_campaign else None,
        ),
    )
    session = await chat.session_create(
        db,
        case.card,
        case.visitor.id,
        visit_id=visit.visit_id,
        source="link",
    )
    return session, (visit.visit_id, case.active.id if with_campaign else None, "qr")


@pytest.mark.parametrize("with_campaign", [False, True])
async def test_访问A创建会话后刷新访问B仍可留资且保留会话A归因(
    db: AsyncSession,
    case: AttributionCase,
    with_campaign: bool,
) -> None:
    session, expected = await canonical_session(db, case, with_campaign)
    refresh = await shared.create_visit(
        db,
        case.visitor,
        s.VisitInput(
            card_code=case.card.code,
            source="nfc",
            campaign_id=case.active.id if with_campaign else None,
        ),
    )
    assert refresh.visit_id != session.visit_id
    payload = s.LeadInput(
        card_code=case.card.code,
        session_id=session.session_id,
        visit_id=refresh.visit_id,
        campaign_id=refresh.campaign_id,
        source="nfc",
        name="合成刷新访客",
        phone="13800009997",
        consent=True,
    )
    # There is deliberately no earlier lead: dedup must not hide a wrong INSERT.
    result = await me.create_lead(db, case.visitor, payload)
    row = await db.get(Lead, result.id, populate_existing=True)
    assert row is not None and row.session_id == session.session_id
    assert attribution(row) == expected
    duplicate = await me.create_lead(db, case.visitor, payload)
    assert duplicate.id == result.id
    persisted = await db.get(ChatSession, session.session_id, populate_existing=True)
    assert persisted is not None and attribution(persisted) == expected


@pytest.mark.parametrize("with_campaign", [False, True])
@pytest.mark.parametrize(
    "hint",
    [
        "live_campaign",
        "draft",
        "expired",
        "missing_campaign",
        "missing_visit",
        "deleted_visit",
        "foreign_visitor",
        "foreign_card",
        "foreign_both",
    ],
)
async def test_已授权会话归因优先于冲突活动或无效访问提示(
    db: AsyncSession,
    case: AttributionCase,
    with_campaign: bool,
    hint: str,
) -> None:
    session, expected = await canonical_session(db, case, with_campaign)
    visit_id = None
    campaign_id = None
    if hint == "live_campaign":
        campaign_id = case.other_active.id
    elif hint in {"draft", "expired"}:
        campaign_id = getattr(case, hint).id
    elif hint == "missing_campaign":
        campaign_id = MISSING_ID
    else:
        visit_id = visit_hint(case, hint.removesuffix("_visit"))
    result = await me.create_lead(
        db,
        case.visitor,
        s.LeadInput(
            card_code=case.card.code,
            session_id=session.session_id,
            visit_id=visit_id,
            campaign_id=campaign_id,
            source="sig",
            name="合成会话优先访客",
            phone="13800009997",
            consent=True,
        ),
    )
    row = await db.get(Lead, result.id, populate_existing=True)
    persisted = await db.get(ChatSession, session.session_id, populate_existing=True)
    assert row is not None and row.session_id == session.session_id
    assert persisted is not None
    assert attribution(row) == attribution(persisted) == expected


@pytest.mark.parametrize("kind", ["visitor", "card", "test", "missing"])
async def test_会话所有权严格拒绝跨访客跨名片调试及不存在会话(
    db: AsyncSession,
    case: AttributionCase,
    kind: str,
) -> None:
    if kind == "missing":
        session_id = MISSING_ID
    elif kind == "test":
        # Keep the same visitor/card to isolate is_test from other ownership checks.
        debug = ChatSession(card_id=case.card.id, visitor_id=case.visitor.id, is_test=True)
        db.add(debug)
        await db.commit()
        session_id = debug.id
    else:
        session = await chat.session_create(
            db,
            case.other_card if kind == "card" else case.card,
            case.other_visitor.id if kind == "visitor" else case.visitor.id,
        )
        session_id = session.session_id
    owned_visit = await shared.create_visit(
        db,
        case.visitor,
        s.VisitInput(
            card_code=case.card.code,
            source="qr",
            campaign_id=case.active.id,
        ),
    )
    with pytest.raises(AppError) as error:
        await me.create_lead(
            db,
            case.visitor,
            s.LeadInput(
                card_code=case.card.code,
                session_id=session_id,
                visit_id=owned_visit.visit_id,
                campaign_id=case.active.id,
                name="合成越权访客",
                phone="13800009997",
                consent=True,
            ),
        )
    assert error.value.status == 404
    assert (
        await db.scalar(
            select(Lead.id).where(
                Lead.card_id.in_(
                    [case.card.id, case.other_card.id],
                )
            )
        )
        is None
    )
    assert (
        await db.scalar(
            select(Notification.id).where(
                Notification.employee_id.in_([case.card.employee_id, case.other_card.employee_id]),
                Notification.target_type == "lead",
            )
        )
        is None
    )


@pytest_asyncio.fixture
async def api(db, monkeypatch):
    import httpx
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.core.db import get_db
    from app.main import app

    factory = async_sessionmaker(db.bind, expire_on_commit=False)

    async def use_db():
        async with factory() as session:
            yield session

    monkeypatch.setitem(app.dependency_overrides, get_db, use_db)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


def visitor_headers(visitor):
    from app.core.security import issue_token

    return {"Authorization": "Bearer " + issue_token(visitor.anon_id, "visitor")}


async def test_HTTP刷新后留资成功且未同意与跨访客仍拒绝(db, case, api):
    headers = visitor_headers(case.visitor)
    first = await api.post(
        "/api/v1/public/visits",
        headers=headers,
        json={
            "card_code": case.card.code,
            "source": "qr",
            "campaign_id": case.active.id,
        },
    )
    assert first.status_code == 200
    session = await api.post(
        "/api/v1/public/chat/sessions",
        headers=headers,
        json={
            "card_code": case.card.code,
            "visit_id": first.json()["visit_id"],
        },
    )
    assert session.status_code == 200
    refresh = await api.post(
        "/api/v1/public/visits",
        headers=headers,
        json={
            "card_code": case.card.code,
            "source": "nfc",
        },
    )
    assert refresh.status_code == 200
    payload = dict(
        card_code=case.card.code,
        session_id=session.json()["session_id"],
        visit_id=refresh.json()["visit_id"],
        name="合成HTTP访客",
        phone="13800009997",
        consent=True,
    )
    response = await api.post(
        "/api/v1/public/leads", headers=headers, json={**payload, "consent": False}
    )
    assert response.status_code == 422
    denied = await api.post(
        "/api/v1/public/leads", headers=visitor_headers(case.other_visitor), json=payload
    )
    assert denied.status_code == 404
    response = await api.post("/api/v1/public/leads", headers=headers, json=payload)
    assert response.status_code == 200
    row = await db.get(Lead, response.json()["id"])
    assert attribution(row) == (first.json()["visit_id"], case.active.id, "qr")
    assert (
        await api.get(
            f"/api/v1/public/chat/sessions/{payload['session_id']}/messages", headers=headers
        )
    ).status_code == 200
    assert (
        await api.get(
            f"/api/v1/public/chat/sessions/{payload['session_id']}/messages",
            headers=visitor_headers(case.other_visitor),
        )
    ).status_code == 404
    assert (await api.post("/api/v1/public/leads", json=payload)).status_code == 401


async def test_HTTP过期活动和外来访问可降级但不泄露私有开场(db, case, api):
    response = await api.post(
        "/api/v1/public/chat/sessions",
        headers=visitor_headers(case.visitor),
        json={
            "card_code": case.card.code,
            "visit_id": case.foreign_visits["foreign_both"].id,
            "campaign_id": case.draft.id,
        },
    )
    assert response.status_code == 200
    assert response.json()["visit_id"] is None
    assert response.json()["campaign_id"] is None
    assert "synthetic-event" not in response.json()["opening"]
    row = await db.get(ChatSession, response.json()["session_id"])
    assert attribution(row) == (None, None, "link")


async def test_HTTP停用名片继续阻断建会话聊天与留资(db, case, api):
    session = await chat.session_create(db, case.card, case.visitor.id)
    case.card.status = "disabled"
    await db.commit()
    headers = visitor_headers(case.visitor)
    for path, payload in [
        ("/api/v1/public/chat/sessions", {"card_code": case.card.code, "visit_id": MISSING_ID}),
        (f"/api/v1/public/chat/sessions/{session.session_id}/messages", {"content": "hello"}),
        (
            "/api/v1/public/leads",
            {
                "card_code": case.card.code,
                "session_id": session.session_id,
                "visit_id": MISSING_ID,
                "consent": True,
                "name": "合成停用测试",
                "phone": "13800009997",
            },
        ),
    ]:
        response = await api.post(path, headers=headers, json=payload)
        assert response.status_code == 409
        assert response.json()["code"] == "CARD_DISABLED"
    assert await db.scalar(select(Lead.id).where(Lead.card_id == case.card.id)) is None


async def test_已验证访问优先于冲突活动并保留结束活动转化(db, case):
    visit = await shared.create_visit(
        db,
        case.visitor,
        s.VisitInput(
            card_code=case.card.code,
            source="qr",
            campaign_id=case.active.id,
        ),
    )
    case.active.status = "ended"
    await db.commit()
    result = await chat.session_create(
        db, case.card, case.visitor.id, visit_id=visit.visit_id, campaign_id=case.draft.id
    )
    assert attribution(result) == (visit.visit_id, case.active.id, "qr")
    assert result.opening == case.active.opening_override
