"""Agreement model for users agreeing with outputs."""

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.database import Base


class Agreement(Base):
    """Agreement model representing user agreement with outputs."""

    __tablename__ = "agreements"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Foreign key to User
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Foreign key to Output
    output_id: Mapped[str] = mapped_column(
        String(30), ForeignKey("outputs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Timestamp (for tracking early agreement - "foresight")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="agreements")
    output: Mapped["Output"] = relationship("Output", back_populates="agreements")

    # Constraints - one user can only agree once per output
    __table_args__ = (UniqueConstraint("user_id", "output_id", name="uq_user_output_agreement"),)

    def __repr__(self) -> str:
        return f"<Agreement(id={self.id}, user_id={self.user_id}, output_id={self.output_id})>"
