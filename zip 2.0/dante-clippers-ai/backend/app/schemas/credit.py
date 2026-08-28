import uuid
from datetime import datetime
from pydantic import BaseModel


class CreditTransactionOut(BaseModel):
    id: uuid.UUID
    amount: int
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True


class CreditBalanceOut(BaseModel):
    credit_balance: int
    credit_renews_at: datetime | None
