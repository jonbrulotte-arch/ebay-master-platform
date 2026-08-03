import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    ebay_user_id: Mapped[str | None] = mapped_column(String(255))
    settings: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    ebay_credentials = relationship("EbayCredential", back_populates="user", cascade="all, delete")
    products = relationship("Product", back_populates="user", cascade="all, delete")
    listings = relationship("Listing", back_populates="user", cascade="all, delete")
    orders = relationship("Order", back_populates="user", cascade="all, delete")
    suppliers = relationship("Supplier", back_populates="user", cascade="all, delete")
    pricing_rules = relationship("PricingRule", back_populates="user", cascade="all, delete")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete")
