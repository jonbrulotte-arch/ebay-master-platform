import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProfitabilityRecord(Base):
    __tablename__ = "profitability_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_line_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("order_line_items.id", ondelete="SET NULL")
    )
    record_type: Mapped[str] = mapped_column(String(20), nullable=False)  # ACTUAL or PROJECTED
    sale_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    cost_of_goods: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    shipping_cost_to_buyer: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    shipping_cost_from_supplier: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    ebay_final_value_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    ebay_payment_processing_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    ebay_promoted_listing_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    ebay_international_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    ebay_insertion_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    other_fees: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    tax_collected: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total_costs: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    gross_profit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    profit_margin_pct: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    roi_pct: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product")
    order_line_item = relationship("OrderLineItem", back_populates="profitability_records")
