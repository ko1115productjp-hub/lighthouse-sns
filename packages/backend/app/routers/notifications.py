"""Notifications API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.models.notification import Notification
from app.models.output import Output
from app.schemas.notification import (
    NotificationResponse,
    NotificationMarkReadRequest,
    NotificationStatsResponse,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    unread_only: bool = Query(False, description="Show only unread notifications"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[NotificationResponse]:
    """
    Get notifications for current user.

    Args:
        limit: Maximum number of results
        offset: Number of results to skip
        unread_only: Filter for unread notifications only
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of notifications
    """
    # Build query
    query = (
        select(Notification, User, Output)
        .join(User, User.id == Notification.actor_id)
        .outerjoin(Output, Output.id == Notification.output_id)
        .where(Notification.user_id == current_user.id)
    )

    if unread_only:
        query = query.where(Notification.is_read == False)  # noqa: E712

    query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    notifications = []
    for notification, actor, output in rows:
        # Create output preview (first 100 chars)
        output_preview = None
        if output:
            output_preview = (
                output.content[:100] + "..." if len(output.content) > 100 else output.content
            )

        notifications.append(
            NotificationResponse(
                id=notification.id,
                user_id=notification.user_id,
                actor_id=notification.actor_id,
                type=notification.type.value,
                output_id=notification.output_id,
                citation_id=notification.citation_id,
                is_read=notification.is_read,
                message=notification.message,
                created_at=notification.created_at,
                actor_username=actor.username,
                actor_display_name=actor.display_name,
                actor_avatar_url=actor.avatar_url,
                output_content_preview=output_preview,
            )
        )

    return notifications


@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationStatsResponse:
    """
    Get notification statistics for current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Notification statistics
    """
    # Total count
    total_count = await db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == current_user.id)
    ) or 0

    # Unread count
    unread_count = await db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)  # noqa: E712
    ) or 0

    return NotificationStatsResponse(
        total_count=total_count,
        unread_count=unread_count,
    )


@router.post("/mark-read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notifications_read(
    request: NotificationMarkReadRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Mark notifications as read.

    Args:
        request: List of notification IDs to mark as read
        current_user: Current authenticated user
        db: Database session
    """
    # Update notifications
    await db.execute(
        update(Notification)
        .where(
            Notification.id.in_(request.notification_ids),
            Notification.user_id == current_user.id,  # Security: only own notifications
        )
        .values(is_read=True)
    )

    await db.commit()


@router.post("/mark-all-read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Mark all notifications as read for current user.

    Args:
        current_user: Current authenticated user
        db: Database session
    """
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id)
        .values(is_read=True)
    )

    await db.commit()
