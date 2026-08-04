import asyncio
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import async_session
from app.models.listing import Listing
from app.models.price_change_log import PriceChangeLog
from app.models.pricing_rule import PricingRule
from app.models.product_supplier import ProductSupplier
from app.models.user import User
from app.services.pricing_service import (
    calculate_fees,
    compute_price_for_target_margin,
    merge_user_settings,
)
from app.tasks.celery_app import celery_app


async def _run_reprice_check() -> dict:
    stats = {"users": 0, "evaluated": 0, "repriced": 0, "errors": 0}

    async with async_session() as db:
        users_result = await db.execute(select(User))
        users = users_result.scalars().all()

        for user in users:
            stats["users"] += 1
            settings = merge_user_settings(user.settings)

            rules_result = await db.execute(
                select(PricingRule).where(
                    PricingRule.user_id == user.id,
                    PricingRule.is_active == True,
                )
            )
            rules = rules_result.scalars().all()
            if not rules:
                continue

            global_rules = [r for r in rules if r.product_id is None]
            product_rules: dict = {}
            for r in rules:
                if r.product_id:
                    product_rules.setdefault(r.product_id, []).append(r)

            listings_result = await db.execute(
                select(Listing).where(
                    Listing.user_id == user.id,
                    Listing.status == "ACTIVE",
                )
            )
            listings = listings_result.scalars().all()

            for listing in listings:
                stats["evaluated"] += 1
                applicable_rules = sorted(
                    product_rules.get(listing.product_id, []) + global_rules,
                    key=lambda r: r.priority,
                    reverse=True,
                )
                if not applicable_rules:
                    continue

                rule = applicable_rules[0]
                if not rule.min_margin_pct or not rule.target_margin_pct:
                    continue

                supplier_result = await db.execute(
                    select(ProductSupplier)
                    .where(
                        ProductSupplier.product_id == listing.product_id,
                        ProductSupplier.is_preferred == True,
                    )
                    .limit(1)
                )
                supplier = supplier_result.scalar_one_or_none()
                if supplier is None:
                    supplier_result = await db.execute(
                        select(ProductSupplier)
                        .where(ProductSupplier.product_id == listing.product_id)
                        .order_by(ProductSupplier.unit_cost)
                        .limit(1)
                    )
                    supplier = supplier_result.scalar_one_or_none()

                cogs = Decimal(str(supplier.unit_cost)) if supplier else Decimal("0")
                actual_shipping = Decimal(str(supplier.shipping_cost or 0)) if supplier else Decimal("0")
                current_price = Decimal(str(listing.price))
                promoted_rate = Decimal(str(listing.promoted_listing_rate or settings["default_promoted_rate"]))

                try:
                    result = calculate_fees(
                        sold_price=current_price,
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
                except Exception:
                    stats["errors"] += 1
                    continue

                current_margin = result["profit_margin_pct"]
                if current_margin >= Decimal(str(rule.min_margin_pct)):
                    continue

                try:
                    new_price = compute_price_for_target_margin(
                        item_cost=cogs,
                        actual_shipping_cost=actual_shipping,
                        target_margin_pct=Decimal(str(rule.target_margin_pct)),
                        store_level=settings["ebay_store_level"],
                        category_name=settings["default_fee_category"],
                        shipping_charge_to_buyer=Decimal("0"),
                        seller_discount_pct=Decimal("0"),
                        promoted_rate=promoted_rate,
                        sales_tax_rate=Decimal(str(settings["default_sales_tax_rate"])),
                        is_top_rated_seller=settings["is_top_rated_seller"],
                    )
                except Exception:
                    stats["errors"] += 1
                    continue

                if rule.min_price:
                    new_price = max(new_price, Decimal(str(rule.min_price)))
                if rule.max_price:
                    new_price = min(new_price, Decimal(str(rule.max_price)))

                if new_price == current_price:
                    continue

                applied = False
                ebay_error = None
                try:
                    from app.services.listing_service import update_listing_price
                    await update_listing_price(db, str(user.id), listing, new_price)
                    applied = True
                except Exception as e:
                    ebay_error = str(e)[:500]

                log = PriceChangeLog(
                    listing_id=listing.id,
                    product_id=listing.product_id,
                    pricing_rule_id=rule.id,
                    old_price=float(current_price),
                    new_price=float(new_price),
                    reason="MARGIN_BELOW_MIN",
                    reason_detail=f"margin {float(current_margin):.2f}% < min {rule.min_margin_pct}%",
                    applied_to_ebay=applied,
                    ebay_update_error=ebay_error,
                    triggered_by="auto",
                )
                db.add(log)

                rule.last_triggered_at = datetime.now(timezone.utc)
                stats["repriced"] += 1

        await db.commit()

    return stats


@celery_app.task(name="app.tasks.repricing.reprice_check", bind=True, max_retries=3)
def reprice_check(self):
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_run_reprice_check())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
