"""Follow API endpoints for user and output following."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.models.follow import Follow
from app.models.output_follow import OutputFollow
from app.models.output import Output
from app.schemas.follow import (
    FollowCreate,
    FollowResponse,
    FollowStats,
    OutputFollowCreate,
    OutputFollowResponse,
    OutputFollowStats,
)

router = APIRouter(prefix="/follow", tags=["Follow"])


# ============================================================================
# User Follow Endpoints
# ============================================================================


@router.post("/users", response_model=FollowResponse, status_code=status.HTTP_201_CREATED)
async def follow_user(
    follow_data: FollowCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> FollowResponse:
    """
    Follow a user.

    Args:
        follow_data: User ID to follow
        current_user: Current authenticated user
        db: Database session

    Returns:
        Follow relationship information

    Raises:
        HTTPException: If user tries to follow themselves or already following
    """
    # Check if trying to follow themselves
    if current_user.id == follow_data.followed_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot follow yourself",
        )

    # Check if user exists
    result = await db.execute(select(User).where(User.id == follow_data.followed_id))
    followed_user = result.scalar_one_or_none()
    if not followed_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if already following
    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user.id,
            Follow.followed_id == follow_data.followed_id,
        )
    )
    existing_follow = result.scalar_one_or_none()
    if existing_follow:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already following this user",
        )

    # Create follow relationship
    new_follow = Follow(
        follower_id=current_user.id,
        followed_id=follow_data.followed_id,
    )
    db.add(new_follow)
    await db.commit()
    await db.refresh(new_follow)

    return FollowResponse.model_validate(new_follow)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Unfollow a user.

    Args:
        user_id: User ID to unfollow
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If not following the user
    """
    # Find follow relationship
    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user.id,
            Follow.followed_id == user_id,
        )
    )
    follow = result.scalar_one_or_none()

    if not follow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not following this user",
        )

    await db.delete(follow)
    await db.commit()


@router.get("/users/{user_id}/stats", response_model=FollowStats)
async def get_user_follow_stats(
    user_id: UUID,
    current_user: User | None = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> FollowStats:
    """
    Get follow statistics for a user.

    Args:
        user_id: User ID to get stats for
        current_user: Current authenticated user (optional)
        db: Database session

    Returns:
        Follow statistics

    Raises:
        HTTPException: If user not found
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get follower count
    follower_count_result = await db.execute(
        select(func.count()).select_from(Follow).where(Follow.followed_id == user_id)
    )
    follower_count = follower_count_result.scalar() or 0

    # Get following count
    following_count_result = await db.execute(
        select(func.count()).select_from(Follow).where(Follow.follower_id == user_id)
    )
    following_count = following_count_result.scalar() or 0

    # Check if current user is following this user
    is_following = False
    if current_user:
        result = await db.execute(
            select(Follow).where(
                Follow.follower_id == current_user.id,
                Follow.followed_id == user_id,
            )
        )
        is_following = result.scalar_one_or_none() is not None

    return FollowStats(
        follower_count=follower_count,
        following_count=following_count,
        is_following=is_following,
    )


@router.get("/users/{user_id}/followers", response_model=list[FollowResponse])
async def get_user_followers(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
) -> list[FollowResponse]:
    """
    Get list of users following a specific user.

    Args:
        user_id: User ID to get followers for
        db: Database session
        limit: Maximum number of results
        offset: Offset for pagination

    Returns:
        List of follow relationships
    """
    result = await db.execute(
        select(Follow)
        .where(Follow.followed_id == user_id)
        .order_by(Follow.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    follows = result.scalars().all()
    return [FollowResponse.model_validate(follow) for follow in follows]


@router.get("/users/{user_id}/following", response_model=list[FollowResponse])
async def get_user_following(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
) -> list[FollowResponse]:
    """
    Get list of users a specific user is following.

    Args:
        user_id: User ID to get following list for
        db: Database session
        limit: Maximum number of results
        offset: Offset for pagination

    Returns:
        List of follow relationships
    """
    result = await db.execute(
        select(Follow)
        .where(Follow.follower_id == user_id)
        .order_by(Follow.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    follows = result.scalars().all()
    return [FollowResponse.model_validate(follow) for follow in follows]


# ============================================================================
# Output Follow Endpoints
# ============================================================================


@router.post("/outputs", response_model=OutputFollowResponse, status_code=status.HTTP_201_CREATED)
async def follow_output(
    follow_data: OutputFollowCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> OutputFollowResponse:
    """
    Follow an output.

    Args:
        follow_data: Output ID to follow
        current_user: Current authenticated user
        db: Database session

    Returns:
        Output follow relationship information

    Raises:
        HTTPException: If output not found or already following
    """
    # Check if output exists
    result = await db.execute(select(Output).where(Output.id == follow_data.output_id))
    output = result.scalar_one_or_none()
    if not output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    # Check if already following
    result = await db.execute(
        select(OutputFollow).where(
            OutputFollow.user_id == current_user.id,
            OutputFollow.output_id == follow_data.output_id,
        )
    )
    existing_follow = result.scalar_one_or_none()
    if existing_follow:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already following this output",
        )

    # Create output follow relationship
    new_follow = OutputFollow(
        user_id=current_user.id,
        output_id=follow_data.output_id,
    )
    db.add(new_follow)
    await db.commit()
    await db.refresh(new_follow)

    return OutputFollowResponse.model_validate(new_follow)


@router.delete("/outputs/{output_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_output(
    output_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Unfollow an output.

    Args:
        output_id: Output ID to unfollow
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If not following the output
    """
    # Find output follow relationship
    result = await db.execute(
        select(OutputFollow).where(
            OutputFollow.user_id == current_user.id,
            OutputFollow.output_id == output_id,
        )
    )
    follow = result.scalar_one_or_none()

    if not follow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not following this output",
        )

    await db.delete(follow)
    await db.commit()


@router.get("/outputs/{output_id}/stats", response_model=OutputFollowStats)
async def get_output_follow_stats(
    output_id: str,
    current_user: User | None = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> OutputFollowStats:
    """
    Get follow statistics for an output.

    Args:
        output_id: Output ID to get stats for
        current_user: Current authenticated user (optional)
        db: Database session

    Returns:
        Output follow statistics

    Raises:
        HTTPException: If output not found
    """
    # Check if output exists
    result = await db.execute(select(Output).where(Output.id == output_id))
    output = result.scalar_one_or_none()
    if not output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    # Get follower count
    follower_count_result = await db.execute(
        select(func.count()).select_from(OutputFollow).where(OutputFollow.output_id == output_id)
    )
    follower_count = follower_count_result.scalar() or 0

    # Check if current user is following this output
    is_following = False
    if current_user:
        result = await db.execute(
            select(OutputFollow).where(
                OutputFollow.user_id == current_user.id,
                OutputFollow.output_id == output_id,
            )
        )
        is_following = result.scalar_one_or_none() is not None

    return OutputFollowStats(
        follower_count=follower_count,
        is_following=is_following,
    )


@router.get("/outputs/{output_id}/followers", response_model=list[OutputFollowResponse])
async def get_output_followers(
    output_id: str,
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
) -> list[OutputFollowResponse]:
    """
    Get list of users following a specific output.

    Args:
        output_id: Output ID to get followers for
        db: Database session
        limit: Maximum number of results
        offset: Offset for pagination

    Returns:
        List of output follow relationships
    """
    result = await db.execute(
        select(OutputFollow)
        .where(OutputFollow.output_id == output_id)
        .order_by(OutputFollow.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    follows = result.scalars().all()
    return [OutputFollowResponse.model_validate(follow) for follow in follows]
