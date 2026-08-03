from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.profitability.recalculate_all")
def recalculate_all():
    """Batch recalculate profitability records with latest fee data."""
    # TODO: Implement in Phase 3
    pass
