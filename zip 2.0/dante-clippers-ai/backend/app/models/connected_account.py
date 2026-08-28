from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base_mixin import TimestampMixin, uuid_pk


class ConnectedAccount(Base, TimestampMixin):
    """
    Stores OAuth tokens for a user's connected social platform.
    Tokens should be encrypted at rest in production (e.g. via KMS envelope
    encryption or a secrets manager) -- this column stores ciphertext, not
    plaintext tokens.
    """

    __tablename__ = "connected_accounts"

    id = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    platform: Mapped[str] = mapped_column(String, nullable=False)  # tiktok | instagram | twitch | youtube | x
    platform_user_id: Mapped[str] = mapped_column(String, nullable=False)
    platform_username: Mapped[str | None] = mapped_column(String, nullable=True)

    access_token_encrypted: Mapped[str] = mapped_column(String, nullable=False)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(String, nullable=True)
    scopes: Mapped[dict] = mapped_column(JSON, default=dict)

    user = relationship("User", back_populates="connected_accounts")
