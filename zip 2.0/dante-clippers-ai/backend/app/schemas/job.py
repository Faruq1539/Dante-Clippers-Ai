import uuid
from datetime import datetime
from pydantic import BaseModel


class ProcessingJobCreate(BaseModel):
    source_video_id: uuid.UUID


class ProcessingJobOut(BaseModel):
    id: uuid.UUID
    source_video_id: uuid.UUID
    status: str
    error_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True
