from datetime import date

from pydantic import BaseModel


class DashboardKPIs(BaseModel):
    total_revenue_today: float = 0
    total_orders_today: int = 0
    pending_orders: int = 0
    items_sold_today: int = 0
    average_margin_pct: float = 0
    low_stock_count: int = 0
    active_listings: int = 0
    margin_alerts: int = 0


class SalesSummary(BaseModel):
    period: str
    date: date
    revenue: float
    orders: int
    units_sold: int
    gross_profit: float
    avg_margin_pct: float


class TopProduct(BaseModel):
    product_id: str
    sku: str
    title: str
    total_revenue: float
    total_profit: float
    units_sold: int
    avg_margin_pct: float


class CategoryPerformance(BaseModel):
    category_id: str
    category_name: str | None = None
    revenue: float
    profit: float
    units_sold: int
    avg_margin_pct: float
    listing_count: int
