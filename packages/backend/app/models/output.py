"""Output (Post) model for user-generated content."""

from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from datetime import datetime
import uuid
import enum
from typing import Any

from app.database import Base


class VisibilityEnum(str, enum.Enum):
    """Output visibility types."""

    PUBLIC = "public"
    PRIVATE = "private"


class AIReviewStatus(str, enum.Enum):
    """AI review status types."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class CategoryEnum(str, enum.Enum):
    """Content category types."""

    SCIENCE = "science"
    ART = "art"
    PHILOSOPHY = "philosophy"
    TECHNOLOGY = "technology"
    SOCIETY = "society"
    SCRIPT = "script"  # 台本（映画、舞台、Podcast等）
    PLACE = "place"  # 場所
    EXPERIENCE = "experience"  # 体験（ユーザー固有の一次情報）
    OTHER = "other"


class Output(Base):
    """Output model representing user posts/content."""

    __tablename__ = "outputs"

    # Primary key - custom format: OUT-YYYY-MMDD-HASH
    id: Mapped[str] = mapped_column(String(30), primary_key=True)

    # Foreign key to User
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Content
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)  # Optional title
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[CategoryEnum] = mapped_column(
        SQLEnum(CategoryEnum, name="category_enum", values_callable=lambda x: [e.name for e in x]), nullable=False
    )
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(30)), nullable=False, default=list)

    # Visibility and AI review
    visibility: Mapped[VisibilityEnum] = mapped_column(
        SQLEnum(VisibilityEnum, name="visibility"),
        default=VisibilityEnum.PUBLIC,
        nullable=False,
        index=True,
    )
    ai_review_status: Mapped[AIReviewStatus] = mapped_column(
        SQLEnum(AIReviewStatus, name="ai_review_status"),
        default=AIReviewStatus.PENDING,
        nullable=False,
    )
    novelty_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, index=True
    )  # 0-100, Phase 2
    ai_review_flagged_categories: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(50)), nullable=True
    )  # Categories flagged by moderation (e.g., 'violence', 'hate')
    ai_review_feedback: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # User-friendly feedback message for rejected content

    # Originality checking (Lighthouse Protocol - 査読1)
    content_embedding: Mapped[Any | None] = mapped_column(
        Vector(1536), nullable=True
    )  # OpenAI embedding vector for similarity search
    originality_score: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Originality score from LLM judgment (0-100)
    ai_generated_probability: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Probability that content is AI-generated (0-100%)
    originality_warnings: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text), nullable=True
    )  # Array of warning messages from originality checks
    originality_reasoning: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Reasoning from LLM judgment explaining the originality score

    # Referenced entity (for reviews of places, books, movies, etc.)
    referenced_entity_type: Mapped[str | None] = mapped_column(
        String(20), nullable=True, index=True
    )  # 'place', 'book', 'movie', 'stage', 'concert', null
    referenced_entity_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )  # External API ID (Google Place ID, ISBN, TMDb ID, etc.)
    referenced_entity_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )  # Metadata from external APIs

    # Hash chain (for immutability)
    content_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # SHA-256 of content only
    hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )  # SHA-256 of full output (content + metadata + timestamp)
    previous_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )  # Hash of previous version (for edit history chain)

    # Version control
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    author: Mapped["User"] = relationship("User", back_populates="outputs")

    history: Mapped[list["OutputHistory"]] = relationship(
        "OutputHistory", back_populates="output", cascade="all, delete-orphan"
    )

    # Citations - this output cites others
    citing: Mapped[list["Citation"]] = relationship(
        "Citation",
        foreign_keys="Citation.source_output_id",
        back_populates="source_output",
        cascade="all, delete-orphan",
    )

    # Citations - this output is cited by others
    cited_by: Mapped[list["Citation"]] = relationship(
        "Citation",
        foreign_keys="Citation.target_output_id",
        back_populates="target_output",
        cascade="all, delete-orphan",
    )

    agreements: Mapped[list["Agreement"]] = relationship(
        "Agreement", back_populates="output", cascade="all, delete-orphan"
    )

    followers: Mapped[list["OutputFollow"]] = relationship(
        "OutputFollow", back_populates="output", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Output(id={self.id}, user_id={self.user_id}, visibility={self.visibility})>"
