import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    locale: str = "en"


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    locale: str
    plan_tier: str
    credit_balance: int
    credit_renews_at: datetime | None

    class Config:
        from_attributes = True
