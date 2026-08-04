"""
AliExpress business logic: product search/import, price monitoring,
dropship order forwarding, and tracking sync.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import AliExpressAPIError, NotFoundError
from app.integrations.aliexpress.client import AliExpressClient
from app.models.notification import Notification
from app.models.order import Order
from app.models.product import Product
from app.models.product_supplier import ProductSupplier
from app.models.supplier import Supplier
from app.schemas.aliexpress import (
    AliExpressImportResponse,
    AliExpressProduct,
    AliExpressSearchResponse,
    SupplierPriceCheckResult,
)

logger = logging.getLogger(__name__)

# CNY → USD safety margin (adds a buffer over market rate to protect margins)
_DEFAULT_SAFETY_MARGIN_PCT = 2.0
# Hardcoded fallback rate updated periodically; in production wire to an FX API
_CNY_USD_RATE = 0.138


# ── Currency ──────────────────────────────────────────────────────────────────

def convert_cny_to_usd(amount_cny: float, safety_margin_pct: float = _DEFAULT_SAFETY_MARGIN_PCT) -> float:
    effective_rate = _CNY_USD_RATE * (1 + safety_margin_pct / 100)
    return round(amount_cny * effective_rate, 2)


def get_currency_info(safety_margin_pct: float = _DEFAULT_SAFETY_MARGIN_PCT) -> dict:
    return {
        "from_currency": "CNY",
        "to_currency": "USD",
        "rate": _CNY_USD_RATE,
        "safety_margin_pct": safety_margin_pct,
        "effective_rate": round(_CNY_USD_RATE * (1 + safety_margin_pct / 100), 6),
        "updated_at": datetime.now(timezone.utc),
    }


# ── Product search / import ───────────────────────────────────────────────────

def _parse_product(raw: dict) -> AliExpressProduct:
    """Normalise a raw AliExpress affiliate API product dict."""
    sale_price = float(raw.get("target_sale_price") or raw.get("sale_price") or 0)
    orig_price = float(raw.get("original_price") or sale_price)
    return AliExpressProduct(
        product_id=str(raw.get("product_id") or raw.get("product_detail_url", "").split("/")[-1]),
        title=raw.get("product_title") or raw.get("title") or "",
        sale_price_usd=sale_price,
        original_price_usd=orig_price,
        image_url=raw.get("product_main_image_url") or raw.get("image_url"),
        product_url=raw.get("product_detail_url") or raw.get("product_url"),
        store_name=raw.get("shop_name") or raw.get("store_name"),
        store_id=str(raw.get("shop_id") or raw.get("store_id") or ""),
        avg_star_rating=float(raw.get("evaluate_rate", 0) or 0) / 20,  # API returns 0-100
        total_orders=int(raw.get("lastest_volume") or 0),
        shipping_lead_days=None,
    )


async def search_products(
    query: str,
    page: int = 1,
    page_size: int = 20,
    min_price: float | None = None,
    max_price: float | None = None,
) -> AliExpressSearchResponse:
    client = AliExpressClient()
    try:
        raw = await client.search_products(
            query=query, page=page, page_size=page_size,
            min_price=min_price, max_price=max_price,
        )
    finally:
        await client.close()

    # Navigate nested AliExpress response structure
    result_wrapper = (
        raw.get("aliexpress_affiliate_product_query_response", {})
        .get("resp_result", {})
    )
    if result_wrapper.get("resp_code") != 200:
        raise AliExpressAPIError(result_wrapper.get("resp_msg", "Search failed"))

    result = result_wrapper.get("result", {})
    products_raw = result.get("products", {}).get("product", [])
    total = int(result.get("total_record_count") or 0)

    products = [_parse_product(p) for p in products_raw]
    return AliExpressSearchResponse(
        products=products,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total else 1,
    )


async def get_product_detail(product_id: str) -> dict[str, Any]:
    client = AliExpressClient()
    try:
        raw = await client.get_product_detail(product_id)
    finally:
        await client.close()

    result_wrapper = (
        raw.get("aliexpress_affiliate_product_detail_query_response", {})
        .get("resp_result", {})
    )
    if result_wrapper.get("resp_code") != 200:
        raise AliExpressAPIError(result_wrapper.get("resp_msg", "Product detail fetch failed"))

    return result_wrapper.get("result", {})


async def import_product(
    data: dict,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> AliExpressImportResponse:
    """
    Import an AliExpress product into the local catalog.
    Creates Product + Supplier (or uses existing) + ProductSupplier link.
    """
    ae_product_id = data["product_id"]
    title = data.get("title") or f"AliExpress Product {ae_product_id}"
    price_usd = float(data.get("sale_price_usd") or 0)
    shipping_cost = float(data.get("shipping_cost_usd") or 0)
    store_name = data.get("store_name") or "AliExpress Supplier"
    store_id = data.get("store_id") or ""
    supplier_id_override: uuid.UUID | None = data.get("supplier_id")

    # Reuse or create supplier
    if supplier_id_override:
        sup_result = await db.execute(
            select(Supplier).where(Supplier.id == supplier_id_override, Supplier.user_id == user_id)
        )
        supplier = sup_result.scalar_one_or_none()
        if not supplier:
            raise NotFoundError("Supplier not found")
    else:
        # Find existing supplier by store_id, or create new
        if store_id:
            sup_result = await db.execute(
                select(Supplier).where(
                    Supplier.user_id == user_id,
                    Supplier.store_id == store_id,
                    Supplier.platform == "ALIEXPRESS",
                )
            )
            supplier = sup_result.scalar_one_or_none()
        else:
            supplier = None

        if not supplier:
            supplier = Supplier(
                user_id=user_id,
                name=store_name,
                platform="ALIEXPRESS",
                store_url=data.get("product_url"),
                store_id=store_id or None,
            )
            db.add(supplier)
            await db.flush()

    # Generate unique SKU
    sku = data.get("sku") or f"AE-{ae_product_id[:12].upper()}"

    # Create product
    product = Product(
        user_id=user_id,
        sku=sku,
        title=title,
        is_active=True,
        item_specifics={"source": "aliexpress", "ae_product_id": ae_product_id},
    )
    db.add(product)
    await db.flush()

    # Create product-supplier link
    ps = ProductSupplier(
        product_id=product.id,
        supplier_id=supplier.id,
        supplier_product_id=ae_product_id,
        supplier_product_url=data.get("product_url"),
        unit_cost=price_usd,
        currency="USD",
        shipping_cost=shipping_cost,
        is_preferred=True,
        last_price_check_at=datetime.now(timezone.utc),
    )
    db.add(ps)
    await db.flush()

    return AliExpressImportResponse(
        product_id=product.id,
        supplier_id=supplier.id,
        product_supplier_id=ps.id,
        sku=sku,
        title=title,
    )


# ── Price monitoring ──────────────────────────────────────────────────────────

async def check_supplier_price(
    product_supplier: ProductSupplier,
    db: AsyncSession,
    notify_user_id: uuid.UUID | None = None,
    change_threshold_pct: float = 5.0,
) -> SupplierPriceCheckResult:
    """Fetch current AliExpress price and update the product_supplier record."""
    ae_product_id = product_supplier.supplier_product_id
    if not ae_product_id:
        return SupplierPriceCheckResult(
            product_supplier_id=product_supplier.id,
            old_price=float(product_supplier.unit_cost),
            new_price=float(product_supplier.unit_cost),
            changed=False,
            change_pct=0.0,
        )

    client = AliExpressClient()
    try:
        detail = await get_product_detail(ae_product_id)
    except AliExpressAPIError as exc:
        logger.warning("Price check failed for %s: %s", ae_product_id, exc)
        return SupplierPriceCheckResult(
            product_supplier_id=product_supplier.id,
            old_price=float(product_supplier.unit_cost),
            new_price=float(product_supplier.unit_cost),
            changed=False,
            change_pct=0.0,
        )
    finally:
        await client.close()

    raw_price = float(
        detail.get("target_sale_price")
        or detail.get("sale_price")
        or product_supplier.unit_cost
    )
    old_price = float(product_supplier.unit_cost)
    change_pct = abs(raw_price - old_price) / old_price * 100 if old_price else 0.0

    changed = change_pct >= change_threshold_pct
    if changed:
        # Append to price_history
        history: list = list(product_supplier.price_history or [])
        history.append({
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "price": old_price,
            "currency": str(product_supplier.currency or "USD"),
        })
        product_supplier.price_history = history[-50:]  # keep last 50
        product_supplier.unit_cost = raw_price  # type: ignore[assignment]

        if notify_user_id:
            direction = "increased" if raw_price > old_price else "decreased"
            notif = Notification(
                user_id=notify_user_id,
                type="SUPPLIER_PRICE_CHANGE",
                title="Supplier Price Change",
                message=(
                    f"AliExpress product {ae_product_id} price {direction} "
                    f"${old_price:.2f} → ${raw_price:.2f} ({change_pct:.1f}%)"
                ),
                severity="WARNING" if raw_price > old_price else "INFO",
                related_entity_type="product_supplier",
                related_entity_id=product_supplier.id,
            )
            db.add(notif)

    product_supplier.last_price_check_at = datetime.now(timezone.utc)  # type: ignore[assignment]

    return SupplierPriceCheckResult(
        product_supplier_id=product_supplier.id,
        old_price=old_price,
        new_price=raw_price,
        changed=changed,
        change_pct=round(change_pct, 2),
    )


# ── Order forwarding ──────────────────────────────────────────────────────────

async def forward_order_to_aliexpress(
    order: Order,
    db: AsyncSession,
    sku_id: str | None = None,
    logistics_service: str = "YANWEN_REGULAR_AIRMAIL",
) -> str:
    """
    Place a dropship order on AliExpress for the given eBay order.
    Returns the AliExpress order ID.
    """
    if order.aliexpress_order_id:
        return order.aliexpress_order_id  # already forwarded

    # Collect product IDs from line items
    line_items = order.line_items
    if not line_items:
        raise ValueError("Order has no line items")

    # Build shipping address from eBay order
    addr = order.shipping_address or {}
    shipping_address = {
        "name": addr.get("fullName") or addr.get("name") or "Buyer",
        "phone": addr.get("primaryPhone", {}).get("phoneNumber") if isinstance(addr.get("primaryPhone"), dict) else addr.get("phone", ""),
        "address_line1": addr.get("addressLine1") or addr.get("street", ""),
        "city": addr.get("city", ""),
        "state": addr.get("stateOrProvince") or addr.get("state", ""),
        "postal_code": addr.get("postalCode") or addr.get("zip", ""),
        "country_code": addr.get("countryCode") or addr.get("country", "US"),
    }

    # For simplicity, forward the first line item that has an AliExpress product
    for li in line_items:
        if li.product_id:
            ps_result = await db.execute(
                select(ProductSupplier)
                .where(
                    ProductSupplier.product_id == li.product_id,
                    ProductSupplier.is_preferred == True,
                )
            )
            ps = ps_result.scalar_one_or_none()
            if ps and ps.supplier_product_id:
                client = AliExpressClient()
                try:
                    raw = await client.place_dropship_order(
                        product_id=ps.supplier_product_id,
                        sku_id=sku_id or ps.supplier_product_id,
                        quantity=li.quantity,
                        shipping_address=shipping_address,
                        logistics_service=logistics_service,
                    )
                finally:
                    await client.close()

                ae_result = raw.get("aliexpress_ds_order_create_request_upload_response", {})
                ae_order_id = str(ae_result.get("order_id", ""))

                order.aliexpress_order_id = ae_order_id  # type: ignore[assignment]
                order.aliexpress_order_status = "PLACED"  # type: ignore[assignment]
                return ae_order_id

    raise AliExpressAPIError("No AliExpress product linked to order line items")


# ── Tracking sync ─────────────────────────────────────────────────────────────

async def sync_tracking_for_order(order: Order, db: AsyncSession) -> dict | None:
    """
    Fetch AliExpress tracking for a forwarded order and update the Order record.
    Returns tracking info dict or None if not yet available.
    """
    if not order.aliexpress_order_id:
        return None

    client = AliExpressClient()
    try:
        raw = await client.get_order_tracking(order.aliexpress_order_id)
    except AliExpressAPIError as exc:
        logger.warning("Tracking fetch failed for AE order %s: %s", order.aliexpress_order_id, exc)
        return None
    finally:
        await client.close()

    tracking_list = (
        raw.get("aliexpress_ds_order_tracking_list_query_response", {})
        .get("result", {})
        .get("tracking_list", {})
        .get("tracking_info", [])
    )
    if not tracking_list:
        return None

    # Take the most recent tracking entry
    latest = tracking_list[0] if isinstance(tracking_list, list) else None
    if not latest:
        return None

    tracking_number = latest.get("tracking_number") or latest.get("logistics_no")
    carrier = latest.get("logistics_company") or latest.get("carrier")

    if tracking_number and not order.aliexpress_tracking_number:
        order.aliexpress_tracking_number = tracking_number  # type: ignore[assignment]
        order.aliexpress_order_status = "SHIPPED"  # type: ignore[assignment]
        # Also update the main order tracking if not already set
        if not order.tracking_number:
            order.tracking_number = tracking_number  # type: ignore[assignment]
            order.shipping_carrier = carrier  # type: ignore[assignment]

    return {"tracking_number": tracking_number, "carrier": carrier}
