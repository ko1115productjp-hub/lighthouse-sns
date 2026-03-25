"""Notification schemas for API requests and responses."""

from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional


class NotificationResponse(BaseModel):
    """Schema for notification response."""

    id: UUID4
    user_id: UUID4
    actor_id: UUID4
    type: str
    output_id: Optional[str] = None
    citation_id: Optional[UUID4] = None
    is_read: bool
    message: Optional[str] = None
    created_at: datetime

    # Actor information
    actor_username: str
    actor_display_name: str
    actor_avatar_url: Optional[str] = None

    # Output preview (if applicable)
    output_content_preview: Optional[str] = None

    model_config = {"from_attributes": True}


class NotificationMarkReadRequest(BaseModel):
    """Request schema to mark notifications as read."""

    notification_ids: list[UUID4]


class NotificationStatsResponse(BaseModel):
    """Notification statistics response."""

    total_count: int
    unread_count: int
