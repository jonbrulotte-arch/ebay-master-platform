"""Unit tests for AliExpress service helper functions."""
import pytest

from app.services.aliexpress_service import (
    _CNY_USD_RATE,
    _DEFAULT_SAFETY_MARGIN_PCT,
    _parse_product,
    convert_cny_to_usd,
    get_currency_info,
)


class TestCurrencyConversion:
    def test_basic_conversion(self):
        result = convert_cny_to_usd(100.0, safety_margin_pct=0.0)
        assert result == round(100.0 * _CNY_USD_RATE, 2)

    def test_safety_margin_increases_rate(self):
        no_margin = convert_cny_to_usd(100.0, safety_margin_pct=0.0)
        with_margin = convert_cny_to_usd(100.0, safety_margin_pct=2.0)
        assert with_margin > no_margin

    def test_default_margin(self):
        result = convert_cny_to_usd(100.0)
        expected = round(100.0 * _CNY_USD_RATE * (1 + _DEFAULT_SAFETY_MARGIN_PCT / 100), 2)
        assert result == expected

    def test_zero_amount(self):
        assert convert_cny_to_usd(0.0) == 0.0


class TestGetCurrencyInfo:
    def test_returns_all_fields(self):
        info = get_currency_info()
        assert "from_currency" in info
        assert "to_currency" in info
        assert "rate" in info
        assert "safety_margin_pct" in info
        assert "effective_rate" in info
        assert "updated_at" in info

    def test_effective_rate_reflects_margin(self):
        info = get_currency_info(safety_margin_pct=5.0)
        expected = _CNY_USD_RATE * 1.05
        assert abs(info["effective_rate"] - expected) < 0.000001

    def test_from_to_currencies(self):
        info = get_currency_info()
        assert info["from_currency"] == "CNY"
        assert info["to_currency"] == "USD"


class TestParseProduct:
    def test_parses_basic_fields(self):
        raw = {
            "product_id": "12345",
            "product_title": "Test Widget",
            "target_sale_price": "9.99",
            "original_price": "14.99",
            "product_main_image_url": "https://example.com/img.jpg",
            "product_detail_url": "https://aliexpress.com/item/12345.html",
            "shop_name": "Test Store",
            "shop_id": "99",
            "evaluate_rate": "80",
            "lastest_volume": "1500",
        }
        product = _parse_product(raw)
        assert product.product_id == "12345"
        assert product.title == "Test Widget"
        assert product.sale_price_usd == 9.99
        assert product.original_price_usd == 14.99
        assert product.store_name == "Test Store"
        assert product.total_orders == 1500

    def test_star_rating_converts_from_100(self):
        raw = {
            "product_id": "1",
            "product_title": "Item",
            "target_sale_price": "5.00",
            "evaluate_rate": "80",  # 80/100 → 4.0 stars (80/20 = 4)
        }
        product = _parse_product(raw)
        assert product.avg_star_rating == pytest.approx(4.0)

    def test_missing_optional_fields(self):
        raw = {
            "product_id": "2",
            "product_title": "Minimal Item",
            "target_sale_price": "3.00",
        }
        product = _parse_product(raw)
        assert product.image_url is None
        assert product.store_name is None
        assert product.total_orders == 0
