"""OutputHistory model for tracking all content edits."""

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.database import Base


class OutputHistory(Base):
    """OutputHistory model for immutable edit history."""

    __tablename__ = "output_history"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Foreign key to Output
    output_id: Mapped[str] = mapped_column(
        String(30), ForeignKey("outputs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Version number
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Content snapshot
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Hash chain
    hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256 of this version
    previous_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # Previous version hash

    # Editor (who made this edit)
    edited_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    output: Mapped["Output"] = relationship("Output", back_populates="history")

    def __repr__(self) -> str:
        return f"<OutputHistory(id={self.id}, output_id={self.output_id}, version={self.version})>"
