from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode
from app.modules.workspace.models import RateCounter


async def hit(db: AsyncSession, key: str, window: str, limit: int) -> None:
    stmt = insert(RateCounter).values(key=key, window=window, count=1)
    await db.execute(stmt.on_duplicate_key_update(count=RateCounter.count + 1))
    count = await db.scalar(
        select(RateCounter.count).where(RateCounter.key == key, RateCounter.window == window)
    )
    if count is not None and count > limit:
        await db.commit()
        raise AppError(ErrorCode.RATE_LIMITED, 429, "今日对话额度已用完，请直接联系员工")
