import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class PricingRuleCreate(BaseModel):
    product_id: uuid.UUID | None = None
    name: str
    rule_type: str = "MIN_MARGIN"
    min_margin_pct: float | None = None
    min_price: float | None = None
    max_price: float | None = None
    target_margin_pct: float | None = None
    reprice_strategy: str = "TARGET_MARGIN"
    priority: int = 0


class PricingRuleUpdate(BaseModel):
    name: str | None = None
    rule_type: str | None = None
    min_margin_pct: float | None = None
    min_price: float | None = None
    max_price: float | None = None
    target_margin_pct: float | None = None
    reprice_strategy: str | None = None
    is_active: bool | None = None
    priority: int | None = None


class PricingRuleResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID | None = None
    name: str
    rule_type: str
    min_margin_pct: float | None = None
    min_price: float | None = None
    max_price: float | None = None
    target_margin_pct: float | None = None
    reprice_strategy: str
    is_active: bool
    priority: int
    last_triggered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PriceChangeLogResponse(BaseModel):
    id: uuid.UUID
    listing_id: uuid.UUID
    product_id: uuid.UUID
    pricing_rule_id: uuid.UUID | None = None
    old_price: float
    new_price: float
    reason: str
    reason_detail: str | None = None
    applied_to_ebay: bool
    ebay_update_error: str | None = None
    triggered_by: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeeCalculationRequest(BaseModel):
    sold_price: float
    item_cost: float = 0.0
    actual_shipping_cost: float = 0.0
    store_level: str = "basic"
    category_name: str = "All Other Categories"
    shipping_charge_to_buyer: float = 0.0
    seller_discount_pct: float = 0.0
    promoted_rate: float = 0.0
    sales_tax_rate: float = 0.0
    is_top_rated_seller: bool = False

    @field_validator("store_level")
    @classmethod
    def validate_store_level(cls, v: str) -> str:
        valid = {"none", "starter", "basic", "premium", "anchor", "enterprise"}
        if v.lower() not in valid:
            raise ValueError(f"store_level must be one of {valid}")
        return v.lower()


class FeeCalculationResponse(BaseModel):
    sold_price: float
    seller_discount_amount: float
    effective_sold_price: float
    shipping_charge_to_buyer: float
    pre_tax_total: float
    sales_tax_amount: float
    total_sale: float
    final_value_fee: float
    promoted_fee: float
    total_fees: float
    payout: float
    item_cost: float
    actual_shipping_cost: float
    net_profit: float
    profit_margin_pct: float
    roi_pct: float


class UserSettingsRequest(BaseModel):
    ebay_store_level: str | None = None
    is_top_rated_seller: bool | None = None
    default_promoted_rate: float | None = None
    default_sales_tax_rate: float | None = None
    default_fee_category: str | None = None

    @field_validator("ebay_store_level")
    @classmethod
    def validate_store_level(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid = {"none", "starter", "basic", "premium", "anchor", "enterprise"}
        if v.lower() not in valid:
            raise ValueError(f"ebay_store_level must be one of {valid}")
        return v.lower()


class UserSettingsResponse(BaseModel):
    ebay_store_level: str
    is_top_rated_seller: bool
    default_promoted_rate: float
    default_sales_tax_rate: float
    default_fee_category: str
