import base64
import hashlib
from typing import Any

from cryptography.fernet import Fernet
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
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
    Setting,
    Template,
)


async def company_update(
    db: AsyncSession, actor: Employee, payload: s.CompanyData
) -> s.CompanyData:
    row = await repo.one(db, Company)
    repo.assign(row, payload.model_dump())
    await shared.audit(db, actor.id, "company.update", str(row.id))
    await db.commit()
    return s.CompanyData.model_validate(row)


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
    previous_role = row.role
    repo.assign(row, payload.model_dump(exclude_none=True))
    if previous_role != row.role:
        row.token_version += 1
    card = await shared.own_card(db, row.id)
    card.status = row.status
    await shared.audit(db, actor.id, "employee.update", str(row.id))
    await db.commit()
    return await shared.staff_data(db, row)


async def employee_reset(
    db: AsyncSession, actor: Employee, employee_id: int, payload: s.ResetPassword
) -> s.OK:
    row = await repo.one(db, Employee, Employee.id == employee_id)
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


def cipher() -> Fernet:
    key = hashlib.sha256(get_settings().jwt_secret.get_secret_value().encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def secret_key(key: str) -> bool:
    return any(word in key.lower() for word in ("api_key", "secret", "password", "token"))


async def setting_get(db: AsyncSession, key: str, *, private: bool = False) -> s.SettingData:
    row = await repo.optional(db, Setting, Setting.key == key)
    value: Any = row.value if row else None
    if secret_key(key) and value:
        value = cipher().decrypt(str(value).encode()).decode() if private else "********"
    return s.SettingData(key=key, value=value)


async def setting_update(
    db: AsyncSession, actor: Employee, key: str, payload: s.SettingInput
) -> s.SettingData:
    if len(key) > 100:
        raise AppError(ErrorCode.VALIDATION_ERROR, 422)
    row = await repo.optional(db, Setting, Setting.key == key)
    value = payload.value
    if secret_key(key):
        if not isinstance(value, str):
            raise AppError(ErrorCode.VALIDATION_ERROR, 422, "密钥必须为文本")
        value = cipher().encrypt(value.encode()).decode()
    elif isinstance(value, (dict, list)) and any(
        word in str(value).lower() for word in ("api_key", "password", "secret")
    ):
        raise AppError(ErrorCode.VALIDATION_ERROR, 422, "密钥请使用独立设置项")
    if row is None:
        row = Setting(key=key, value=value)
        db.add(row)
    else:
        row.value = value
    await shared.audit(db, actor.id, "setting.update", key)
    await db.commit()
    return await setting_get(db, key)


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
