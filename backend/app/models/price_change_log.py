import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PriceChangeLog(Base):
    __tablename__ = "price_change_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    pricing_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pricing_rules.id", ondelete="SET NULL")
    )
    old_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    new_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    reason: Mapped[str] = mapped_column(String(30), nullable=False)
    reason_detail: Mapped[str | None] = mapped_column(Text)
    applied_to_ebay: Mapped[bool] = mapped_column(Boolean, default=False)
    ebay_update_error: Mapped[str | None] = mapped_column(Text)
    triggered_by: Mapped[str] = mapped_column(String(20), default="SCHEDULER")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
