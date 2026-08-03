import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    sku: str
    title: str
    description: str | None = None
    category_id: str | None = None
    condition: str = "NEW"
    condition_description: str | None = None
    brand: str | None = None
    mpn: str | None = None
    upc: str | None = None
    ean: str | None = None
    isbn: str | None = None
    item_specifics: dict | None = None
    weight_oz: float | None = None
    dimensions: dict | None = None
    tags: list[str] | None = None
    notes: str | None = None


class ProductUpdate(BaseModel):
    sku: str | None = None
    title: str | None = None
    description: str | None = None
    category_id: str | None = None
    condition: str | None = None
    condition_description: str | None = None
    brand: str | None = None
    mpn: str | None = None
    upc: str | None = None
    ean: str | None = None
    isbn: str | None = None
    item_specifics: dict | None = None
    weight_oz: float | None = None
    dimensions: dict | None = None
    tags: list[str] | None = None
    notes: str | None = None
    is_active: bool | None = None


class ProductImageResponse(BaseModel):
    id: uuid.UUID
    url: str
    position: int
    is_primary: bool
    original_filename: str | None = None
    width: int | None = None
    height: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductResponse(BaseModel):
    id: uuid.UUID
    sku: str
    title: str
    description: str | None = None
    category_id: str | None = None
    condition: str
    condition_description: str | None = None
    brand: str | None = None
    mpn: str | None = None
    upc: str | None = None
    ean: str | None = None
    isbn: str | None = None
    item_specifics: dict | None = None
    weight_oz: float | None = None
    dimensions: dict | None = None
    is_active: bool
    tags: list[str] | None = None
    notes: str | None = None
    images: list[ProductImageResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    id: uuid.UUID
    sku: str
    title: str
    brand: str | None = None
    condition: str
    category_id: str | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
