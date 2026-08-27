from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base_mixin import TimestampMixin, uuid_pk


class ProcessingJob(Base, TimestampMixin):
    __tablename__ = "processing_jobs"

    id = uuid_pk()
    source_video_id: Mapped[UUID] = mapped_column(ForeignKey("source_videos.id"), nullable=False)

    # queued -> transcribing -> scoring -> rendering -> done  (or failed at any stage)
    status: Mapped[str] = mapped_column(String, default="queued")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_video = relationship("SourceVideo", back_populates="processing_jobs")
    clips = relationship("Clip", back_populates="job", cascade="all, delete-orphan")
