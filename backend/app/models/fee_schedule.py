import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FeeSchedule(Base):
    __tablename__ = "fee_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    marketplace: Mapped[str] = mapped_column(String(20), default="EBAY_US")
    category_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category_name: Mapped[str | None] = mapped_column(String(255))
    final_value_fee_pct: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    final_value_fee_cap: Mapped[float | None] = mapped_column(Numeric(10, 2))
    payment_processing_pct: Mapped[float] = mapped_column(Numeric(6, 4), default=2.35)
    payment_processing_fixed: Mapped[float] = mapped_column(Numeric(10, 2), default=0.25)
    international_fee_pct: Mapped[float] = mapped_column(Numeric(6, 4), default=1.65)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
