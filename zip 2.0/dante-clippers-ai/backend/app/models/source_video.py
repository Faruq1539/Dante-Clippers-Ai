from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base_mixin import TimestampMixin, uuid_pk


class SourceVideo(Base, TimestampMixin):
    __tablename__ = "source_videos"

    id = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # upload | tiktok | instagram | twitch | x  (never "link_scrape" -- see platform integration matrix in docs/tech-spec.md)
    origin: Mapped[str] = mapped_column(String, nullable=False)
    storage_url: Mapped[str] = mapped_column(String, nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(String, default="uploaded")  # uploaded | processing | ready | failed

    user = relationship("User", back_populates="source_videos")
    processing_jobs = relationship("ProcessingJob", back_populates="source_video", cascade="all, delete-orphan")
