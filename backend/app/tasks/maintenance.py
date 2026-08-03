import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(
    name="app.tasks.maintenance.refresh_tokens",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def refresh_tokens(self):
    """Refresh eBay OAuth tokens expiring within 1 hour."""
    from app.database import async_session
    from app.services.ebay_service import refresh_all_expiring_tokens

    async def _refresh():
        async with async_session() as db:
            return await refresh_all_expiring_tokens(db)

    try:
        result = _run(_refresh())
        logger.info("Token refresh complete: %s", result)
        return result
    except Exception as exc:
        logger.error("Token refresh failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(name="app.tasks.maintenance.generate_daily_summary")
def generate_daily_summary():
    """Create daily sales/profit summary notification — Phase 4."""
    pass
