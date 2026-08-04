import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(
    name="app.tasks.inventory_tasks.check_low_stock",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def check_low_stock(self):
    """
    Check inventory records against reorder_point thresholds.
    Create LOW_STOCK notifications for products at or below reorder point.
    """
    from sqlalchemy import select

    from app.database import async_session
    from app.models.inventory import Inventory
    from app.models.notification import Notification
    from app.models.product import Product
    from app.models.user import User

    async def _check():
        alerted = 0
        async with async_session() as db:
            result = await db.execute(
                select(Inventory, Product, User)
                .join(Product, Product.id == Inventory.product_id)
                .join(User, User.id == Product.user_id)
                .where(
                    Inventory.reorder_point != None,  # noqa: E711
                    Product.is_active == True,  # noqa: E712
                )
            )
            rows = result.all()

            for inv, product, user in rows:
                available = inv.quantity_available - inv.quantity_reserved
                if available <= inv.reorder_point:
                    notif = Notification(
                        user_id=user.id,
                        type="LOW_STOCK",
                        title="Low Stock Alert",
                        message=(
                            f"{product.title} (SKU: {product.sku}) is low: "
                            f"{available} units available (reorder point: {inv.reorder_point})"
                        ),
                        severity="WARNING",
                        related_entity_type="product",
                        related_entity_id=product.id,
                    )
                    db.add(notif)
                    alerted += 1
                    logger.info(
                        "Low stock alert: %s (SKU %s) — %d available",
                        product.title, product.sku, available,
                    )

            await db.commit()
        return {"alerted": alerted}

    try:
        result = _run(_check())
        logger.info("Low stock check complete: %s", result)
        return result
    except Exception as exc:
        logger.error("Low stock check failed: %s", exc)
        raise self.retry(exc=exc)
