"""Search API endpoints for outputs, tags, and users."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_optional_current_user
from app.models.user import User
from app.models.output import Output, VisibilityEnum
from app.models.follow import Follow
from app.schemas.output import OutputResponse
from app.schemas.user import UserPublicResponse

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/outputs", response_model=list[OutputResponse])
async def search_outputs(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    category: str | None = Query(None, description="Filter by category"),
    tags: str | None = Query(None, description="Comma-separated tags"),
    visibility: str | None = Query(None, description="Filter by visibility (PUBLIC/PRIVATE)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[OutputResponse]:
    """
    Search for outputs by content, category, or tags.

    Args:
        q: Search query for content full-text search
        category: Optional category filter
        tags: Optional comma-separated tags
        visibility: Optional visibility filter
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Current authenticated user (optional)
        db: Database session

    Returns:
        List of matching outputs
    """
    # Build base query
    query = select(Output)

    # Full-text search on content using PostgreSQL's to_tsvector
    # This uses the GIN index for better performance
    from sqlalchemy import text
    search_condition = text(
        "to_tsvector('english', content) @@ plainto_tsquery('english', :query)"
    ).bindparams(query=q)
    query = query.where(search_condition)

    # Category filter
    if category:
        query = query.where(Output.category == category)

    # Tags filter
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        # Use PostgreSQL array overlap operator
        for tag in tag_list:
            query = query.where(Output.tags.contains([tag]))

    # Visibility filtering
    if current_user:
        # Authenticated: show PUBLIC + PRIVATE from followed users
        if visibility == "PUBLIC":
            query = query.where(Output.visibility == VisibilityEnum.PUBLIC)
        elif visibility == "PRIVATE":
            # Get followed user IDs
            followed_result = await db.execute(
                select(Follow.followed_id).where(Follow.follower_id == current_user.id)
            )
            followed_ids = [row[0] for row in followed_result.all()]
            followed_ids.append(current_user.id)  # Include own outputs

            query = query.where(
                and_(
                    Output.visibility == VisibilityEnum.PRIVATE,
                    Output.user_id.in_(followed_ids),
                )
            )
        else:
            # Show all visible outputs
            followed_result = await db.execute(
                select(Follow.followed_id).where(Follow.follower_id == current_user.id)
            )
            followed_ids = [row[0] for row in followed_result.all()]
            followed_ids.append(current_user.id)

            query = query.where(
                or_(
                    Output.visibility == VisibilityEnum.PUBLIC,
                    and_(
                        Output.visibility == VisibilityEnum.PRIVATE,
                        Output.user_id.in_(followed_ids),
                    ),
                )
            )
    else:
        # Not authenticated: only PUBLIC outputs
        query = query.where(Output.visibility == VisibilityEnum.PUBLIC)

    # Order by relevance (novelty_score) and recency
    query = query.order_by(
        Output.novelty_score.desc().nulls_last(),
        Output.created_at.desc(),
    ).offset(offset).limit(limit)

    result = await db.execute(query)
    outputs = result.scalars().all()

    return [OutputResponse.model_validate(output) for output in outputs]


@router.get("/tags", response_model=list[dict])
async def search_tags(
    q: str = Query(..., min_length=1, max_length=50, description="Tag prefix to search"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """
    Search for tags by prefix.

    Args:
        q: Tag prefix to search for
        limit: Maximum number of results
        db: Database session

    Returns:
        List of matching tags with usage counts
    """
    # PostgreSQL query to get all unique tags from public outputs
    # Using unnest to flatten the tag arrays
    query_text = """
    SELECT
        tag,
        COUNT(*) as count
    FROM (
        SELECT unnest(tags) as tag
        FROM outputs
        WHERE visibility = 'public'
    ) AS all_tags
    WHERE tag ILIKE :search_pattern
    GROUP BY tag
    ORDER BY count DESC, tag ASC
    LIMIT :limit
    """

    result = await db.execute(
        query_text,
        {"search_pattern": f"{q}%", "limit": limit}
    )

    tags = []
    for row in result:
        tags.append({"tag": row[0], "count": row[1]})

    return tags


@router.get("/users", response_model=list[UserPublicResponse])
async def search_users(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User | None = Depends(get_optional_current_user),
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

    # Order by follower count (relevance) and username
    # Get follower counts via subquery
    follower_count_subq = (
        select(
            Follow.followed_id,
            func.count().label("follower_count")
        )
        .group_by(Follow.followed_id)
        .subquery()
    )

    query = (
        query
        .outerjoin(follower_count_subq, User.id == follower_count_subq.c.followed_id)
        .order_by(
            follower_count_subq.c.follower_count.desc().nulls_last(),
            User.username.asc(),
        )
        .offset(offset)
        .limit(limit)
    )

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

        user_responses.append(UserPublicResponse(**user_dict))

    return user_responses
