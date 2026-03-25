"""User model for authentication and profile management."""

from sqlalchemy import Boolean, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.database import Base


class User(Base):
    """User model representing platform users."""

    __tablename__ = "users"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Authentication
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Null for social login

    # OAuth fields
    oauth_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 'google', 'line', etc.
    oauth_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Provider's user ID

    # Profile
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Verification
    age_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    has_agreed_to_protocol: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # Lighthouse Protocol agreement

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # For anonymization

    # Relationships
    outputs: Mapped[list["Output"]] = relationship(
        "Output", back_populates="author", cascade="all, delete-orphan"
    )
    agreements: Mapped[list["Agreement"]] = relationship(
        "Agreement", back_populates="user", cascade="all, delete-orphan"
    )

    # Following relationships
    following: Mapped[list["Follow"]] = relationship(
        "Follow",
        foreign_keys="Follow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan",
    )
    followers: Mapped[list["Follow"]] = relationship(
        "Follow",
        foreign_keys="Follow.followed_id",
        back_populates="followed",
        cascade="all, delete-orphan",
    )

    output_follows: Mapped[list["OutputFollow"]] = relationship(
        "OutputFollow", back_populates="user", cascade="all, delete-orphan"
    )

    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        foreign_keys="Notification.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"
