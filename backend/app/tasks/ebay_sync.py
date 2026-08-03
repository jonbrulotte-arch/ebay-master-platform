from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.ebay_sync.sync_orders")
def sync_orders():
    """Pull new/updated orders from eBay Fulfillment API."""
    # TODO: Implement in Phase 2
    pass


@celery_app.task(name="app.tasks.ebay_sync.sync_listings")
def sync_listings():
    """Sync listing status changes from eBay."""
    # TODO: Implement in Phase 2
    pass


@celery_app.task(name="app.tasks.ebay_sync.sync_messages")
def sync_messages():
    """Pull buyer messages from eBay."""
    # TODO: Implement in Phase 6
    pass


@celery_app.task(name="app.tasks.ebay_sync.sync_returns")
def sync_returns():
    """Pull return/refund updates from eBay."""
    # TODO: Implement in Phase 6
    pass
