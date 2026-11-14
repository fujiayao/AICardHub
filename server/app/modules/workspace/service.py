from datetime import timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import utcnow
from app.core.errors import AppError, ErrorCode
from app.core.security import hash_password, issue_token, verify_password
from app.modules.workspace import repo
from app.modules.workspace import schemas as s
from app.modules.workspace.models import (
    Assistant,
    AuditLog,
    Card,
    Company,
    Employee,
    Product,
    Template,
    Visit,
    Visitor,
)


async def primary_company(db: AsyncSession) -> Company:
    """The primary company is fixed as the original lowest id row."""
    from sqlalchemy import select

    row = await db.scalar(select(Company).order_by(Company.id).limit(1))
    if row is None:
        raise AppError(ErrorCode.NOT_FOUND, 404, "企业信息未配置")
    return row


async def employee_company(db: AsyncSession, employee: Employee) -> Company:
    return await repo.one(db, Company, Company.id == employee.company_id)


async def is_primary_company(db: AsyncSession, company: Company) -> bool:
    return company.id == (await primary_company(db)).id


async def company_item(db: AsyncSession, company: Company) -> s.CompanyItem:
    return s.CompanyItem(
        **s.CompanyData.model_validate(company).model_dump(),
        id=company.id,
        is_primary=await is_primary_company(db, company),
    )


def login_enabled(employee: Employee) -> bool:
    return bool(employee.phone and employee.password_hash)


async def staff_data(db: AsyncSession, employee: Employee) -> s.Staff:
    result = s.Staff.model_validate(employee, from_attributes=True)
    card = await repo.optional(db, Card, Card.employee_id == employee.id)
    result.card_code = card.code if card else ""
    company = await employee_company(db, employee)
    result.company_id, result.company_name = company.id, company.name
    result.login_enabled = login_enabled(employee)
    return result


async def login(db: AsyncSession, payload: s.LoginInput, admin: bool = False) -> s.LoginResult:
    employee = await repo.optional(db, Employee, Employee.phone == payload.phone)
    if employee is None or employee.password_hash is None:
        raise AppError(ErrorCode.AUTH_INVALID, 401, "账号或密码错误")
    if employee.status != "active":
        raise AppError(ErrorCode.AUTH_DISABLED, 401, "账号已停用")
    if employee.locked_until and employee.locked_until > utcnow():
        raise AppError(ErrorCode.AUTH_LOCKED, 423, "账号暂时锁定，请15分钟后重试")
    if not await verify_password(payload.password, employee.password_hash):
        employee.failed_logins += 1
        if employee.failed_logins >= 5:
            employee.locked_until = utcnow() + timedelta(minutes=15)
            employee.failed_logins = 0
        await db.commit()
        raise AppError(
            ErrorCode.AUTH_INVALID,
            401,
            f"账号或密码错误，剩余{max(0, 5 - employee.failed_logins)}次",
        )
    if admin and employee.role != "admin":
        raise AppError(ErrorCode.FORBIDDEN, 403, "需要管理员身份")
    employee.failed_logins = 0
    employee.locked_until = None
    await db.commit()
    return s.LoginResult(
        token=issue_token(str(employee.id), "staff", employee.role, employee.token_version),
        must_change_pwd=employee.must_change_pwd,
        staff=await staff_data(db, employee),
    )


async def change_password(db: AsyncSession, employee: Employee, payload: s.PasswordInput) -> s.OK:
    if employee.password_hash is None or not await verify_password(
        payload.old_password, employee.password_hash
    ):
        raise AppError(ErrorCode.AUTH_INVALID, 400, "原密码不正确")
    employee.password_hash = await hash_password(payload.new_password)
    employee.must_change_pwd = False
    employee.token_version += 1
    await db.commit()
    return s.OK()


async def own_card(db: AsyncSession, employee_id: int) -> Card:
    return await repo.one(db, Card, Card.employee_id == employee_id, code=ErrorCode.CARD_NOT_FOUND)


