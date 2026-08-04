import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InventoryUpdate(BaseModel):
    quantity_available: int | None = None
    quantity_reserved: int | None = None
    reorder_point: int | None = None
    reorder_quantity: int | None = None
    location: str | None = None


class InventoryAdjust(BaseModel):
    adjustment: int
    reason: str | None = None


class InventoryResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    quantity_available: int
    quantity_reserved: int
    reorder_point: int | None = None
    reorder_quantity: int | None = None
    location: str | None = None
    last_checked_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryWithProductResponse(InventoryResponse):
    product_sku: str | None = None
    product_title: str | None = None
