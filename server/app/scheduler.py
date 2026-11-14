"""Run with python -m app.scheduler; never imported by the API startup."""

import asyncio
from collections.abc import Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SessionLocal, engine
from app.jobs import tasks


async def guarded(name: str, job: Callable[[AsyncSession], Awaitable[object]]) -> None:
    # Connection-owned MySQL lock survives session commits and excludes accidental
    # duplicate scheduler processes. Job sessions release their separate connection
    # before provider calls; the scheduler owns only this one advisory-lock connection.
    async with engine.connect() as connection:
        lock_name = f"aicardhub-job-{name}"
        acquired = await connection.scalar(text("SELECT GET_LOCK(:name, 0)"), {"name": lock_name})
        await connection.commit()
        if acquired != 1:
            return
        try:
            async with SessionLocal() as db:
                await job(db)
        except Exception as exc:
            logger.error("Scheduled job failed job={} type={}", name, type(exc).__name__)
        finally:
            await connection.execute(text("SELECT RELEASE_LOCK(:name)"), {"name": lock_name})
            await connection.commit()


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
    for name, function, interval in [
        ("sessions", tasks.end_sessions, 60),
        ("render", tasks.render_pending, 15),
        ("overdue", tasks.overdue_reminders, 3600),
    ]:
        scheduler.add_job(
            guarded,
            "interval",
            seconds=interval,
            args=[name, function],
            id=name,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60,
        )
    scheduler.add_job(
        guarded,
        CronTrigger(hour=9, minute=0, timezone="Asia/Shanghai"),
        args=["digest", tasks.daily_digest],
        id="digest",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        guarded,
        CronTrigger(hour=3, minute=0, timezone="Asia/Shanghai"),
        args=["cleanup", tasks.cleanup],
        id="cleanup",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    return scheduler


async def main() -> None:
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("Independent scheduler started")
    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown(wait=True)
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")
