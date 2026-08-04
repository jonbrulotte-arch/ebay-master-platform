import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReturnResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    ebay_return_id: str | None = None
    reason: str | None = None
    buyer_comments: str | None = None
    status: str
    refund_amount: float | None = None
    return_shipping_paid_by: str
    return_tracking_number: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReturnUpdate(BaseModel):
    status: str | None = None
    refund_amount: float | None = None
    return_tracking_number: str | None = None
    return_shipping_paid_by: str | None = None
