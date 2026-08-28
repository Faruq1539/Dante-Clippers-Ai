from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base
from app.models.base_mixin import TimestampMixin, uuid_pk


class PublishJob(Base, TimestampMixin):
    __tablename__ = "publish_jobs"

    id = uuid_pk()
    clip_id: Mapped[UUID] = mapped_column(ForeignKey("clips.id"), nullable=False)
    connected_account_id: Mapped[UUID] = mapped_column(ForeignKey("connected_accounts.id"), nullable=False)

    platform: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    caption: Mapped[str | None] = mapped_column(String, nullable=True)

    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String, default="scheduled")  # scheduled | publishing | published | failed
    platform_post_id: Mapped[str | None] = mapped_column(String, nullable=True)

    clip = relationship("Clip", back_populates="publish_jobs")
