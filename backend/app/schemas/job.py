import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobHistoryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    job_type: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    items_processed: int
    items_failed: int
    result_summary: dict | None = None
    triggered_by: str
    celery_task_id: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ManualTriggerRequest(BaseModel):
    job_type: str
