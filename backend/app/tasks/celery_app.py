from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery("ebay_platform", broker=settings.redis_url, backend=settings.redis_url)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.tasks.ebay_sync.*": {"queue": "critical"},
        "app.tasks.maintenance.refresh_tokens": {"queue": "critical"},
        "app.tasks.repricing.*": {"queue": "default"},
        "app.tasks.inventory_tasks.*": {"queue": "default"},
        "app.tasks.supplier_monitoring.*": {"queue": "bulk"},
        "app.tasks.profitability.*": {"queue": "bulk"},
    },
    beat_schedule={
        "sync-ebay-orders": {
            "task": "app.tasks.ebay_sync.sync_orders",
            "schedule": crontab(minute="*/15"),
        },
        "sync-ebay-listings": {
            "task": "app.tasks.ebay_sync.sync_listings",
            "schedule": crontab(minute="*/30"),
        },
        "refresh-ebay-tokens": {
            "task": "app.tasks.maintenance.refresh_tokens",
            "schedule": crontab(minute="*/30"),
        },
        "reprice-check": {
            "task": "app.tasks.repricing.reprice_check",
            "schedule": crontab(minute="0"),  # every hour
        },
        "check-low-stock": {
            "task": "app.tasks.inventory_tasks.check_low_stock",
            "schedule": crontab(minute="0", hour="*/2"),
        },
        "check-supplier-prices": {
            "task": "app.tasks.supplier_monitoring.check_supplier_prices",
            "schedule": crontab(minute="0", hour="*/6"),
        },
        "sync-aliexpress-tracking": {
            "task": "app.tasks.aliexpress_sync.sync_tracking",
            "schedule": crontab(minute="0", hour="*/2"),
        },
        "daily-profitability-recalc": {
            "task": "app.tasks.profitability.recalculate_all",
            "schedule": crontab(minute="0", hour="2"),
        },
        "daily-summary": {
            "task": "app.tasks.maintenance.generate_daily_summary",
            "schedule": crontab(minute="0", hour="8"),
        },
    },
)

celery_app.autodiscover_tasks([
    "app.tasks.ebay_sync",
    "app.tasks.repricing",
    "app.tasks.supplier_monitoring",
    "app.tasks.inventory_tasks",
    "app.tasks.profitability",
    "app.tasks.maintenance",
    "app.tasks.aliexpress_sync",
])
