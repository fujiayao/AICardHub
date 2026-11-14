from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode
from app.core.security import hash_password
from app.modules.workspace import repo
from app.modules.workspace import schemas as s
from app.modules.workspace import service as shared
from app.modules.workspace.models import (
    Assistant,
    AuditLog,
    Company,
    Employee,
    Issue,
    Lead,
    Notification,
    Product,
    Template,
)


async def company_update(
    db: AsyncSession, actor: Employee, payload: s.CompanyData
) -> s.CompanyData:
    row = await shared.primary_company(db)
    repo.assign(row, payload.model_dump())
    from app.modules.workspace.render_service import render_all

    await render_all(db)
    await shared.audit(db, actor.id, "company.update", str(row.id))
    await db.commit()
    return s.CompanyData.model_validate(row)


async def company_options(db: AsyncSession) -> list[s.CompanyOption]:
    primary = await shared.primary_company(db)
    rows = await repo.many(db, Company)
    return [
        s.CompanyOption(
            id=row.id,
            name=row.name,
            short_name=row.short_name,
            is_primary=row.id == primary.id,
        )
        for row in rows
    ]


async def company_create(
    db: AsyncSession, actor: Employee, payload: s.CompanyData
) -> s.CompanyItem:
    row = Company()
    repo.assign(row, payload.model_dump())
    db.add(row)
    await db.flush()
    await shared.audit(db, actor.id, "company.create", str(row.id))
    item = await shared.company_item(db, row)
    await db.commit()
    return item


async def company_item_get(db: AsyncSession, company_id: int) -> s.CompanyItem:
    row = await repo.one(db, Company, Company.id == company_id)
    return await shared.company_item(db, row)


async def company_item_update(
    db: AsyncSession, actor: Employee, company_id: int, payload: s.CompanyData
) -> s.CompanyItem:
    row = await repo.one(db, Company, Company.id == company_id)
    repo.assign(row, payload.model_dump())
    from app.modules.workspace.render_service import render_all

    if await shared.is_primary_company(db, row):
        await render_all(db)
    await shared.audit(db, actor.id, "company.update", str(row.id))
    item = await shared.company_item(db, row)
    await db.commit()
    return item


async def products(db: AsyncSession) -> list[s.ProductData]:
    return [s.ProductData.model_validate(row) for row in await repo.many(db, Product)]


async def product_save(
    db: AsyncSession, actor: Employee, payload: s.ProductInput, product_id: int | None = None
) -> s.ProductData:
    row = await repo.one(db, Product, Product.id == product_id) if product_id else Product()
    repo.assign(row, payload.model_dump())
    db.add(row)
    await db.flush()
    await shared.audit(db, actor.id, "product.save", str(row.id))
    await db.commit()
    return s.ProductData.model_validate(row)


async def product_delete(db: AsyncSession, actor: Employee, product_id: int) -> s.OK:
    row = await repo.one(db, Product, Product.id == product_id)
    await db.delete(row)
    await shared.audit(db, actor.id, "product.delete", str(product_id))
    await db.commit()
    return s.OK()


async def employees(db: AsyncSession, page: int, page_size: int, q: str = "") -> s.Page[s.Staff]:
    stmt = select(Employee).order_by(Employee.id.desc())
    if q:
        stmt = stmt.where(or_(Employee.name.contains(q), Employee.phone.contains(q)))
    result = await repo.page(db, stmt, page, page_size)
    result["items"] = [await shared.staff_data(db, row) for row in result["items"]]
    return s.Page[s.Staff](**result)


async def employee_create(db: AsyncSession, actor: Employee, payload: s.EmployeeInput) -> s.Staff:
    row = await shared.create_employee(db, payload)
    await shared.audit(db, actor.id, "employee.create", str(row.id))
    await db.commit()
    return await shared.staff_data(db, row)


