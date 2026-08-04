import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageCreate(BaseModel):
    order_id: uuid.UUID | None = None
    buyer_username: str
    subject: str | None = None
    body: str | None = None


class MessageResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    order_id: uuid.UUID | None = None
    ebay_message_id: str | None = None
    buyer_username: str
    direction: str
    subject: str | None = None
    body: str | None = None
    is_read: bool
    responded_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
