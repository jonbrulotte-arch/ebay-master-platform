import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SupplierCreate(BaseModel):
    name: str
    platform: str = "ALIEXPRESS"
    store_url: str | None = None
    store_id: str | None = None
    contact_info: dict | None = None
    reliability_rating: float | None = None
    avg_shipping_days: int | None = None
    notes: str | None = None


class SupplierUpdate(BaseModel):
    name: str | None = None
    platform: str | None = None
    store_url: str | None = None
    store_id: str | None = None
    contact_info: dict | None = None
    reliability_rating: float | None = None
    avg_shipping_days: int | None = None
    notes: str | None = None
    is_active: bool | None = None


class SupplierResponse(BaseModel):
    id: uuid.UUID
    name: str
    platform: str
    store_url: str | None = None
    store_id: str | None = None
    contact_info: dict | None = None
    reliability_rating: float | None = None
    avg_shipping_days: int | None = None
    notes: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductSupplierCreate(BaseModel):
    supplier_id: uuid.UUID
    supplier_product_url: str | None = None
    supplier_product_id: str | None = None
    unit_cost: float
    currency: str = "USD"
    shipping_cost: float = 0
    min_order_quantity: int = 1
    is_preferred: bool = False


class ProductSupplierUpdate(BaseModel):
    supplier_product_url: str | None = None
    supplier_product_id: str | None = None
    unit_cost: float | None = None
    currency: str | None = None
    shipping_cost: float | None = None
    min_order_quantity: int | None = None
    is_preferred: bool | None = None


class ProductSupplierResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    supplier_id: uuid.UUID
    supplier_product_url: str | None = None
    supplier_product_id: str | None = None
    unit_cost: float
    currency: str
    shipping_cost: float | None = None
    min_order_quantity: int
    is_preferred: bool
    last_price_check_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
