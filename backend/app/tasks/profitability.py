import asyncio

from sqlalchemy import select

from app.database import async_session
from app.models.user import User
from app.services.profitability_service import recalculate_for_user
from app.tasks.celery_app import celery_app


async def _run_recalculate_all() -> dict:
    stats = {"users": 0, "records": 0, "errors": 0}

    async with async_session() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()

        for user in users:
            stats["users"] += 1
            try:
                count = await recalculate_for_user(db, user.id)
                stats["records"] += count
            except Exception:
                stats["errors"] += 1

        await db.commit()

    return stats


@celery_app.task(name="app.tasks.profitability.recalculate_all", bind=True, max_retries=2)
def recalculate_all(self):
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_run_recalculate_all())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)
