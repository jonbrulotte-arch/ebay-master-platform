import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
    sale_price: float
    category_id: str | None = None
    promoted_listing_rate: float | None = None
    is_international: bool = False
    shipping_cost: float = 0
    cost_of_goods: float = 0
    supplier_shipping_cost: float = 0


class FeeCalculationResponse(BaseModel):
    sale_price: float
    cost_of_goods: float
    supplier_shipping_cost: float
    ebay_final_value_fee: float
    ebay_payment_processing_fee: float
    ebay_promoted_listing_fee: float
    ebay_international_fee: float
    shipping_cost: float
    total_fees: float
    total_costs: float
    gross_profit: float
    profit_margin_pct: float
    roi_pct: float
