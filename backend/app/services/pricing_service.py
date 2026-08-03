from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fee_schedule import FeeSchedule
from app.models.price_change_log import PriceChangeLog
from app.models.pricing_rule import PricingRule
from app.models.product_supplier import ProductSupplier


class PricingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_fee_rates(self, category_id: str | None, marketplace: str = "EBAY_US") -> dict:
        defaults = {
            "final_value_fee_pct": Decimal("13.25"),
            "payment_processing_pct": Decimal("2.35"),
            "payment_processing_fixed": Decimal("0.25"),
            "international_fee_pct": Decimal("1.65"),
        }
        if not category_id:
            return defaults

        result = await self.db.execute(
            select(FeeSchedule)
            .where(
                FeeSchedule.category_id == category_id,
                FeeSchedule.marketplace == marketplace,
            )
            .order_by(FeeSchedule.effective_from.desc())
            .limit(1)
        )
        schedule = result.scalar_one_or_none()
        if not schedule:
            return defaults

        return {
            "final_value_fee_pct": Decimal(str(schedule.final_value_fee_pct)),
            "payment_processing_pct": Decimal(str(schedule.payment_processing_pct)),
            "payment_processing_fixed": Decimal(str(schedule.payment_processing_fixed)),
            "international_fee_pct": Decimal(str(schedule.international_fee_pct)),
        }

    def calculate_fees(
        self,
        sale_price: Decimal,
        fee_rates: dict,
        promoted_rate: Decimal | None = None,
        is_international: bool = False,
    ) -> dict:
        fvf = sale_price * fee_rates["final_value_fee_pct"] / 100
        pp = sale_price * fee_rates["payment_processing_pct"] / 100 + fee_rates["payment_processing_fixed"]
        promo = sale_price * promoted_rate / 100 if promoted_rate else Decimal("0")
        intl = sale_price * fee_rates["international_fee_pct"] / 100 if is_international else Decimal("0")
        total = fvf + pp + promo + intl

        return {
            "final_value_fee": fvf.quantize(Decimal("0.01")),
            "payment_processing_fee": pp.quantize(Decimal("0.01")),
            "promoted_listing_fee": promo.quantize(Decimal("0.01")),
            "international_fee": intl.quantize(Decimal("0.01")),
            "total_fees": total.quantize(Decimal("0.01")),
        }

    def calculate_profitability(
        self,
        sale_price: Decimal,
        cost_of_goods: Decimal,
        supplier_shipping: Decimal,
        fees: dict,
        shipping_to_buyer: Decimal = Decimal("0"),
    ) -> dict:
        total_costs = cost_of_goods + supplier_shipping + fees["total_fees"] + shipping_to_buyer
        gross_profit = sale_price - total_costs
        margin = (gross_profit / sale_price * 100) if sale_price > 0 else Decimal("0")
        roi = (gross_profit / cost_of_goods * 100) if cost_of_goods > 0 else Decimal("0")

        return {
            "total_costs": total_costs.quantize(Decimal("0.01")),
            "gross_profit": gross_profit.quantize(Decimal("0.01")),
            "profit_margin_pct": margin.quantize(Decimal("0.01")),
            "roi_pct": roi.quantize(Decimal("0.01")),
        }

    def compute_price_for_target_margin(
        self,
        cost_of_goods: Decimal,
        supplier_shipping: Decimal,
        target_margin_pct: Decimal,
        fee_rates: dict,
        promoted_rate: Decimal | None = None,
        is_international: bool = False,
    ) -> Decimal:
        """Reverse-calculate the sale price needed to achieve a target margin."""
        fee_pct_total = fee_rates["final_value_fee_pct"] + fee_rates["payment_processing_pct"]
        if promoted_rate:
            fee_pct_total += promoted_rate
        if is_international:
            fee_pct_total += fee_rates["international_fee_pct"]

        fixed_costs = cost_of_goods + supplier_shipping + fee_rates["payment_processing_fixed"]
        price = fixed_costs / (1 - fee_pct_total / 100 - target_margin_pct / 100)
        return price.quantize(Decimal("0.01"))
