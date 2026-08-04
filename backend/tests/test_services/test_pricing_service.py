"""
Unit tests for the fee calculator — verifies against the reference eBay profit
calculator tool that defines the exact expected outputs.
"""
from decimal import Decimal

import pytest

from app.services.pricing_service import calculate_fees, compute_price_for_target_margin


class TestCalculateFees:
    def _call(self, **kwargs) -> dict:
        defaults = dict(
            sold_price=Decimal("0"),
            item_cost=Decimal("0"),
            actual_shipping_cost=Decimal("0"),
            store_level="basic",
            category_name="All Other Categories",
            shipping_charge_to_buyer=Decimal("0"),
            seller_discount_pct=Decimal("0"),
            promoted_rate=Decimal("0"),
            sales_tax_rate=Decimal("0"),
            is_top_rated_seller=False,
        )
        defaults.update(kwargs)
        return calculate_fees(**defaults)

    def test_reference_case(self):
        """
        Reference values from the HTML calculator tool:
        soldPrice=$29.99, itemCost=$5.00, sellerDiscount=8%, shippingCharge=$0,
        shippingCost=$4.99, storeLevel=basic, category=All Other Categories,
        promotedRate=8%, salesTax=6.8%, topRated=true
        → netProfit=$11.47, margin=41.57%, ROI=229.42%
        """
        result = self._call(
            sold_price=Decimal("29.99"),
            item_cost=Decimal("5.00"),
            actual_shipping_cost=Decimal("4.99"),
            store_level="basic",
            category_name="All Other Categories",
            shipping_charge_to_buyer=Decimal("0"),
            seller_discount_pct=Decimal("8"),
            promoted_rate=Decimal("8"),
            sales_tax_rate=Decimal("6.8"),
            is_top_rated_seller=True,
        )
        assert result["net_profit"] == Decimal("11.47")
        assert float(result["profit_margin_pct"]) == pytest.approx(41.57, abs=0.1)
        assert float(result["roi_pct"]) == pytest.approx(229.42, abs=0.5)

    def test_no_discount_no_tax(self):
        result = self._call(
            sold_price=Decimal("50.00"),
            item_cost=Decimal("10.00"),
            actual_shipping_cost=Decimal("5.00"),
        )
        # pre_tax_total = $50, total_sale = $50 (no tax)
        # store=basic → 12.7% up to $2500 → 50 * 0.127 = $6.35
        # per_order_fee = $0.40
        # final_value_fee = $6.75
        # promoted_fee = 0
        # payout = $50 - $6.75 = $43.25
        # net_profit = $43.25 - $10 - $5 = $28.25
        assert result["pre_tax_total"] == Decimal("50.00")
        assert result["total_sale"] == Decimal("50.00")
        assert result["final_value_fee"] == Decimal("6.75")
        assert result["net_profit"] == Decimal("28.25")

    def test_starter_store_uses_higher_rate(self):
        result_basic = self._call(
            sold_price=Decimal("100.00"),
            item_cost=Decimal("20.00"),
            actual_shipping_cost=Decimal("0"),
            store_level="basic",
            category_name="All Other Categories",
        )
        result_starter = self._call(
            sold_price=Decimal("100.00"),
            item_cost=Decimal("20.00"),
            actual_shipping_cost=Decimal("0"),
            store_level="none",
            category_name="Most Categories",
        )
        # Starter has 13.6% vs basic 12.7% for typical categories
        assert result_starter["final_value_fee"] > result_basic["final_value_fee"]

    def test_top_rated_seller_10pct_discount(self):
        result_normal = self._call(sold_price=Decimal("100"), item_cost=Decimal("10"), actual_shipping_cost=Decimal("0"), is_top_rated_seller=False)
        result_trs = self._call(sold_price=Decimal("100"), item_cost=Decimal("10"), actual_shipping_cost=Decimal("0"), is_top_rated_seller=True)
        # fee_amount for TRS should be 90% of normal fee_amount
        # FVF = fee_amount + per_order_fee; only fee_amount gets the discount
        normal_fee_amount = result_normal["final_value_fee"] - Decimal("0.40")
        trs_fee_amount = result_trs["final_value_fee"] - Decimal("0.40")
        assert trs_fee_amount == (normal_fee_amount * Decimal("0.90")).quantize(Decimal("0.01"))

    def test_per_order_fee_waived_for_athletic_shoes_above_150(self):
        result = self._call(
            sold_price=Decimal("200.00"),
            item_cost=Decimal("50.00"),
            actual_shipping_cost=Decimal("0"),
            store_level="basic",
            category_name="Clothing, Shoes & Accs > Athletic Shoes",
        )
        # pre_tax_total = $200 > $150 → per_order_fee should be $0
        # basic rate for athletic shoes: 12.7% up to $150, 7% above
        # tier 1: 150 * 0.127 = $19.05
        # tier 2: (200 - 150) * 0.07 = $3.50
        # fee_amount = $22.55; per_order_fee = $0 (waived)
        assert result["final_value_fee"] == Decimal("22.55")

    def test_per_order_fee_30_cents_below_10(self):
        result = self._call(sold_price=Decimal("8.00"), item_cost=Decimal("1.00"), actual_shipping_cost=Decimal("0"))
        # pre_tax_total = $8 ≤ $10 → per_order_fee = $0.30
        # 8 * 0.127 = $1.016 → fee_amount portion; per_order = $0.30
        fvf = result["final_value_fee"]
        fee_amount = fvf - Decimal("0.30")
        assert fee_amount == (Decimal("8") * Decimal("0.127")).quantize(Decimal("0.01"))

    def test_sales_tax_included_in_fvf_basis(self):
        result = self._call(
            sold_price=Decimal("100.00"),
            item_cost=Decimal("20.00"),
            actual_shipping_cost=Decimal("0"),
            sales_tax_rate=Decimal("10"),
        )
        # total_sale = $100 * 1.10 = $110; FVF applied to $110 not $100
        assert result["total_sale"] == Decimal("110.00")
        # payout is from pre_tax_total ($100), not total_sale — tax goes to state
        assert result["pre_tax_total"] == Decimal("100.00")

    def test_promoted_fee_applied_to_total_sale(self):
        result = self._call(
            sold_price=Decimal("100.00"),
            item_cost=Decimal("20.00"),
            actual_shipping_cost=Decimal("0"),
            promoted_rate=Decimal("5"),
            sales_tax_rate=Decimal("0"),
        )
        assert result["promoted_fee"] == Decimal("5.00")

    def test_zero_item_cost_roi(self):
        result = self._call(sold_price=Decimal("10"), item_cost=Decimal("0"), actual_shipping_cost=Decimal("0"))
        assert result["roi_pct"] == Decimal("0")

    def test_negative_net_profit(self):
        result = self._call(
            sold_price=Decimal("5.00"),
            item_cost=Decimal("10.00"),
            actual_shipping_cost=Decimal("5.00"),
        )
        assert result["net_profit"] < Decimal("0")

    def test_tiered_fee_jewellery_watches(self):
        """Watches have a 3-tier fee structure for basic+ stores."""
        # Watches: $1000 at 12.5%, $1000-$5000 at 4%, >$5000 at 3%
        result = self._call(
            sold_price=Decimal("2000.00"),
            item_cost=Decimal("500.00"),
            actual_shipping_cost=Decimal("0"),
            store_level="basic",
            category_name="Jewelry & Watches > Watches, Parts & Accs",
        )
        # tier1: $1000 * 0.125 = $125
        # tier2: ($2000 - $1000) * 0.04 = $40
        # total fee_amount = $165; per_order = $0.40
        # FVF = $165.40
        assert result["final_value_fee"] == Decimal("165.40")


