"""Real MySQL checks for phone changes and administrator credential prerequisites."""

from uuid import uuid4

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import delete
from starlette.requests import Request

from app.core.deps import get_current_staff
from app.core.errors import AppError
from app.core.security import issue_token
from app.modules.workspace import admin_service as admin
from app.modules.workspace import schemas as s
from app.modules.workspace import service as shared
from app.modules.workspace.models import Assistant, AuditLog, Card, Employee

pytest_plugins = ["test_backend_isolation"]


def synthetic_phone():
    return "138" + str(uuid4().int)[-8:]


async def test_更换手机号使旧token失效而重复保存相同手机号不撤销(db, employees):
    actor, employee, _ = employees
    old_version = employee.token_version
    token = issue_token(str(employee.id), "staff", employee.role, old_version)
    phone = synthetic_phone()
    changed = await admin.employee_update(db, actor, employee.id, s.EmployeeUpdate(phone=phone))
    assert changed.login_enabled
    assert employee.token_version == old_version + 1
    request = Request({"type": "http", "path": "/api/v1/me/profile"})
    with pytest.raises(AppError) as error:
        await get_current_staff(
            request, db, HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        )
    assert error.value.status == 401
    await admin.employee_update(db, actor, employee.id, s.EmployeeUpdate(phone=phone))
    assert employee.token_version == old_version + 1


async def test_无凭据员工补手机再设密码后才可提升管理员(db, employees):
    actor, _, _ = employees
    employee = await shared.create_employee(db, s.EmployeeInput(name="合成任职凭据测试"))
    await db.commit()
    employee_id = employee.id
    card = await shared.own_card(db, employee_id)
    card_id = card.id
    try:
        assert employee.phone is None and employee.password_hash is None
        with pytest.raises(AppError) as error:
            await admin.employee_update(db, actor, employee_id, s.EmployeeUpdate(role="admin"))
        assert error.value.status == 403
        assert employee.role == "employee"
        phone = synthetic_phone()
        with pytest.raises(AppError):
            await admin.employee_update(
                db, actor, employee_id, s.EmployeeUpdate(phone=phone, role="admin")
            )
        assert employee.phone is None and employee.role == "employee"
        result = await admin.employee_update(db, actor, employee_id, s.EmployeeUpdate(phone=phone))
        assert not result.login_enabled and employee.password_hash is None
        with pytest.raises(AppError):
            await admin.employee_update(db, actor, employee_id, s.EmployeeUpdate(role="admin"))
        await admin.employee_reset(
            db, actor, employee_id, s.ResetPassword(password="SyntheticTest42")
        )
        result = await admin.employee_update(db, actor, employee_id, s.EmployeeUpdate(role="admin"))
        assert result.login_enabled and result.role == "admin"
    finally:
        await db.commit()
        await db.execute(delete(AuditLog).where(AuditLog.target == str(employee_id)))
        await db.execute(delete(Assistant).where(Assistant.card_id == card_id))
        await db.execute(delete(Card).where(Card.id == card_id))
        await db.execute(delete(Employee).where(Employee.id == employee_id))
        await db.commit()
