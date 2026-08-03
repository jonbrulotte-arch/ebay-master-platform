from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.inventory_tasks.check_low_stock")
def check_low_stock():
    """Evaluate inventory against reorder points and generate alerts."""
    # TODO: Implement in Phase 6
    pass
