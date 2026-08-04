import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(
    name="app.tasks.aliexpress_sync.sync_tracking",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def sync_tracking(self):
    """Poll AliExpress for tracking updates on all forwarded orders."""
    from sqlalchemy import select

    from app.database import async_session
    from app.models.order import Order
    from app.services.aliexpress_service import sync_tracking_for_order

    async def _sync():
        synced = 0
        failed = 0
        async with async_session() as db:
            result = await db.execute(
                select(Order).where(
                    Order.aliexpress_order_id != None,  # noqa: E711
                    Order.aliexpress_tracking_number == None,  # noqa: E711
                    Order.order_status.in_(["IN_PROGRESS", "FULFILLED"]),
                )
            )
            orders = result.scalars().all()

            for order in orders:
                try:
                    tracking = await sync_tracking_for_order(order, db)
                    if tracking:
                        synced += 1
                        logger.info("Synced tracking for order %s: %s", order.id, tracking)
                except Exception as exc:
                    failed += 1
                    logger.error("Tracking sync failed for order %s: %s", order.id, exc)

            await db.commit()
        return {"synced": synced, "failed": failed}

    try:
        result = _run(_sync())
        logger.info("Tracking sync complete: %s", result)
        return result
    except Exception as exc:
        logger.error("Tracking sync task failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.tasks.aliexpress_sync.forward_order",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def forward_order(self, order_id: str, sku_id: str | None = None):
    """Forward an eBay order to AliExpress for fulfillment."""
    import uuid as _uuid

    from sqlalchemy import select

    from app.database import async_session
    from app.models.order import Order
    from app.services.aliexpress_service import forward_order_to_aliexpress
    from app.exceptions import AliExpressAPIError

    async def _forward():
        async with async_session() as db:
            result = await db.execute(
                select(Order).where(Order.id == _uuid.UUID(order_id))
            )
            order = result.scalar_one_or_none()
            if not order:
                logger.error("forward_order: order %s not found", order_id)
                return {"error": "order not found"}

            try:
                ae_order_id = await forward_order_to_aliexpress(
                    order=order,
                    db=db,
                    sku_id=sku_id,
                )
                await db.commit()
                return {"aliexpress_order_id": ae_order_id}
            except AliExpressAPIError as exc:
                logger.error("Order forwarding failed for %s: %s", order_id, exc)
                if exc.is_transient:
                    raise  # will be caught below and retried
                return {"error": str(exc)}

    try:
        return _run(_forward())
    except AliExpressAPIError as exc:
        if exc.is_transient:
            raise self.retry(exc=exc)
        logger.error("Non-retryable forwarding error for %s: %s", order_id, exc)
        return {"error": str(exc)}
    except Exception as exc:
        logger.error("Unexpected forwarding error for %s: %s", order_id, exc)
        raise self.retry(exc=exc)
