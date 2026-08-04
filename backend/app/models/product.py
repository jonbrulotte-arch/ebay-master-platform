import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    sku: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[str | None] = mapped_column(String(50))
    condition: Mapped[str] = mapped_column(String(20), default="NEW")
    condition_description: Mapped[str | None] = mapped_column(Text)
    brand: Mapped[str | None] = mapped_column(String(255))
    mpn: Mapped[str | None] = mapped_column(String(255))
    upc: Mapped[str | None] = mapped_column(String(50))
    ean: Mapped[str | None] = mapped_column(String(50))
    isbn: Mapped[str | None] = mapped_column(String(50))
    item_specifics: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    weight_oz: Mapped[float | None] = mapped_column(Numeric(10, 2))
    dimensions: Mapped[dict | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete", order_by="ProductImage.position")
    suppliers = relationship("ProductSupplier", back_populates="product", cascade="all, delete")
    inventory = relationship("Inventory", back_populates="product", uselist=False, cascade="all, delete")
    listings = relationship("Listing", back_populates="product", cascade="all, delete")
    pricing_rules = relationship("PricingRule", back_populates="product", cascade="all, delete")
