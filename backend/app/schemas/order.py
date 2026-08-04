import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrderLineItemResponse(BaseModel):
    id: uuid.UUID
    ebay_line_item_id: str | None = None
    title: str
    sku: str | None = None
    quantity: int
    unit_price: float
    total_price: float
    ebay_final_value_fee: float | None = None
    ebay_payment_processing_fee: float | None = None
    ebay_promoted_listing_fee: float | None = None
    ebay_international_fee: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: uuid.UUID
    marketplace: str
    ebay_order_id: str
    buyer_username: str | None = None
    order_status: str
    payment_status: str
    total_amount: float
    subtotal: float
    shipping_cost: float
    tax_amount: float
    ebay_fees_total: float | None = None
    currency: str
    shipping_address: dict | None = None
    shipping_carrier: str | None = None
    tracking_number: str | None = None
    shipped_at: datetime | None = None
    paid_at: datetime | None = None
    aliexpress_order_id: str | None = None
    aliexpress_order_status: str | None = None
    aliexpress_tracking_number: str | None = None
    line_items: list[OrderLineItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderShipRequest(BaseModel):
    shipping_carrier: str
    tracking_number: str


class OrderListResponse(BaseModel):
    id: uuid.UUID
    ebay_order_id: str
    buyer_username: str | None = None
    order_status: str
    payment_status: str
    total_amount: float
    currency: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
