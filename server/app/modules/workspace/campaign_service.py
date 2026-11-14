"""Campaign lifecycle, immutable attribution and join-free aggregate reports."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import utcnow
from app.core.errors import AppError, ErrorCode
from app.modules.workspace import repo
from app.modules.workspace import schemas as s
from app.modules.workspace.models import Campaign, Card, ChatSession, Employee, Lead, Visit


def live(row: Campaign) -> bool:
    return row.status == "active" and row.start_at <= utcnow() < row.end_at


async def get(db: AsyncSession, campaign_id: int, *, public: bool = False) -> Campaign:
    row = await repo.one(db, Campaign, Campaign.id == campaign_id)
    if public and not live(row):
        raise AppError(ErrorCode.NOT_FOUND, 404, "活动不存在或已结束")
    return row


def data(row: Campaign) -> s.CampaignData:
    result = s.CampaignData.model_validate(row)
    result.is_live = live(row)
    return result


async def list_admin(
    db: AsyncSession, page: int, size: int, status: str = ""
) -> s.Page[s.CampaignData]:
    stmt = select(Campaign).order_by(Campaign.id.desc())
    if status:
        stmt = stmt.where(Campaign.status == status)
    result = await repo.page(db, stmt, page, size)
    result["items"] = [data(row) for row in result["items"]]
    return s.Page[s.CampaignData](**result)


async def save(
    db: AsyncSession, actor: Employee, payload: s.CampaignInput, campaign_id: int | None = None
) -> s.CampaignData:
    from app.modules.workspace.service import audit

    row = await get(db, campaign_id) if campaign_id else Campaign()
    if campaign_id and row.status == "ended" and payload.status != "ended":
        raise AppError(ErrorCode.CONFLICT, 409, "已结束活动不可重新启用")
    repo.assign(row, payload.model_dump())
    db.add(row)
    await db.flush()
    await audit(db, actor.id, "campaign.save", str(row.id))
    await db.commit()
    return data(row)


async def remove(db: AsyncSession, actor: Employee, campaign_id: int) -> s.OK:
    from app.modules.workspace.service import audit

    row = await get(db, campaign_id)
    used = False
    for model in (Visit, ChatSession, Lead):
        used = used or bool(
            await db.scalar(select(model.id).where(model.campaign_id == campaign_id).limit(1))
        )
    if row.status != "draft" or used:
        raise AppError(ErrorCode.CONFLICT, 409, "仅未使用的草稿活动可删除")
    await db.delete(row)
    await audit(db, actor.id, "campaign.delete", str(campaign_id))
    await db.commit()
    return s.OK()


async def list_public(db: AsyncSession) -> list[s.PublicCampaign]:
    now = utcnow()
    rows = (
        await db.scalars(
            select(Campaign)
            .where(Campaign.status == "active", Campaign.start_at <= now, Campaign.end_at > now)
            .order_by(Campaign.start_at)
        )
    ).all()
    return [s.PublicCampaign.model_validate(row) for row in rows]


async def attribution(
    db: AsyncSession,
    card: Card,
    visitor_id: int,
    *,
    visit_id: int | None,
    campaign_id: int | None,
    source: str,
    session_id: int | None = None,
) -> tuple[int | None, int | None, str]:
    if session_id is not None:
        session = await repo.one(
            db,
            ChatSession,
            ChatSession.id == session_id,
            ChatSession.card_id == card.id,
            ChatSession.visitor_id == visitor_id,
            ChatSession.is_test.is_(False),
        )
        return session.visit_id, session.campaign_id, session.source
    if visit_id is not None:
        visit = await repo.optional(
            db,
            Visit,
            Visit.id == visit_id,
            Visit.card_id == card.id,
            Visit.visitor_id == visitor_id,
        )
        if visit is not None:
            # A verified historical visit can convert after the event ends.
            return visit.id, visit.campaign_id, visit.source
    if campaign_id is not None:
        campaign = await repo.optional(db, Campaign, Campaign.id == campaign_id)
        if campaign is None or not live(campaign):
            campaign_id = None
    return None, campaign_id, source


async def report(db: AsyncSession, campaign_id: int) -> s.CampaignReport:
    await get(db, campaign_id)
    visits = list((await db.scalars(select(Visit).where(Visit.campaign_id == campaign_id))).all())
    sessions = list(
        (
            await db.scalars(
                select(ChatSession).where(
                    ChatSession.campaign_id == campaign_id,
                    ChatSession.is_test.is_(False),
                    ChatSession.rounds > 0,
                )
            )
        ).all()
    )
    leads = list((await db.scalars(select(Lead).where(Lead.campaign_id == campaign_id))).all())
    visitors = (
        {r.visitor_id for r in visits}
        | {r.visitor_id for r in sessions if r.visitor_id is not None}
        | {r.visitor_id for r in leads}
    )
    sources = sorted(
        {"nfc", "qr", "poster", "link", "sig"} | {r.source for r in visits + sessions + leads}
    )
    breakdown = []
    for source in sources:
        vv = [r for r in visits if r.source == source]
        cc = [r for r in sessions if r.source == source]
        ll = [r for r in leads if r.source == source]
        unique = (
            {r.visitor_id for r in vv}
            | {r.visitor_id for r in cc if r.visitor_id is not None}
            | {r.visitor_id for r in ll}
        )
        breakdown.append(
            s.SourceBreakdownRow(
                source=source,
                visits=len(vv),
                visitors=len(unique),
                chats=len(cc),
                leads=len({(r.card_id, r.visitor_id) for r in ll}),
            )
        )
    return s.CampaignReport(
        campaign_id=campaign_id,
        visits=len(visits),
        visitors=len(visitors),
        chats=len(sessions),
        leads=len({(r.card_id, r.visitor_id) for r in leads}),
        source_breakdown=breakdown,
    )
