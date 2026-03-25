"""Citation model for tracking references between outputs."""

from sqlalchemy import String, Text, DateTime, ForeignKey, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.database import Base


class CitationType(str, enum.Enum):
    """Citation type classification."""

    AGREE = "agree"  # Agreeing with the cited work
    CRITICIZE = "criticize"  # Criticizing or disagreeing
    DEVELOP = "develop"  # Developing/extending the idea
    REFERENCE = "reference"  # Simple reference


class Citation(Base):
    """Citation model representing references between outputs."""

    __tablename__ = "citations"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Source output (the one doing the citing)
    source_output_id: Mapped[str] = mapped_column(
        String(30), ForeignKey("outputs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Target output (the one being cited)
    target_output_id: Mapped[str] = mapped_column(
        String(30), ForeignKey("outputs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Citation type
    citation_type: Mapped[CitationType] = mapped_column(
        SQLEnum(CitationType, name="citation_type_enum"), nullable=False
    )

    # Excerpt from the cited work
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    source_output: Mapped["Output"] = relationship(
        "Output", foreign_keys=[source_output_id], back_populates="citing"
    )

    target_output: Mapped["Output"] = relationship(
        "Output", foreign_keys=[target_output_id], back_populates="cited_by"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "source_output_id", "target_output_id", "citation_type", name="uq_citation"
        ),
    )

    def __repr__(self) -> str:
        return f"<Citation(id={self.id}, source={self.source_output_id}, target={self.target_output_id}, type={self.citation_type})>"
