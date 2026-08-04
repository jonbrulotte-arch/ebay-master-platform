import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(
    name="app.tasks.supplier_monitoring.check_supplier_prices",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def check_supplier_prices(self):
    """
    For every active AliExpress product_supplier, fetch current price and
    notify the owning user if it changed more than 5%.
    """
    from sqlalchemy import select

    from app.database import async_session
    from app.models.product_supplier import ProductSupplier
    from app.models.supplier import Supplier
    from app.models.user import User
    from app.services.aliexpress_service import check_supplier_price

    async def _check():
        checked = 0
        changed = 0
        async with async_session() as db:
            result = await db.execute(
                select(ProductSupplier, Supplier, User)
                .join(Supplier, Supplier.id == ProductSupplier.supplier_id)
                .join(User, User.id == Supplier.user_id)
                .where(
                    Supplier.platform == "ALIEXPRESS",
                    Supplier.is_active == True,  # noqa: E712
                    ProductSupplier.supplier_product_id != None,  # noqa: E711
                )
            )
            rows = result.all()

            for ps, supplier, user in rows:
                try:
                    price_result = await check_supplier_price(
                        product_supplier=ps,
                        db=db,
                        notify_user_id=user.id,
                    )
                    checked += 1
                    if price_result.changed:
                        changed += 1
                        logger.info(
                            "Price changed for AE product %s: $%.2f → $%.2f (%.1f%%)",
                            ps.supplier_product_id,
                            price_result.old_price,
                            price_result.new_price,
                            price_result.change_pct,
                        )
                except Exception as exc:
                    logger.error(
                        "Price check failed for product_supplier %s: %s", ps.id, exc
                    )

            await db.commit()
        return {"checked": checked, "changed": changed}

    try:
        result = _run(_check())
        logger.info("Supplier price check complete: %s", result)
        return result
    except Exception as exc:
        logger.error("Supplier price check task failed: %s", exc)
        raise self.retry(exc=exc)
