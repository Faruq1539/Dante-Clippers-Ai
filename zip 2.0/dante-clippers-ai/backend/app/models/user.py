from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base
from app.models.base_mixin import TimestampMixin, uuid_pk


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = uuid_pk()
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    locale: Mapped[str] = mapped_column(String, default="en")
    plan_tier: Mapped[str] = mapped_column(String, default="free")  # free | pro

    credit_balance: Mapped[int] = mapped_column(Integer, default=0)
    credit_renews_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    connected_accounts = relationship("ConnectedAccount", back_populates="user", cascade="all, delete-orphan")
    source_videos = relationship("SourceVideo", back_populates="user", cascade="all, delete-orphan")
    credit_transactions = relationship("CreditTransaction", back_populates="user", cascade="all, delete-orphan")
    brand_templates = relationship("BrandTemplate", back_populates="user", cascade="all, delete-orphan")
