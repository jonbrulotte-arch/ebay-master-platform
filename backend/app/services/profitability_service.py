from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing
from app.models.order_line_item import OrderLineItem
from app.models.product_supplier import ProductSupplier
from app.models.profitability import ProfitabilityRecord
from app.services.pricing_service import calculate_fees, merge_user_settings


async def create_projected_record(
    db: AsyncSession,
    listing: Listing,
    user_settings: dict | None = None,
) -> ProfitabilityRecord | None:
    if not listing.product_id:
        return None

    result = await db.execute(
        select(ProductSupplier)
        .where(
            ProductSupplier.product_id == listing.product_id,
            ProductSupplier.is_preferred == True,
        )
        .limit(1)
    )
    supplier = result.scalar_one_or_none()
    if supplier is None:
        result = await db.execute(
            select(ProductSupplier)
            .where(ProductSupplier.product_id == listing.product_id)
            .order_by(ProductSupplier.unit_cost)
            .limit(1)
        )
        supplier = result.scalar_one_or_none()

    cogs = Decimal(str(supplier.unit_cost)) if supplier else Decimal("0")
    actual_shipping = Decimal(str(supplier.shipping_cost or 0)) if supplier else Decimal("0")

    settings = merge_user_settings(user_settings)
    promoted_rate = Decimal(str(listing.promoted_listing_rate or settings["default_promoted_rate"]))

    result_data = calculate_fees(
        sold_price=Decimal(str(listing.price)),
        item_cost=cogs,
        actual_shipping_cost=actual_shipping,
        store_level=settings["ebay_store_level"],
        category_name=settings["default_fee_category"],
        shipping_charge_to_buyer=Decimal("0"),
        seller_discount_pct=Decimal("0"),
        promoted_rate=promoted_rate,
        sales_tax_rate=Decimal(str(settings["default_sales_tax_rate"])),
        is_top_rated_seller=settings["is_top_rated_seller"],
    )

    existing = await db.execute(
        select(ProfitabilityRecord).where(
            ProfitabilityRecord.product_id == listing.product_id,
            ProfitabilityRecord.record_type == "PROJECTED",
            ProfitabilityRecord.order_line_item_id == None,
        )
    )
    record = existing.scalar_one_or_none()
    if record is None:
        record = ProfitabilityRecord(
            product_id=listing.product_id,
            record_type="PROJECTED",
        )
        db.add(record)

    record.sale_price = float(result_data["sold_price"])
    record.cost_of_goods = float(cogs)
    record.shipping_cost_from_supplier = float(actual_shipping)
    record.ebay_final_value_fee = float(result_data["final_value_fee"])
    record.ebay_payment_processing_fee = 0.0
    record.ebay_promoted_listing_fee = float(result_data["promoted_fee"])
    record.ebay_international_fee = 0.0
    record.tax_collected = float(result_data["sales_tax_amount"])
    record.total_costs = float(cogs + actual_shipping + result_data["total_fees"])
    record.gross_profit = float(result_data["net_profit"])
    record.profit_margin_pct = float(result_data["profit_margin_pct"])
    record.roi_pct = float(result_data["roi_pct"])

    await db.flush()
    return record


async def create_actual_record(
    db: AsyncSession,
    line_item: OrderLineItem,
    user_settings: dict | None = None,
) -> ProfitabilityRecord | None:
    if not line_item.product_id:
        return None

    result = await db.execute(
        select(ProductSupplier)
        .where(
            ProductSupplier.product_id == line_item.product_id,
            ProductSupplier.is_preferred == True,
        )
        .limit(1)
    )
    supplier = result.scalar_one_or_none()
    if supplier is None:
        result = await db.execute(
            select(ProductSupplier)
            .where(ProductSupplier.product_id == line_item.product_id)
            .order_by(ProductSupplier.unit_cost)
            .limit(1)
        )
        supplier = result.scalar_one_or_none()

    cogs = Decimal(str(supplier.unit_cost)) if supplier else Decimal("0")
    actual_shipping = Decimal(str(supplier.shipping_cost or 0)) if supplier else Decimal("0")

    settings = merge_user_settings(user_settings)

    fvf = Decimal(str(line_item.ebay_final_value_fee or 0))
    promo = Decimal(str(line_item.ebay_promoted_listing_fee or 0))
    intl = Decimal(str(line_item.ebay_international_fee or 0))
    total_fees = fvf + promo + intl

    sale_price = Decimal(str(line_item.unit_price))
    payout = sale_price - total_fees
    net_profit = payout - cogs - actual_shipping
    pre_tax_total = sale_price
    margin = (net_profit / pre_tax_total * 100) if pre_tax_total > 0 else Decimal("0")
    roi = (net_profit / cogs * 100) if cogs > 0 else Decimal("0")

    record = ProfitabilityRecord(
        product_id=line_item.product_id,
        order_line_item_id=line_item.id,
        record_type="ACTUAL",
        sale_price=float(sale_price),
        cost_of_goods=float(cogs),
        shipping_cost_from_supplier=float(actual_shipping),
        ebay_final_value_fee=float(fvf),
        ebay_payment_processing_fee=0.0,
        ebay_promoted_listing_fee=float(promo),
        ebay_international_fee=float(intl),
        tax_collected=0.0,
        total_costs=float(cogs + actual_shipping + total_fees),
        gross_profit=float(net_profit),
        profit_margin_pct=float(margin),
        roi_pct=float(roi),
    )
    db.add(record)
    await db.flush()
    return record


async def recalculate_for_user(db: AsyncSession, user_id: str) -> int:
    from app.models.listing import Listing
    from app.models.user import User

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return 0

    result = await db.execute(
        select(Listing).where(
            Listing.user_id == user_id,
            Listing.status == "ACTIVE",
        )
    )
    listings = result.scalars().all()

    count = 0
    for listing in listings:
        rec = await create_projected_record(db, listing, user.settings)
        if rec:
            count += 1

    return count
