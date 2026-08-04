import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AliExpressProduct(BaseModel):
    product_id: str
    title: str
    sale_price_usd: float
    original_price_usd: float | None = None
    image_url: str | None = None
    product_url: str | None = None
    store_name: str | None = None
    store_id: str | None = None
    avg_star_rating: float | None = None
    total_orders: int | None = None
    shipping_lead_days: int | None = None


class AliExpressSearchResponse(BaseModel):
    products: list[AliExpressProduct]
    total: int
    page: int
    page_size: int
    total_pages: int


class AliExpressImportRequest(BaseModel):
    product_id: str
    title: str | None = None
    sale_price_usd: float
    image_url: str | None = None
    product_url: str | None = None
    store_name: str | None = None
    store_id: str | None = None
    sku: str | None = None
    shipping_cost_usd: float = 0.0
    # If supplier_id is provided, link to existing supplier; otherwise create new
    supplier_id: uuid.UUID | None = None


class AliExpressImportResponse(BaseModel):
    product_id: uuid.UUID
    supplier_id: uuid.UUID
    product_supplier_id: uuid.UUID
    sku: str
    title: str


class SupplierPriceCheckRequest(BaseModel):
    product_supplier_ids: list[uuid.UUID]


class SupplierPriceCheckResult(BaseModel):
    product_supplier_id: uuid.UUID
    old_price: float
    new_price: float
    changed: bool
    change_pct: float


class SupplierPriceCheckResponse(BaseModel):
    checked: int
    changed: int
    results: list[SupplierPriceCheckResult]


class ForwardOrderRequest(BaseModel):
    sku_id: str | None = None  # AliExpress SKU ID for this product variant
    logistics_service: str = "YANWEN_REGULAR_AIRMAIL"


class ForwardOrderResponse(BaseModel):
    order_id: uuid.UUID
    aliexpress_order_id: str
    status: str


class TrackingSyncResponse(BaseModel):
    synced: int
    failed: int
    details: list[dict]


class CurrencyRateResponse(BaseModel):
    from_currency: str
    to_currency: str
    rate: float
    safety_margin_pct: float
    effective_rate: float  # rate * (1 + safety_margin_pct/100)
    updated_at: datetime
