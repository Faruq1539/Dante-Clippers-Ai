from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base_mixin import TimestampMixin, uuid_pk


class Clip(Base, TimestampMixin):
    __tablename__ = "clips"

    id = uuid_pk()
    job_id: Mapped[UUID] = mapped_column(ForeignKey("processing_jobs.id"), nullable=False)
    brand_template_id: Mapped[UUID | None] = mapped_column(ForeignKey("brand_templates.id"), nullable=True)

    start_ts: Mapped[float] = mapped_column(Float, nullable=False)
    end_ts: Mapped[float] = mapped_column(Float, nullable=False)
    highlight_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    storage_url: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending | rendering | ready | failed

    job = relationship("ProcessingJob", back_populates="clips")
    publish_jobs = relationship("PublishJob", back_populates="clip", cascade="all, delete-orphan")