async def employee_update(
    db: AsyncSession, actor: Employee, employee_id: int, payload: s.EmployeeUpdate
) -> s.Staff:
    row = await repo.one(db, Employee, Employee.id == employee_id)
    if row.id == actor.id and (payload.status == "disabled" or payload.role == "employee"):
        raise AppError(ErrorCode.FORBIDDEN, 403, "不能停用或移除自己的管理员身份")
    data = payload.model_dump(exclude_unset=True)
    previous_role = row.role
    effective_role = data.get("role") or row.role
    effective_phone = data.get("phone", row.phone)
    if effective_role == "admin" and not (effective_phone and row.password_hash):
        raise AppError(ErrorCode.FORBIDDEN, 403, "请先补充手机号并设置密码后再授予管理员身份")
    if "company_id" in data:
        row.company_id = await shared.resolve_company_id(db, data.pop("company_id"))
    if "phone" in data:
        new_phone = data.pop("phone")
        if new_phone is None:
            if effective_role == "admin":
                raise AppError(ErrorCode.FORBIDDEN, 403, "管理员不可清空手机号")
            if row.phone is not None:
                row.phone = None
                row.password_hash = None
                row.token_version += 1
        else:
            if new_phone != row.phone:
                row.token_version += 1
            row.phone = new_phone
    for key, value in data.items():
        if value is not None:
            setattr(row, key, value)
    if previous_role != row.role:
        row.token_version += 1
    card = await shared.own_card(db, row.id)
    card.status = row.status
    card.mobile = row.phone or ""
    from app.modules.workspace.render_service import render_card

    await render_card(db, card)
    await shared.audit(db, actor.id, "employee.update", str(row.id))
    await db.commit()
    return await shared.staff_data(db, row)


async def employee_reset(
    db: AsyncSession, actor: Employee, employee_id: int, payload: s.ResetPassword
) -> s.OK:
    row = await repo.one(db, Employee, Employee.id == employee_id)
    if row.phone is None:
        raise AppError(ErrorCode.CONFLICT, 409, "请先为该员工补充手机号后再设置密码")
    row.password_hash = await hash_password(payload.password)
    row.must_change_pwd = True
    row.token_version += 1
    row.failed_logins, row.locked_until = 0, None
    await shared.audit(db, actor.id, "employee.reset_password", str(row.id))
    await db.commit()
    return s.OK()


async def employee_disable(db: AsyncSession, actor: Employee, employee_id: int) -> s.OK:
    await employee_update(db, actor, employee_id, s.EmployeeUpdate(status="disabled"))
    return s.OK()


async def employee_transfer(
    db: AsyncSession, actor: Employee, employee_id: int, payload: s.TransferInput
) -> s.OK:
    if employee_id == actor.id or employee_id == payload.to_employee_id:
        raise AppError(ErrorCode.FORBIDDEN, 403, "不可转交自己或转交至同一员工")
    await repo.one(db, Employee, Employee.id == employee_id)
    target = await repo.one(
        db, Employee, Employee.id == payload.to_employee_id, Employee.status == "active"
    )
    from app.modules.workspace.models import CardAccessGrant

    card_ids = await shared.customer_card_ids(db, employee_id)
    for card_id in card_ids:
        grant = await repo.optional(db, CardAccessGrant, CardAccessGrant.card_id == card_id)
        if grant is None:
            db.add(CardAccessGrant(card_id=card_id, employee_id=target.id, operator_id=actor.id))
        else:
            grant.employee_id, grant.operator_id = target.id, actor.id
    await db.execute(
        update(Lead)
        .where(Lead.owner_employee_id == employee_id)
        .values(owner_employee_id=target.id)
    )
    await shared.audit(
        db, actor.id, "employee.transfer", str(employee_id), {"to_employee_id": target.id}
    )
    await db.commit()
    return s.OK()


async def templates(db: AsyncSession, only_enabled: bool = False) -> list[s.TemplateData]:
    rows = await repo.many(db, Template, *([Template.enabled.is_(True)] if only_enabled else []))
    return [s.TemplateData.model_validate(row) for row in rows]


