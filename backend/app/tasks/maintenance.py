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


@celery_app.task(name="app.tasks.maintenance.generate_daily_summary", bind=True, max_retries=2)
def generate_daily_summary(self):
    """Create a daily sales/profit summary notification for each user."""
    from datetime import date, timedelta

    from sqlalchemy import text

    from app.database import async_session
    from app.models.notification import Notification
    from app.models.user import User

    async def _run():
        async with async_session() as db:
            from sqlalchemy import select
            result = await db.execute(select(User))
            users = result.scalars().all()

            yesterday = date.today() - timedelta(days=1)
            from_dt = f"{yesterday}T00:00:00+00:00"
            to_dt = f"{yesterday}T23:59:59+00:00"

            for user in users:
                row = (
                    await db.execute(
                        text("""
                            SELECT
                                COUNT(DISTINCT o.id)              AS order_count,
                                COALESCE(SUM(o.total_amount), 0)  AS gross_revenue,
                                COALESCE(SUM(pr.gross_profit), 0) AS net_profit,
                                COALESCE(AVG(pr.profit_margin_pct), 0) AS avg_margin
                            FROM orders o
                            LEFT JOIN order_line_items oli ON oli.order_id = o.id
                            LEFT JOIN profitability_records pr
                                ON pr.order_line_item_id = oli.id AND pr.record_type = 'ACTUAL'
                            WHERE o.user_id = :uid
                              AND o.order_status != 'CANCELLED'
                              AND o.paid_at >= :from_dt
                              AND o.paid_at <= :to_dt
                        """),
                        {"uid": str(user.id), "from_dt": from_dt, "to_dt": to_dt},
                    )
                ).mappings().one()

                orders = int(row["order_count"] or 0)
                revenue = float(row["gross_revenue"] or 0)
                profit = float(row["net_profit"] or 0)
                margin = float(row["avg_margin"] or 0)

                if orders == 0:
                    message = f"No orders on {yesterday}."
                else:
                    message = (
                        f"{yesterday}: {orders} order{'s' if orders != 1 else ''} · "
                        f"${revenue:.2f} revenue · ${profit:.2f} profit ({margin:.1f}% margin)"
                    )

                notification = Notification(
                    user_id=user.id,
                    type="DAILY_SUMMARY",
                    title=f"Daily Summary — {yesterday}",
                    message=message,
                    severity="INFO",
                )
                db.add(notification)

            await db.commit()

    try:
        asyncio.get_event_loop().run_until_complete(_run())
    except Exception as exc:
        logger.error("Daily summary failed: %s", exc)
        raise self.retry(exc=exc, countdown=300)
