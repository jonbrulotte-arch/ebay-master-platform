from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.supplier_monitoring.check_supplier_prices")
def check_supplier_prices():
    """Check AliExpress supplier prices for changes."""
    # TODO: Implement in Phase 5
    pass
