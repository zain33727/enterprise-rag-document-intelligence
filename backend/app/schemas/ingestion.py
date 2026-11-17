import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import IngestionJobStatus


class IngestionJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    status: IngestionJobStatus
    attempts: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class IngestionJobListResponse(BaseModel):
    items: list[IngestionJobResponse]
    total: int