async def template_save(
    db: AsyncSession, actor: Employee, payload: s.TemplateInput, template_id: int | None = None
) -> s.TemplateData:
    if payload.is_default and not payload.enabled:
        raise AppError(ErrorCode.VALIDATION_ERROR, 422, "默认模板必须启用")
    row = await repo.one(db, Template, Template.id == template_id) if template_id else Template()
    if payload.is_default:
        await db.execute(update(Template).values(is_default=False))
    repo.assign(row, payload.model_dump())
    db.add(row)
    await db.flush()
    from app.modules.workspace.render_service import render_all

    await render_all(db, row.id)
    await shared.audit(db, actor.id, "template.save", str(row.id))
    await db.commit()
    return s.TemplateData.model_validate(row)


async def template_default(db: AsyncSession, actor: Employee, template_id: int) -> s.TemplateData:
    row = await repo.one(db, Template, Template.id == template_id, Template.enabled.is_(True))
    await db.execute(update(Template).values(is_default=False))
    row.is_default = True
    await shared.audit(db, actor.id, "template.default", str(row.id))
    await db.commit()
    return s.TemplateData.model_validate(row)


async def template_delete(db: AsyncSession, actor: Employee, template_id: int) -> s.OK:
    row = await repo.one(db, Template, Template.id == template_id)
    if row.is_default:
        raise AppError(ErrorCode.CONFLICT, 409, "请先设置其他默认模板")
    await db.execute(
        update(Assistant).where(Assistant.template_id == row.id).values(template_id=None)
    )
    await db.delete(row)
    await shared.audit(db, actor.id, "template.delete", str(template_id))
    await db.commit()
    return s.OK()


async def issues(
    db: AsyncSession, page: int, page_size: int, status: str = ""
) -> s.Page[s.IssueData]:
    stmt = select(Issue).order_by(Issue.id.desc())
    if status:
        stmt = stmt.where(Issue.status == status)
    return s.Page[s.IssueData](**await repo.page(db, stmt, page, page_size))


async def issue_update(
    db: AsyncSession, actor: Employee, issue_id: int, payload: s.IssuePatch
) -> s.IssueData:
    row = await repo.one(db, Issue, Issue.id == issue_id)
    row.status = payload.status
    if row.employee_id:
        db.add(
            Notification(
                employee_id=row.employee_id,
                type="issue_done",
                title="问题处理进度更新",
                content=row.question,
                target_type="issue",
                target_id=row.id,
            )
        )
    await shared.audit(db, actor.id, "issue.update", str(row.id), payload.model_dump())
    await db.commit()
    return s.IssueData.model_validate(row)


async def setting_get(db: AsyncSession, key: str) -> s.SettingData:
    from app.modules.workspace.runtime_settings import get_value

    return s.SettingData(key=key, value=await get_value(db, key))


async def setting_update(
    db: AsyncSession, actor: Employee, key: str, payload: s.SettingInput
) -> s.SettingData:
    from app.modules.workspace.runtime_settings import save

    value = await save(db, actor, key, payload.value, clear_secret=payload.clear_secret)
    return s.SettingData(key=key, value=value)


async def audit_logs(db: AsyncSession, page: int, page_size: int) -> s.Page[s.AuditData]:
    return s.Page[s.AuditData](
        **await repo.page(db, select(AuditLog).order_by(AuditLog.id.desc()), page, page_size)
    )


async def broadcast(db: AsyncSession, actor: Employee, payload: s.BroadcastInput) -> s.OK:
    rows = await repo.many(db, Employee, Employee.status == "active")
    for row in rows:
        if payload.employee_ids is None or row.id in payload.employee_ids:
            db.add(Notification(employee_id=row.id, title=payload.title, content=payload.content))
    await shared.audit(db, actor.id, "notification.broadcast", "employees")
    await db.commit()
    return s.OK()
