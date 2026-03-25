"""Follow-related Pydantic schemas."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


# ============================================================================
# User Follow Schemas
# ============================================================================


class FollowCreate(BaseModel):
    """Schema for creating a user follow relationship."""

    followed_id: UUID


class FollowResponse(BaseModel):
    """Schema for user follow response."""

    id: UUID
    follower_id: UUID
    followed_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FollowStats(BaseModel):
    """Schema for user follow statistics."""

    follower_count: int
    following_count: int
    is_following: bool = False  # Whether current user is following this user


# ============================================================================
# Output Follow Schemas
# ============================================================================


class OutputFollowCreate(BaseModel):
    """Schema for creating an output follow relationship."""

    output_id: str


class OutputFollowResponse(BaseModel):
    """Schema for output follow response."""

    id: UUID
    user_id: UUID
    output_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OutputFollowStats(BaseModel):
    """Schema for output follow statistics."""

    follower_count: int
    is_following: bool = False  # Whether current user is following this output
