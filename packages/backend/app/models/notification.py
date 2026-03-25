"""Notification model for user notifications."""

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.database import Base


class NotificationType(str, enum.Enum):
    """Notification types."""

    FOLLOW = "follow"  # Someone followed you
    UNFOLLOW = "unfollow"  # Someone unfollowed you
    CITATION = "citation"  # Your output was cited
    AGREEMENT = "agreement"  # Someone agreed with your output
    OUTPUT_FOLLOW = "output_follow"  # Someone followed your output


class Notification(Base):
    """Notification model for user notifications."""

    __tablename__ = "notifications"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Recipient
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Actor (who triggered the notification)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Notification type
    type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType, name="notification_type_enum"),
        nullable=False,
        index=True,
    )

    # Related entity (optional)
    output_id: Mapped[str | None] = mapped_column(
        String(30), ForeignKey("outputs.id", ondelete="CASCADE"), nullable=True
    )
    citation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="CASCADE"), nullable=True
    )

    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Message (optional custom message)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="notifications")
    actor: Mapped["User"] = relationship("User", foreign_keys=[actor_id])
    output: Mapped["Output"] = relationship("Output")
    citation: Mapped["Citation"] = relationship("Citation")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type})>"