class TestComputePriceForTargetMargin:
    def test_basic_target_margin(self):
        """Price solver should return a price where margin ≈ target."""
        price = compute_price_for_target_margin(
            item_cost=Decimal("10.00"),
            actual_shipping_cost=Decimal("3.00"),
            target_margin_pct=Decimal("30"),
            store_level="basic",
            category_name="All Other Categories",
        )
        # Verify the result achieves the target margin within tolerance
        result = calculate_fees(
            sold_price=price,
            item_cost=Decimal("10.00"),
            actual_shipping_cost=Decimal("3.00"),
            store_level="basic",
            category_name="All Other Categories",
        )
        assert float(result["profit_margin_pct"]) == pytest.approx(30.0, abs=0.1)

    def test_higher_cogs_requires_higher_price(self):
        price_low_cogs = compute_price_for_target_margin(
            item_cost=Decimal("5.00"),
            actual_shipping_cost=Decimal("0"),
            target_margin_pct=Decimal("25"),
            store_level="basic",
            category_name="All Other Categories",
        )
        price_high_cogs = compute_price_for_target_margin(
            item_cost=Decimal("20.00"),
            actual_shipping_cost=Decimal("0"),
            target_margin_pct=Decimal("25"),
            store_level="basic",
            category_name="All Other Categories",
        )
        assert price_high_cogs > price_low_cogs

    def test_starter_store_requires_higher_price(self):
        """Higher fees in starter store should require a higher price to hit same margin."""
        price_basic = compute_price_for_target_margin(
            item_cost=Decimal("10.00"),
            actual_shipping_cost=Decimal("2.00"),
            target_margin_pct=Decimal("20"),
            store_level="basic",
            category_name="All Other Categories",
        )
        price_starter = compute_price_for_target_margin(
            item_cost=Decimal("10.00"),
            actual_shipping_cost=Decimal("2.00"),
            target_margin_pct=Decimal("20"),
            store_level="none",
            category_name="Most Categories",
        )
        assert price_starter > price_basic
