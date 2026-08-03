from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.maintenance.refresh_tokens")
def refresh_tokens():
    """Refresh any eBay OAuth tokens expiring within 1 hour."""
    # TODO: Implement in Phase 2
    pass


@celery_app.task(name="app.tasks.maintenance.generate_daily_summary")
def generate_daily_summary():
    """Create daily sales/profit summary notification."""
    # TODO: Implement in Phase 4
    pass