async def by_code(db: AsyncSession, code: str, active: bool = False) -> Card:
    card = await repo.one(db, Card, Card.code == code, code=ErrorCode.CARD_NOT_FOUND)
    if active:
        employee = await repo.one(db, Employee, Employee.id == card.employee_id)
        if card.status != "active" or employee.status != "active":
            raise AppError(ErrorCode.CARD_DISABLED, 409, "该名片已停用，请联系公司")
    return card


async def company_get(db: AsyncSession) -> s.CompanyData:
    return s.CompanyData.model_validate(await primary_company(db))


async def public_card(db: AsyncSession, code: str, campaign_id: int | None = None) -> s.PublicCard:
    card = await by_code(db, code)
    employee = await repo.one(db, Employee, Employee.id == card.employee_id)
    company_row = await employee_company(db, employee)
    company = s.CompanyData.model_validate(company_row)
    if card.status != "active" or employee.status != "active":
        return s.PublicCard(code=card.code, status="disabled", company=company)
    assistant = await repo.one(db, Assistant, Assistant.card_id == card.id)
    primary = await primary_company(db)
    campaign = None
    if campaign_id is not None:
        from app.modules.workspace import campaign_service

        campaign = await campaign_service.get(db, campaign_id, public=True)
    public_assistant = s.PublicAssistant.model_validate(assistant)
    if campaign is not None:
        public_assistant.opening = campaign.opening_override or public_assistant.opening
        public_assistant.guide_questions = (
            campaign.guide_override[:3] or public_assistant.guide_questions
        )
    products = (
        await repo.many(db, Product, Product.enabled.is_(True))
        if company_row.id == primary.id
        else []
    )
    return s.PublicCard(
        code=card.code,
        status="active",
        name=employee.name,
        dept=employee.dept,
        title=card.display_title or employee.title,
        photo_url=card.photo_url,
        photo_bg_url=card.photo_bg_url,
        mobile=card.mobile,
        email=card.email,
        intro=card.intro,
        business_scope=employee.business_scope,
        wechat_qr_url=card.wechat_qr_url,
        company=company,
        products=[s.ProductData.model_validate(p) for p in sorted(products, key=lambda p: p.sort)],
        assistant=public_assistant,
        campaign=s.PublicCampaign.model_validate(campaign) if campaign else None,
    )


async def card_data(db: AsyncSession, card: Card) -> s.CardData:
    employee = await repo.one(db, Employee, Employee.id == card.employee_id)
    result = s.CardData.model_validate(card)
    result.name, result.dept, result.title = employee.name, employee.dept, employee.title
    return result


async def update_card(db: AsyncSession, card: Card, payload: s.CardInput) -> s.CardData:
    repo.assign(card, payload.model_dump(exclude_none=True))
    from app.modules.workspace.render_service import enqueue_card

    await enqueue_card(db, card)
    await db.commit()
    return await card_data(db, card)


async def assistant_get(db: AsyncSession, card: Card) -> Assistant:
    return await repo.one(db, Assistant, Assistant.card_id == card.id)


async def assistant_update(
    db: AsyncSession, card: Card, payload: s.AssistantInput
) -> s.AssistantData:
    if payload.template_id is not None:
        await repo.one(db, Template, Template.id == payload.template_id, Template.enabled.is_(True))
    assistant = await assistant_get(db, card)
    repo.assign(assistant, payload.model_dump())
    from app.modules.workspace.render_service import enqueue_card

    await enqueue_card(db, card)
    await db.commit()
    return s.AssistantData.model_validate(assistant)


def render(text: str, employee: Employee, company: Company) -> str:
    for key, value in {
        "姓名": employee.name,
        "职位": employee.title,
        "部门": employee.dept,
        "公司简称": company.short_name,
        "负责业务": employee.business_scope,
    }.items():
        text = text.replace("{" + key + "}", value)
    return text


async def resolve_company_id(db: AsyncSession, company_id: int | None) -> int:
    if company_id is None:
        return (await primary_company(db)).id
    return (await repo.one(db, Company, Company.id == company_id)).id


