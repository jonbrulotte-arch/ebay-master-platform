import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ListingCreate(BaseModel):
    product_id: uuid.UUID
    title: str
    price: float
    quantity_listed: int = 1
    listing_type: str = "FIXED_PRICE"
    listing_duration: str = "GTC"
    marketplace: str = "EBAY_US"
    currency: str = "USD"
    ebay_category_id: str | None = None
    shipping_policy_id: str | None = None
    return_policy_id: str | None = None
    payment_policy_id: str | None = None
    promoted_listing_rate: float | None = None
    listing_template_id: uuid.UUID | None = None
    item_specifics_override: dict | None = None
    description_html: str | None = None


class ListingUpdate(BaseModel):
    title: str | None = None
    price: float | None = None
    quantity_listed: int | None = None
    ebay_category_id: str | None = None
    shipping_policy_id: str | None = None
    return_policy_id: str | None = None
    payment_policy_id: str | None = None
    promoted_listing_rate: float | None = None
    item_specifics_override: dict | None = None
    description_html: str | None = None


class ListingResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    marketplace: str
    ebay_item_id: str | None = None
    listing_type: str
    status: str
    title: str
    price: float
    currency: str
    quantity_listed: int
    quantity_sold: int
    shipping_policy_id: str | None = None
    return_policy_id: str | None = None
    promoted_listing_rate: float | None = None
    ebay_category_id: str | None = None
    started_at: datetime | None = None
    ends_at: datetime | None = None
    last_synced_at: datetime | None = None
    ebay_fees: dict | None = None
    error_messages: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
