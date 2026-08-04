"""Order ingestion and sync from eBay Fulfillment API."""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.ebay.fulfillment_api import EbayFulfillmentAPI
from app.models.listing import Listing
from app.models.order import Order
from app.models.order_line_item import OrderLineItem
from app.models.product import Product
from app.models.user import User
from app.services.ebay_service import get_ebay_client


def _parse_amount(amount_obj: dict | None) -> Decimal:
    if not amount_obj:
        return Decimal("0")
    return Decimal(str(amount_obj.get("value", "0")))


async def sync_orders_for_user(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Pull orders from eBay that were modified in the last 2 days (conservative window)."""
    client = await get_ebay_client(db, user_id)
    api = EbayFulfillmentAPI(client)

    try:
        since = (datetime.now(timezone.utc) - timedelta(days=2)).strftime(
            "%Y-%m-%dT%H:%M:%S.000Z"
        )
        ebay_orders = await api.get_orders_since(since)
    finally:
        await client.close()

    created = 0
    updated = 0

    for ebay_order in ebay_orders:
        ebay_order_id = ebay_order.get("orderId", "")
        if not ebay_order_id:
            continue

        result = await db.execute(
            select(Order).where(Order.ebay_order_id == ebay_order_id)
        )
        order = result.scalar_one_or_none()

        pricing = ebay_order.get("pricingSummary", {})
        total_amount = _parse_amount(pricing.get("total"))
        subtotal = _parse_amount(pricing.get("priceSubtotal"))
        shipping_cost = _parse_amount(pricing.get("deliveryCost"))
        tax_amount = _parse_amount(pricing.get("tax"))

        buyer = ebay_order.get("buyer", {})
        shipping_addr_raw = ebay_order.get("fulfillmentStartInstructions", [{}])[0].get(
            "shippingStep", {}
        ).get("shipTo", {})

        shipping_address = {
            "name": shipping_addr_raw.get("fullName", ""),
            "addressLine1": shipping_addr_raw.get("contactAddress", {}).get("addressLine1", ""),
            "addressLine2": shipping_addr_raw.get("contactAddress", {}).get("addressLine2", ""),
            "city": shipping_addr_raw.get("contactAddress", {}).get("city", ""),
            "stateOrProvince": shipping_addr_raw.get("contactAddress", {}).get("stateOrProvince", ""),
            "postalCode": shipping_addr_raw.get("contactAddress", {}).get("postalCode", ""),
            "countryCode": shipping_addr_raw.get("contactAddress", {}).get("countryCode", "US"),
        }

        paid_at = None
        raw_paid = ebay_order.get("paymentSummary", {}).get("payments", [{}])[0].get("paymentDate")
        if raw_paid:
            try:
                paid_at = datetime.fromisoformat(raw_paid.replace("Z", "+00:00"))
            except ValueError:
                pass

        if order is None:
            order = Order(
                user_id=user_id,
                ebay_order_id=ebay_order_id,
                buyer_username=buyer.get("username", ""),
                order_status=ebay_order.get("orderFulfillmentStatus", "NOT_STARTED"),
                payment_status=ebay_order.get("paymentSummary", {}).get("payments", [{}])[0].get(
                    "paymentStatus", "PENDING"
                ),
                total_amount=total_amount,
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                tax_amount=tax_amount,
                shipping_address=shipping_address,
                paid_at=paid_at,
            )
            db.add(order)
            await db.flush()
            created += 1

            # Create line items
            for li in ebay_order.get("lineItems", []):
                ebay_li_id = li.get("lineItemId", "")
                ebay_item_id = li.get("legacyItemId", "")

                # Look up listing by eBay item ID
                listing_result = await db.execute(
                    select(Listing).where(Listing.ebay_item_id == ebay_item_id)
                )
                listing = listing_result.scalar_one_or_none()

                product_id = listing.product_id if listing else None
                listing_id = listing.id if listing else None

                unit_price = _parse_amount(li.get("lineItemCost"))
                quantity = li.get("quantity", 1)

                line_item = OrderLineItem(
                    order_id=order.id,
                    listing_id=listing_id,
                    product_id=product_id,
                    ebay_line_item_id=ebay_li_id,
                    title=li.get("title", ""),
                    sku=li.get("sku", ""),
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=unit_price * quantity,
                )
                db.add(line_item)
                await db.flush()

                # Create actual profitability record for new line items with a product
                if product_id:
                    user_result = await db.execute(select(User).where(User.id == user_id))
                    user = user_result.scalar_one_or_none()
                    user_settings = user.settings if user else None
                    try:
                        from app.services.profitability_service import create_actual_record
                        await create_actual_record(db, line_item, user_settings)
                    except Exception:
                        pass
        else:
            # Update existing order status
            order.order_status = ebay_order.get("orderFulfillmentStatus", order.order_status)
            order.payment_status = (
                ebay_order.get("paymentSummary", {})
                .get("payments", [{}])[0]
                .get("paymentStatus", order.payment_status)
            )
            shipping_info = ebay_order.get("fulfillmentStartInstructions", [{}])[0]
            tracking = shipping_info.get("finalDestinationAddress", {})
            carrier = shipping_info.get("shippingStep", {}).get("shippingServiceCode", "")
            if carrier:
                order.shipping_carrier = carrier
            updated += 1

    await db.commit()
    return {"created": created, "updated": updated, "total_fetched": len(ebay_orders)}


async def get_order_with_profitability(db: AsyncSession, order_id: uuid.UUID) -> Order | None:
    result = await db.execute(
        select(Order).where(Order.id == order_id)
    )
    return result.scalar_one_or_none()