async def create_employee(
    db: AsyncSession, payload: s.EmployeeInput, *, code: str | None = None, must_change: bool = True
) -> Employee:
    values = payload.model_dump(exclude={"password", "company_id"})
    values["company_id"] = await resolve_company_id(db, payload.company_id)
    password_hash = await hash_password(payload.password) if payload.password else None
    employee = Employee(**values, password_hash=password_hash, must_change_pwd=must_change)
    db.add(employee)
    await db.flush()
    card = Card(
        code=code or uuid4().hex[:8],
        employee_id=employee.id,
        display_title=employee.title,
        mobile=employee.phone or "",
        email=employee.email,
    )
    db.add(card)
    await db.flush()
    template = await repo.optional(
        db, Template, Template.is_default.is_(True), Template.enabled.is_(True)
    )
    company = await employee_company(db, employee)
    db.add(
        Assistant(
            card_id=card.id,
            template_id=template.id if template else None,
            opening=render(template.opening, employee, company)
            if template
            else "您好，请问有什么可以帮助您？",
            guide_questions=[render(q, employee, company) for q in template.guide_questions[:3]]
            if template
            else [],
        )
    )
    await db.flush()
    from app.modules.workspace.render_service import enqueue_card

    await enqueue_card(db, card)
    return employee


async def audit(
    db: AsyncSession,
    operator_id: int,
    action: str,
    target: str,
    detail: dict[str, Any] | None = None,
) -> None:
    db.add(AuditLog(operator_id=operator_id, action=action, target=target, detail=detail or {}))


async def init_visitor(db: AsyncSession, token: str | None) -> s.VisitorInit:
    from app.core.security import decode_token

    if token:
        payload = decode_token(token, "visitor")
        visitor = await repo.optional(db, Visitor, Visitor.anon_id == str(payload["sub"]))
        if visitor is None:
            raise AppError(ErrorCode.AUTH_REQUIRED, 401, "访客身份已失效，请重新初始化")
        visitor.last_seen_at = utcnow()
    else:
        visitor = Visitor(anon_id=str(uuid4()))
        db.add(visitor)
    await db.commit()
    return s.VisitorInit(
        anon_id=visitor.anon_id, visitor_token=issue_token(visitor.anon_id, "visitor")
    )


async def create_visit(db: AsyncSession, visitor: Visitor, payload: s.VisitInput) -> s.VisitResult:
    card = await by_code(db, payload.card_code, active=True)
    if payload.campaign_id is not None:
        from app.modules.workspace.campaign_service import get

        await get(db, payload.campaign_id, public=True)
    visit = Visit(
        card_id=card.id,
        visitor_id=visitor.id,
        source=payload.source,
        campaign_id=payload.campaign_id,
    )
    visitor.last_seen_at = utcnow()
    db.add(visit)
    await db.commit()
    return s.VisitResult(visit_id=visit.id, campaign_id=visit.campaign_id)


async def update_visit(
    db: AsyncSession, visitor: Visitor, visit_id: int, payload: s.StayInput
) -> s.OK:
    visit = await repo.one(db, Visit, Visit.id == visit_id, Visit.visitor_id == visitor.id)
    visit.stay_seconds = max(visit.stay_seconds, payload.stay_seconds)
    await db.commit()
    return s.OK()


async def customer_card_ids(db: AsyncSession, employee_id: int) -> list[int]:
    from sqlalchemy import select

    from app.modules.workspace.models import CardAccessGrant

    owned = select(Card.id).where(
        Card.employee_id == employee_id, ~Card.id.in_(select(CardAccessGrant.card_id))
    )
    transferred = select(CardAccessGrant.card_id).where(CardAccessGrant.employee_id == employee_id)
    return list((await db.scalars(owned.union(transferred))).all())


async def lead_owner(db: AsyncSession, card: Card) -> int:
    from app.modules.workspace.models import CardAccessGrant

    grant = await repo.optional(db, CardAccessGrant, CardAccessGrant.card_id == card.id)
    return grant.employee_id if grant else card.employee_id
