import uuid
from datetime import datetime
from pydantic import BaseModel


class SourceVideoCreate(BaseModel):
    origin: str  # upload | tiktok | instagram | twitch | x
    storage_url: str
    duration_seconds: int | None = None


class SourceVideoOut(BaseModel):
    id: uuid.UUID
    origin: str
    storage_url: str
    duration_seconds: int | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
