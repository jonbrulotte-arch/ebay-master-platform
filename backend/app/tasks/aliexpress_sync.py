from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.aliexpress_sync.sync_tracking")
def sync_tracking():
    """Poll AliExpress for tracking updates on forwarded orders."""
    # TODO: Implement in Phase 5
    pass


@celery_app.task(name="app.tasks.aliexpress_sync.forward_order")
def forward_order(order_id: str):
    """Forward an eBay order to AliExpress for fulfillment."""
    # TODO: Implement in Phase 5
    pass
