from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.errors import AppError, ErrorCode
from app.core.security import decode_token
from app.modules.workspace import repo
from app.modules.workspace.models import Employee, Visitor

bearer = HTTPBearer(auto_error=False)
DB = Annotated[AsyncSession, Depends(get_db, scope="function")]
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]


def required_token(credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is None:
        raise AppError(ErrorCode.AUTH_REQUIRED, 401, "请先登录")
    return credentials.credentials


async def get_current_staff(request: Request, db: DB, credentials: Credentials) -> Employee:
    payload = decode_token(required_token(credentials), "staff")
    employee = await repo.optional(db, Employee, Employee.id == int(str(payload["sub"])))
    if employee is None or employee.status != "active":
        raise AppError(ErrorCode.AUTH_DISABLED, 401, "账号已停用")
    if not (employee.phone and employee.password_hash):
        raise AppError(ErrorCode.AUTH_INVALID, 401, "账号或密码错误")
    if payload.get("version") != employee.token_version:
        raise AppError(ErrorCode.AUTH_REQUIRED, 401, "请重新登录")
    allowed = ("/api/v1/me/profile", "/api/v1/auth/change-password")
    if employee.must_change_pwd and request.url.path not in allowed:
        raise AppError(ErrorCode.PASSWORD_CHANGE_REQUIRED, 403, "请先修改初始密码")
    return employee


StaffDep = Annotated[Employee, Depends(get_current_staff)]


async def get_current_admin(staff: StaffDep) -> Employee:
    if staff.role != "admin":
        raise AppError(ErrorCode.FORBIDDEN, 403, "需要管理员身份")
    return staff


AdminDep = Annotated[Employee, Depends(get_current_admin)]


async def get_visitor(db: DB, credentials: Credentials) -> Visitor:
    payload = decode_token(required_token(credentials), "visitor")
    visitor = await repo.optional(db, Visitor, Visitor.anon_id == str(payload["sub"]))
    if visitor is None:
        raise AppError(ErrorCode.AUTH_REQUIRED, 401, "访客身份已失效")
    return visitor


VisitorDep = Annotated[Visitor, Depends(get_visitor)]
