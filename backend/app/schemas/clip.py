import uuid
from pydantic import BaseModel


class ClipOut(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    start_ts: float
    end_ts: float
    highlight_score: float | None
    storage_url: str | None
    status: str

    class Config:
        from_attributes = True


class ClipUpdate(BaseModel):
    brand_template_id: uuid.UUID | None = None
    start_ts: float | None = None
    end_ts: float | None = None
