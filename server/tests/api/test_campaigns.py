"""Real MySQL campaign boundaries; no network or real model calls."""

from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.core.db import utcnow
from app.core.errors import AppError
from app.modules.workspace import campaign_service as campaigns
from app.modules.workspace import chat_service as chat
from app.modules.workspace import me_service as me
from app.modules.workspace import schemas as s
from app.modules.workspace import service as shared
from app.modules.workspace.models import (
    Campaign,
    ChatSession,
    Lead,
    Message,
    Notification,
    Visit,
    Visitor,
)

pytest_plugins = ["test_backend_isolation"]


async def test_campaign_live_attribution_dedup_and_join_free_report(db, employees):
    actor, staff, colleague = employees
    card = await shared.own_card(db, staff.id)
    other_card = await shared.own_card(db, colleague.id)
    now = utcnow()
    event = await campaigns.save(
        db,
        actor,
        s.CampaignInput(
            name="合成活动权限测试",
            status="active",
            start_at=now - timedelta(hours=1),
            end_at=now + timedelta(hours=1),
            opening_override="活动专属欢迎",
            guide_override=["活动引导问题"],
        ),
    )
    visitor = Visitor(anon_id=str(uuid4()))
    second = Visitor(anon_id=str(uuid4()))
    db.add_all([visitor, second])
    await db.commit()
    try:
        visit = await shared.create_visit(
            db, visitor, s.VisitInput(card_code=card.code, source="qr", campaign_id=event.id)
        )
        session = await chat.session_create(
            db, card, visitor.id, visit_id=visit.visit_id, campaign_id=event.id
        )
        assert session.campaign_id == event.id and session.source == "qr"
        assert session.opening == "活动专属欢迎"
        public = await shared.public_card(db, card.code, event.id)
        assert public.campaign.id == event.id and public.assistant.opening == "活动专属欢迎"
        with pytest.raises(AppError) as error:
            await campaigns.attribution(
                db,
                other_card,
                visitor.id,
                visit_id=visit.visit_id,
                campaign_id=event.id,
                source="link",
            )
        assert error.value.status == 404
        with pytest.raises(AppError):
            await campaigns.attribution(
                db, card, second.id, visit_id=visit.visit_id, campaign_id=event.id, source="link"
            )
        lead_input = s.LeadInput(
            card_code=card.code,
            session_id=session.session_id,
            campaign_id=event.id,
            name="合成访客",
            phone="13800009998",
            consent=True,
        )
        first = await me.create_lead(db, visitor, lead_input)
        duplicate = await me.create_lead(db, visitor, lead_input)
        assert first.id == duplicate.id
        business = await me.create_lead(
            db,
            visitor,
            s.LeadInput(
                card_code=card.code, name="商务合成访客", phone="13800009998", consent=True
            ),
        )
        assert business.id != first.id
        await db.execute(delete(Lead).where(Lead.id == business.id))
        await db.commit()
        row = await db.get(ChatSession, session.session_id)
        row.rounds = 1
        db.add(Message(session_id=row.id, role="user", content="合成问题"))
        await db.commit()
        report = await campaigns.report(db, event.id)
        assert (report.visits, report.visitors, report.chats, report.leads) == (1, 1, 1, 1)
        qr = next(x for x in report.source_breakdown if x.source == "qr")
        assert (qr.visits, qr.chats, qr.leads) == (1, 1, 1)
        ended = await campaigns.save(
            db,
            actor,
            s.CampaignInput(
                name=event.name, status="ended", start_at=event.start_at, end_at=event.end_at
            ),
            event.id,
        )
        assert not ended.is_live
        with pytest.raises(AppError) as err:
            await campaigns.get(db, event.id, public=True)
        assert err.value.status == 404
        # Existing verified context can convert late but a new event context cannot.
        assert (
            await campaigns.attribution(
                db,
                card,
                visitor.id,
                visit_id=None,
                campaign_id=event.id,
                source="link",
                session_id=session.session_id,
            )
        )[1] == event.id
        with pytest.raises(AppError):
            await campaigns.attribution(
                db, card, second.id, visit_id=None, campaign_id=event.id, source="link"
            )
        with pytest.raises(AppError):
            await campaigns.remove(db, actor, event.id)
    finally:
        sess_ids = select(ChatSession.id).where(ChatSession.campaign_id == event.id)
        await db.execute(
            delete(Notification).where(Notification.employee_id.in_([staff.id, colleague.id]))
        )
        await db.execute(delete(Lead).where(Lead.campaign_id == event.id))
        await db.execute(delete(Message).where(Message.session_id.in_(sess_ids)))
        await db.execute(delete(ChatSession).where(ChatSession.campaign_id == event.id))
        await db.execute(delete(Visit).where(Visit.campaign_id == event.id))
        await db.execute(delete(Campaign).where(Campaign.id == event.id))
        await db.execute(delete(Visitor).where(Visitor.id.in_([visitor.id, second.id])))
        await db.commit()


async def test_campaign_draft_delete_and_invalid_period(db, employees):
    actor, _, _ = employees
    now = utcnow()
    with pytest.raises(ValueError):
        s.CampaignInput(name="invalid", start_at=now, end_at=now)
    draft = await campaigns.save(
        db,
        actor,
        s.CampaignInput(name="可删除合成草稿", start_at=now, end_at=now + timedelta(hours=1)),
    )
    with pytest.raises(AppError):
        await campaigns.get(db, draft.id, public=True)
    assert (await campaigns.remove(db, actor, draft.id)).ok
