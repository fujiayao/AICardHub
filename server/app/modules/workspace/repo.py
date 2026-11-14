from collections.abc import Sequence
from typing import Any, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.core.db import Entity
from app.core.errors import AppError, ErrorCode

T = TypeVar("T", bound=Entity)


async def one[T: Entity](
    db: AsyncSession,
    model: type[T],
    *where: ColumnElement[bool],
    code: ErrorCode = ErrorCode.NOT_FOUND,
    lock: bool = False,
) -> T:
    stmt = select(model).where(*where)
    if lock:
        stmt = stmt.with_for_update()
    result = await db.scalar(stmt)
    if result is None:
        raise AppError(code, 404, "记录不存在或无权访问")
    return result


async def optional[T: Entity](
    db: AsyncSession, model: type[T], *where: ColumnElement[bool]
) -> T | None:
    return (await db.scalars(select(model).where(*where))).first()


async def many[T: Entity](
    db: AsyncSession, model: type[T], *where: ColumnElement[bool]
) -> Sequence[T]:
    return (await db.scalars(select(model).where(*where).order_by(model.id))).all()


async def page[T: Entity](
    db: AsyncSession, stmt: Select[tuple[T]], page: int, page_size: int
) -> dict[str, Any]:
    total = await db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    items = (await db.scalars(stmt.limit(page_size).offset((page - 1) * page_size))).all()
    return {"items": list(items), "total": total or 0, "page": page, "page_size": page_size}


def assign(row: Entity, values: dict[str, Any]) -> None:
    for key, value in values.items():
        setattr(row, key, value)
