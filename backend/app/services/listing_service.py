"""Service for publishing and syncing eBay listings via the Inventory API."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import EbayAPIError
from app.integrations.ebay.inventory_api import EbayInventoryAPI
from app.models.inventory import Inventory
from app.models.listing import Listing
from app.models.product import Product
from app.services.ebay_service import get_ebay_client


async def publish_listing(
    db: AsyncSession,
    user_id: uuid.UUID,
    listing_id: uuid.UUID,
) -> Listing:
    result = await db.execute(
        select(Listing).where(Listing.id == listing_id, Listing.user_id == user_id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise ValueError(f"Listing {listing_id} not found")

    product_result = await db.execute(
        select(Product).where(Product.id == listing.product_id)
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise ValueError("Product not found")

    inv_result = await db.execute(
        select(Inventory).where(Inventory.product_id == product.id)
    )
    inventory = inv_result.scalar_one_or_none()
    quantity = inventory.quantity_available if inventory else 1

    client = await get_ebay_client(db, user_id)
    api = EbayInventoryAPI(client)

    try:
        # 1. Create or replace inventory item
        inv_payload = api.build_inventory_item_payload(
            product=product,
            supplier_cost=0,
            quantity=quantity,
            condition=_map_condition(listing.status, product.condition),
        )
        # Attach image URLs if available
        images = sorted(product.images, key=lambda i: i.position) if product.images else []
        if images:
            inv_payload["product"]["imageUrls"] = [img.url for img in images[:12]]

        await api.create_or_replace_inventory_item(product.sku, inv_payload)

        # 2. Create or update offer
        if listing.ebay_offer_id:
            offer_payload = api.build_offer_payload(
                sku=product.sku,
                price=float(listing.price),
                category_id=listing.ebay_category_id or "",
                shipping_policy_id=listing.shipping_policy_id or "",
                return_policy_id=listing.return_policy_id or "",
                payment_policy_id=listing.payment_policy_id or "",
                quantity=listing.quantity_listed,
                description_html=listing.description_html,
                promoted_listing_rate=float(listing.promoted_listing_rate)
                if listing.promoted_listing_rate
                else None,
            )
            await api.update_offer(listing.ebay_offer_id, offer_payload)
            offer_id = listing.ebay_offer_id
        else:
            offer_payload = api.build_offer_payload(
                sku=product.sku,
                price=float(listing.price),
                category_id=listing.ebay_category_id or "",
                shipping_policy_id=listing.shipping_policy_id or "",
                return_policy_id=listing.return_policy_id or "",
                payment_policy_id=listing.payment_policy_id or "",
                quantity=listing.quantity_listed,
                description_html=listing.description_html,
            )
            offer_resp = await api.create_offer(offer_payload)
            offer_id = offer_resp.get("offerId", "")
            listing.ebay_offer_id = offer_id

        # 3. Publish offer
        publish_resp = await api.publish_offer(offer_id)
        ebay_item_id = publish_resp.get("listingId", "")
        if ebay_item_id:
            listing.ebay_item_id = ebay_item_id

        listing.status = "ACTIVE"
        listing.started_at = datetime.now(timezone.utc)
        listing.last_synced_at = datetime.now(timezone.utc)
        listing.error_messages = {}

    except EbayAPIError as exc:
        listing.status = "ERROR"
        listing.error_messages = {"error": str(exc), "error_id": exc.error_id}
        raise
    finally:
        await client.close()

    await db.commit()
    await db.refresh(listing)
    return listing


async def end_listing(
    db: AsyncSession,
    user_id: uuid.UUID,
    listing_id: uuid.UUID,
) -> Listing:
    result = await db.execute(
        select(Listing).where(Listing.id == listing_id, Listing.user_id == user_id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise ValueError(f"Listing {listing_id} not found")

    if not listing.ebay_offer_id:
        listing.status = "ENDED"
        await db.commit()
        return listing

    client = await get_ebay_client(db, user_id)
    api = EbayInventoryAPI(client)
    try:
        await api.withdraw_offer(listing.ebay_offer_id)
        listing.status = "ENDED"
        listing.last_synced_at = datetime.now(timezone.utc)
    finally:
        await client.close()

    await db.commit()
    await db.refresh(listing)
    return listing


async def update_listing_price(
    db: AsyncSession,
    user_id: uuid.UUID,
    listing: Listing,
    new_price: float,
) -> Listing:
    if not listing.ebay_offer_id:
        raise ValueError("Listing has no eBay offer ID — publish it first")

    client = await get_ebay_client(db, user_id)
    api = EbayInventoryAPI(client)
    try:
        await api.update_offer(
            listing.ebay_offer_id,
            {"pricingSummary": {"price": {"value": str(new_price), "currency": "USD"}}},
        )
        listing.price = new_price
        listing.last_synced_at = datetime.now(timezone.utc)
    finally:
        await client.close()

    await db.commit()
    await db.refresh(listing)
    return listing


async def sync_listings_for_user(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Pull current offer statuses from eBay and update local DB."""
    result = await db.execute(
        select(Listing).where(
            Listing.user_id == user_id,
            Listing.status.in_(["ACTIVE", "DRAFT"]),
            Listing.ebay_offer_id.isnot(None),
        )
    )
    listings = result.scalars().all()
    if not listings:
        return {"synced": 0}

    client = await get_ebay_client(db, user_id)
    api = EbayInventoryAPI(client)
    synced = 0
    try:
        for listing in listings:
            try:
                offer = await api.get_offer(listing.ebay_offer_id)
                remote_status = offer.get("status", "")
                if remote_status == "PUBLISHED":
                    listing.status = "ACTIVE"
                    listing.ebay_item_id = offer.get("listing", {}).get("listingId", listing.ebay_item_id)
                elif remote_status in ("WITHDRAWN", "ENDED"):
                    listing.status = "ENDED"
                listing.last_synced_at = datetime.now(timezone.utc)
                synced += 1
            except EbayAPIError:
                pass
    finally:
        await client.close()

    await db.commit()
    return {"synced": synced}


def _map_condition(listing_status: str, product_condition: str) -> str:
    condition_map = {
        "NEW": "NEW",
        "NEW_OTHER": "NEW_OTHER",
        "NEW_WITH_DEFECTS": "NEW_WITH_DEFECTS",
        "MANUFACTURER_REFURBISHED": "MANUFACTURER_REFURBISHED",
        "CERTIFIED_REFURBISHED": "CERTIFIED_REFURBISHED",
        "EXCELLENT_REFURBISHED": "EXCELLENT_REFURBISHED",
        "VERY_GOOD_REFURBISHED": "VERY_GOOD_REFURBISHED",
        "GOOD_REFURBISHED": "GOOD_REFURBISHED",
        "SELLER_REFURBISHED": "SELLER_REFURBISHED",
        "LIKE_NEW": "USED_LIKE_NEW",
        "USED_EXCELLENT": "USED_EXCELLENT",
        "USED_VERY_GOOD": "USED_VERY_GOOD",
        "USED_GOOD": "USED_GOOD",
        "USED_ACCEPTABLE": "USED_ACCEPTABLE",
        "FOR_PARTS": "FOR_PARTS_OR_NOT_WORKING",
    }
    return condition_map.get(product_condition.upper(), "USED_GOOD")
