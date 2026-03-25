"""User management API endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.models.follow import Follow
from app.schemas.user import (
    UserUpdate,
    UserResponse,
    UserPublicResponse,
    UserListItemResponse,
)
from app.schemas.follow import FollowResponse
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Update current user's profile.

    Args:
        user_data: Updated user data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user information
    """
    # Update fields if provided
    if user_data.display_name is not None:
        current_user.display_name = user_data.display_name
    if user_data.bio is not None:
        current_user.bio = user_data.bio
    if user_data.avatar_url is not None:
        current_user.avatar_url = user_data.avatar_url

    current_user.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.get("/search", response_model=list[UserPublicResponse])
async def search_users(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User | None = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[UserPublicResponse]:
    """
    Search for users by username or display name.

    Args:
        q: Search query
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Current authenticated user (optional)
        db: Database session

    Returns:
        List of matching users
    """
    # Search by username or display_name
    query = select(User).where(
        User.is_active == True,  # noqa: E712
        User.deleted_at.is_(None),
        or_(
            User.username.ilike(f"%{q}%"),
            User.display_name.ilike(f"%{q}%"),
        ),
    )

    # Add pagination
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()

    # Convert to response schema
    user_responses = []
    for user in users:
        # Check if current user is following this user
        is_following = False
        if current_user:
            follow_result = await db.execute(
                select(Follow).where(
                    Follow.follower_id == current_user.id,
                    Follow.followed_id == user.id,
                )
            )
            is_following = follow_result.scalar_one_or_none() is not None

        user_dict = {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "bio": user.bio,
            "avatar_url": user.avatar_url,
            "followers_count": 0,  # TODO: Calculate actual count
            "following_count": 0,  # TODO: Calculate actual count
            "outputs_count": 0,  # TODO: Calculate actual count
            "is_following": is_following,
            "created_at": user.created_at,
        }
        user_responses.append(UserPublicResponse(**user_dict))

    return user_responses


@router.get("/{username}", response_model=UserPublicResponse)
async def get_user_by_username(
    username: str,
    current_user: User | None = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserPublicResponse:
    """
    Get user profile by username.

    Args:
        username: Username to look up
        current_user: Current authenticated user (optional)
        db: Database session

    Returns:
        User profile information

    Raises:
        HTTPException: If user not found
    """
    # Find user by username
    result = await db.execute(
        select(User).where(
            User.username == username,
            User.is_active == True,  # noqa: E712
            User.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if current user is following this user
    is_following = False
    if current_user and current_user.id != user.id:
        follow_result = await db.execute(
            select(Follow).where(
                Follow.follower_id == current_user.id,
                Follow.followed_id == user.id,
            )
        )
        is_following = follow_result.scalar_one_or_none() is not None

    # Get counts
    followers_count = await db.scalar(
        select(func.count()).select_from(Follow).where(Follow.followed_id == user.id)
    )
    following_count = await db.scalar(
        select(func.count()).select_from(Follow).where(Follow.follower_id == user.id)
    )

    user_dict = {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "followers_count": followers_count or 0,
        "following_count": following_count or 0,
        "outputs_count": 0,  # TODO: Calculate from outputs table
        "is_following": is_following,
        "created_at": user.created_at,
    }

    return UserPublicResponse(**user_dict)


@router.post("/{username}/follow", response_model=FollowResponse)
async def follow_user(
    username: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> FollowResponse:
    """
    Follow a user.

    Args:
        username: Username to follow
        current_user: Current authenticated user
        db: Database session

    Returns:
        Follow relationship information

    Raises:
        HTTPException: If user not found or trying to follow self
    """
    # Find user to follow
    result = await db.execute(
        select(User).where(
            User.username == username,
            User.is_active == True,  # noqa: E712
            User.deleted_at.is_(None),
        )
    )
    user_to_follow = result.scalar_one_or_none()

    if user_to_follow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if trying to follow self
    if user_to_follow.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot follow yourself",
        )

    # Check if already following
    existing_follow_result = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user.id,
            Follow.followed_id == user_to_follow.id,
        )
    )
    existing_follow = existing_follow_result.scalar_one_or_none()
    if existing_follow is not None:
        # Already following, return existing relationship
        return FollowResponse(is_following=True, followed_at=existing_follow.created_at)

    # Create new follow relationship
    new_follow = Follow(
        follower_id=current_user.id,
        followed_id=user_to_follow.id,
    )
    db.add(new_follow)
    await db.commit()
    await db.refresh(new_follow)

    return FollowResponse(is_following=True, followed_at=new_follow.created_at)


@router.delete("/{username}/follow", response_model=MessageResponse)
async def unfollow_user(
    username: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Unfollow a user.

    Args:
        username: Username to unfollow
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If user not found or not following
    """
    # Find user to unfollow
    result = await db.execute(
        select(User).where(
            User.username == username,
            User.is_active == True,  # noqa: E712
            User.deleted_at.is_(None),
        )
    )
    user_to_unfollow = result.scalar_one_or_none()

    if user_to_unfollow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Find follow relationship
    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user.id,
            Follow.followed_id == user_to_unfollow.id,
        )
    )
    follow = result.scalar_one_or_none()

    if follow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not following this user",
        )

    # Delete follow relationship
    await db.delete(follow)
    await db.commit()

    return MessageResponse(message=f"Successfully unfollowed {username}")


@router.get("/{username}/followers", response_model=list[UserListItemResponse])
async def get_followers(
    username: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
) -> list[UserListItemResponse]:
    """
    Get list of users following the specified user.

    Args:
        username: Username to get followers for
        limit: Maximum number of results
        offset: Number of results to skip
        db: Database session

    Returns:
        List of followers

    Raises:
        HTTPException: If user not found
    """
    # Find user
    result = await db.execute(
        select(User).where(
            User.username == username,
            User.is_active == True,  # noqa: E712
            User.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get followers
    query = (
        select(User, Follow.created_at)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.followed_id == user.id)
        .order_by(Follow.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(query)
    followers = result.all()

    return [
        UserListItemResponse(
            id=follower.id,
            username=follower.username,
            display_name=follower.display_name,
            avatar_url=follower.avatar_url,
            followed_at=followed_at,
        )
        for follower, followed_at in followers
    ]


@router.get("/{username}/following", response_model=list[UserListItemResponse])
async def get_following(
    username: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
) -> list[UserListItemResponse]:
    """
    Get list of users that the specified user is following.

    Args:
        username: Username to get following list for
        limit: Maximum number of results
        offset: Number of results to skip
        db: Database session

    Returns:
        List of users being followed

    Raises:
        HTTPException: If user not found
    """
    # Find user
    result = await db.execute(
        select(User).where(
            User.username == username,
            User.is_active == True,  # noqa: E712
            User.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get following
    query = (
        select(User, Follow.created_at)
        .join(Follow, Follow.followed_id == User.id)
        .where(Follow.follower_id == user.id)
        .order_by(Follow.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(query)
    following = result.all()

    return [
        UserListItemResponse(
            id=followed_user.id,
            username=followed_user.username,
            display_name=followed_user.display_name,
            avatar_url=followed_user.avatar_url,
            followed_at=followed_at,
        )
        for followed_user, followed_at in following
    ]


@router.get("/me/protocol-agreement")
async def get_protocol_agreement_status(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get current user's protocol agreement status.

    Returns:
        Protocol agreement status
    """
    return {
        "has_agreed_to_protocol": current_user.has_agreed_to_protocol,
        "user_id": str(current_user.id),
    }


@router.post("/me/protocol-agreement", response_model=MessageResponse)
async def agree_to_protocol(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Record user's agreement to the Lighthouse Protocol.

    This agreement means the user understands and accepts:
    - All public outputs are permanently stored and cannot be deleted
    - Edit history is immutable and publicly visible
    - Content becomes part of the collective human knowledge archive

    Returns:
        Success message

    Raises:
        HTTPException: If user has already agreed
    """
    if current_user.has_agreed_to_protocol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has already agreed to the protocol",
        )

    current_user.has_agreed_to_protocol = True
    current_user.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(current_user)

    return MessageResponse(
        message="Successfully agreed to the Lighthouse Protocol. You can now create public outputs."
    )
