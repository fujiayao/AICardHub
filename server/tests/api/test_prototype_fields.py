"""Prototype-facing fields stay truthful and restricted to the current staff scope."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import delete

from app.modules.workspace import me_service as me
from app.modules.workspace import service as shared
from app.modules.workspace.models import ChatSession, Message, Visit, Visitor

pytest_plugins = ["test_backend_isolation"]


async def test_today_yesterday_use_shanghai_boundary_and_exclude_other_staff(
    db, employees, monkeypatch
):
    _, owner, other = employees
    card = await shared.own_card(db, owner.id)
    other_card = await shared.own_card(db, other.id)
    now = datetime(2026, 11, 14, 3, tzinfo=UTC)
    monkeypatch.setattr(me, "utcnow", lambda: now)
    visitor = Visitor(anon_id=str(uuid4()))
    db.add(visitor)
    await db.flush()
    # Shanghai 00:30 today is UTC 16:30 yesterday; UTC-date grouping is wrong here.
    today = datetime(2026, 11, 13, 16, 30, tzinfo=UTC)
    yesterday = today - timedelta(days=1)
    db.add_all(
        [
            Visit(card_id=card.id, visitor_id=visitor.id, source="qr", created_at=today),
            Visit(card_id=card.id, visitor_id=visitor.id, source="nfc", created_at=yesterday),
            Visit(card_id=other_card.id, visitor_id=visitor.id, source="poster", created_at=now),
            ChatSession(
                card_id=card.id,
                visitor_id=visitor.id,
                is_test=False,
                intent_level="B",
                created_at=today,
                last_msg_at=today,
            ),
            ChatSession(
                card_id=other_card.id,
                visitor_id=visitor.id,
                is_test=False,
                intent_level="A",
                created_at=now,
                last_msg_at=now,
            ),
        ]
    )
    await db.commit()
    try:
        stats = await me.stats(db, owner.id, "today")
        assert stats.visits == 1
        assert stats.today.visits == 1 and stats.yesterday.visits == 1
        assert stats.today.visitors == 1 and stats.today.chats == 1
        assert stats.daily[0].date == "2026-11-14"
        listing = await me.visitors(db, owner.id, 1, 20)
        row = next(item for item in listing.items if item.id == visitor.id)
        assert row.source == "qr" and row.intent_level == "B"
        card_data = await shared.card_data(db, card)
        company = await shared.employee_company(db, owner)
        assert card_data.company_id == company.id
        assert card_data.company_name == company.name
    finally:
        await db.execute(delete(ChatSession).where(ChatSession.visitor_id == visitor.id))
        await db.execute(delete(Visit).where(Visit.visitor_id == visitor.id))
        await db.delete(visitor)
        await db.commit()


async def test_assistant_metrics_exclude_other_staff_and_debug_sessions(db, employees, monkeypatch):
    import tempfile

    from app.core.config import get_settings

    _, owner, other = employees
    own_card = await shared.own_card(db, owner.id)
    other_card = await shared.own_card(db, other.id)
    with tempfile.TemporaryDirectory() as temporary:
        monkeypatch.setattr(get_settings(), "kb_root", temporary)
        sessions = [
            ChatSession(card_id=own_card.id, is_test=False),
            ChatSession(card_id=own_card.id, is_test=True),
            ChatSession(card_id=other_card.id, is_test=False),
        ]
        db.add_all(sessions)
        await db.flush()
        ids = [row.id for row in sessions]
        db.add_all(
            [
                Message(
                    session_id=ids[0],
                    role="assistant",
                    content="需确认",
                    nokb=True,
                    feedback="down",
                ),
                Message(session_id=ids[1], role="assistant", content="调试，不计统计", nokb=True),
                Message(session_id=ids[2], role="assistant", content="其他员工", nokb=True),
            ]
        )
        await db.commit()
        try:
            metrics = await me.assistant_metrics(db, owner.id)
            assert metrics.answers == metrics.unanswered == metrics.disliked == 1
            assert metrics.notes == 0
        finally:
            await db.execute(delete(Message).where(Message.session_id.in_(ids)))
            await db.execute(delete(ChatSession).where(ChatSession.id.in_(ids)))
            await db.commit()
