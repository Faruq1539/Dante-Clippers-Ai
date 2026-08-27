from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base_mixin import TimestampMixin, uuid_pk


class CreditTransaction(Base, TimestampMixin):
    __tablename__ = "credit_transactions"

    id = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # positive = grant/purchase, negative = spend
    reason: Mapped[str] = mapped_column(String, nullable=False)  # monthly_grant | purchase | spend_processing

    user = relationship("User", back_populates="credit_transactions")
