import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run(coro):
    """Run an async coroutine from a synchronous Celery task."""
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(
    name="app.tasks.ebay_sync.sync_orders",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def sync_orders(self):
    """Pull new/updated orders from eBay Fulfillment API for all active users."""
    from sqlalchemy import select

    from app.database import async_session
    from app.models.ebay_credential import EbayCredential
    from app.services.order_service import sync_orders_for_user

    async def _sync():
        async with async_session() as db:
            result = await db.execute(
                select(EbayCredential.user_id).where(EbayCredential.is_active == True).distinct()
            )
            user_ids = result.scalars().all()

        totals = {"created": 0, "updated": 0, "total_fetched": 0}
        for user_id in user_ids:
            async with async_session() as db:
                try:
                    counts = await sync_orders_for_user(db, user_id)
                    for k in totals:
                        totals[k] += counts.get(k, 0)
                    logger.info("Order sync for user %s: %s", user_id, counts)
                except Exception as exc:
                    logger.error("Order sync failed for user %s: %s", user_id, exc)
        return totals

    try:
        result = _run(_sync())
        logger.info("sync_orders complete: %s", result)
        return result
    except Exception as exc:
        logger.error("sync_orders task error: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.tasks.ebay_sync.sync_listings",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
)
def sync_listings(self):
    """Sync listing statuses from eBay for all active users."""
    from sqlalchemy import select

    from app.database import async_session
    from app.models.ebay_credential import EbayCredential
    from app.services.listing_service import sync_listings_for_user

    async def _sync():
        async with async_session() as db:
            result = await db.execute(
                select(EbayCredential.user_id).where(EbayCredential.is_active == True).distinct()
            )
            user_ids = result.scalars().all()

        total_synced = 0
        for user_id in user_ids:
            async with async_session() as db:
                try:
                    counts = await sync_listings_for_user(db, user_id)
                    total_synced += counts.get("synced", 0)
                    logger.info("Listing sync for user %s: %s", user_id, counts)
                except Exception as exc:
                    logger.error("Listing sync failed for user %s: %s", user_id, exc)
        return {"synced": total_synced}

    try:
        result = _run(_sync())
        logger.info("sync_listings complete: %s", result)
        return result
    except Exception as exc:
        logger.error("sync_listings task error: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(name="app.tasks.ebay_sync.sync_messages")
def sync_messages():
    """Pull buyer messages from eBay — Phase 6."""
    pass


@celery_app.task(name="app.tasks.ebay_sync.sync_returns")
def sync_returns():
    """Pull return/refund updates from eBay — Phase 6."""
    pass
