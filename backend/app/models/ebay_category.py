from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EbayCategory(Base):
    __tablename__ = "ebay_category_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    marketplace: Mapped[str] = mapped_column(String(20), default="EBAY_US")
    category_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category_name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_category_id: Mapped[str | None] = mapped_column(String(50))
    level: Mapped[int] = mapped_column(Integer, default=0)
    leaf_category: Mapped[bool] = mapped_column(Boolean, default=False)
    required_item_specifics: Mapped[dict | None] = mapped_column(JSONB, default=list)
    recommended_item_specifics: Mapped[dict | None] = mapped_column(JSONB, default=list)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
