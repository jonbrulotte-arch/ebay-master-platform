import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    marketplace: Mapped[str] = mapped_column(String(20), default="EBAY_US")
    ebay_item_id: Mapped[str | None] = mapped_column(String(50), unique=True, index=True)
    listing_type: Mapped[str] = mapped_column(String(20), default="FIXED_PRICE")
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    quantity_listed: Mapped[int] = mapped_column(Integer, default=1)
    quantity_sold: Mapped[int] = mapped_column(Integer, default=0)
    shipping_policy_id: Mapped[str | None] = mapped_column(String(100))
    return_policy_id: Mapped[str | None] = mapped_column(String(100))
    payment_policy_id: Mapped[str | None] = mapped_column(String(100))
    listing_duration: Mapped[str] = mapped_column(String(20), default="GTC")
    promoted_listing_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    ebay_category_id: Mapped[str | None] = mapped_column(String(50))
    ebay_store_category_id: Mapped[str | None] = mapped_column(String(50))
    listing_template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listing_templates.id", ondelete="SET NULL")
    )
    item_specifics_override: Mapped[dict | None] = mapped_column(JSONB)
    description_html: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ebay_fees: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    error_messages: Mapped[dict | None] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    product = relationship("Product", back_populates="listings")
    user = relationship("User", back_populates="listings")
    template = relationship("ListingTemplate")
    order_line_items = relationship("OrderLineItem", back_populates="listing")
