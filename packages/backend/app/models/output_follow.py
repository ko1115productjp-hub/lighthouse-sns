"""OutputFollow model for output following relationships."""

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.database import Base


class OutputFollow(Base):
    """OutputFollow model representing user following specific outputs."""

    __tablename__ = "output_follows"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # User who is following the output
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Output being followed (String type as outputs.id is String)
    output_id: Mapped[str] = mapped_column(
        String(30), ForeignKey("outputs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="output_follows")
    output: Mapped["Output"] = relationship("Output", back_populates="followers")

    # Constraints - one user can only follow an output once
    __table_args__ = (UniqueConstraint("user_id", "output_id", name="uq_user_output"),)

    def __repr__(self) -> str:
        return f"<OutputFollow(id={self.id}, user_id={self.user_id}, output_id={self.output_id})>"
