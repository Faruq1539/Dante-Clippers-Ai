from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base_mixin import TimestampMixin, uuid_pk


class BrandTemplate(Base, TimestampMixin):
    __tablename__ = "brand_templates"

    id = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    name: Mapped[str] = mapped_column(String, default="My Brand")
    font: Mapped[str] = mapped_column(String, default="Inter")
    primary_color: Mapped[str] = mapped_column(String, default="#000000")
    accent_color: Mapped[str] = mapped_column(String, default="#FFFFFF")
    logo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    caption_style: Mapped[dict] = mapped_column(JSON, default=dict)  # animation, position, size, etc.

    user = relationship("User", back_populates="brand_templates")
