"""Output (post) management API endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user, get_optional_current_user
from app.models.user import User
from app.models.output import Output, VisibilityEnum, AIReviewStatus
from app.models.output_history import OutputHistory
from app.models.follow import Follow
from app.models.citation import Citation
from app.models.agreement import Agreement
from app.schemas.output import (
    OutputCreate,
    OutputUpdate,
    OutputResponse,
    OutputDetailResponse,
    OutputHistoryResponse,
    HashVerificationResponse,
)
from app.schemas.common import MessageResponse
from app.utils.hash_chain import (
    generate_content_hash,
    generate_full_hash,
    generate_output_id,
    verify_content_hash,
    verify_full_hash,
)
from app.utils.ai_moderation import (
    check_content_safety,
    calculate_novelty_score,
    determine_visibility,
)

router = APIRouter(prefix="/outputs", tags=["Outputs"])


@router.post("/", response_model=OutputResponse, status_code=status.HTTP_201_CREATED)
async def create_output(
    output_data: OutputCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> OutputResponse:
    """
    Create a new output (post).

    Args:
        output_data: Output creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created output information

    Raises:
        HTTPException: If content moderation fails
    """
    # Check content safety with AI moderation
    moderation_result = await check_content_safety(output_data.content)

    if not moderation_result.is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content violates safety policies: {', '.join(moderation_result.flagged_categories)}",
        )

    # Calculate novelty score
    novelty_score = await calculate_novelty_score(output_data.content)

    # Determine visibility based on novelty
    visibility = await determine_visibility(novelty_score)

    # Generate content hash (content only, for deduplication)
    content_hash = generate_content_hash(content=output_data.content)

    # Get creation timestamp
    created_at = datetime.now(timezone.utc)

    # Generate full hash (content + metadata + timestamp)
    full_hash = generate_full_hash(
        content=output_data.content,
        user_id=str(current_user.id),
        category=output_data.category.value,
        tags=output_data.tags or [],
        created_at=created_at,
        previous_hash=None,
    )

    # Generate output ID
    output_id = generate_output_id(full_hash, created_at)

    # Check for ID collision (very rare)
    existing = await db.execute(select(Output).where(Output.id == output_id))
    if existing.scalar_one_or_none() is not None:
        # Add timestamp suffix to make it unique
        timestamp_suffix = str(int(created_at.timestamp()))[-4:]
        output_id = f"{output_id}-{timestamp_suffix}"

    # Create output
    new_output = Output(
        id=output_id,
        user_id=current_user.id,
        content=output_data.content,
        category=output_data.category,
        tags=output_data.tags or [],
        visibility=VisibilityEnum(visibility),
        ai_review_status=AIReviewStatus.APPROVED,
        novelty_score=novelty_score,
        content_hash=content_hash,
        hash=full_hash,
        previous_hash=None,
        version=1,
        created_at=created_at,
    )

    db.add(new_output)
    await db.commit()
    await db.refresh(new_output)

    return OutputResponse.model_validate(new_output)


@router.patch("/{output_id}", response_model=OutputResponse)
async def update_output(
    output_id: str,
    output_data: OutputUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> OutputResponse:
    """
    Update an existing output (creates new version with hash chain).

    Args:
        output_id: Output ID to update
        output_data: Updated output data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated output information

    Raises:
        HTTPException: If output not found or user not authorized
    """
    # Find existing output
    result = await db.execute(select(Output).where(Output.id == output_id))
    existing_output = result.scalar_one_or_none()

    if existing_output is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    # Check ownership
    if existing_output.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this output",
        )

    # Save current version to history
    history_entry = OutputHistory(
        output_id=existing_output.id,
        version=existing_output.version,
        content=existing_output.content,
        hash=existing_output.hash,
        previous_hash=existing_output.previous_hash,
        edited_by=current_user.id,
    )
    db.add(history_entry)

    # Check content safety
    if output_data.content is not None:
        moderation_result = await check_content_safety(output_data.content)
        if not moderation_result.is_safe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Content violates safety policies: {', '.join(moderation_result.flagged_categories)}",
            )

    # Update fields
    new_content = output_data.content if output_data.content is not None else existing_output.content
    new_category = output_data.category if output_data.category is not None else existing_output.category
    new_tags = output_data.tags if output_data.tags is not None else existing_output.tags

    # Recalculate novelty score if content changed
    if output_data.content is not None:
        novelty_score = await calculate_novelty_score(new_content)
        visibility = await determine_visibility(novelty_score)
        existing_output.novelty_score = novelty_score
        existing_output.visibility = VisibilityEnum(visibility)

    # Generate new content hash
    new_content_hash = generate_content_hash(content=new_content)

    # Generate new full hash with previous hash reference
    updated_at = datetime.now(timezone.utc)
    new_full_hash = generate_full_hash(
        content=new_content,
        user_id=str(current_user.id),
        category=new_category.value,
        tags=new_tags,
        created_at=updated_at,  # Use updated timestamp for new version
        previous_hash=existing_output.hash,  # Link to previous version
    )

    # Update output
    existing_output.content = new_content
    existing_output.category = new_category
    existing_output.tags = new_tags
    existing_output.content_hash = new_content_hash
    existing_output.previous_hash = existing_output.hash  # Old hash becomes previous
    existing_output.hash = new_full_hash  # New hash
    existing_output.version += 1
    existing_output.updated_at = updated_at

    await db.commit()
    await db.refresh(existing_output)

    return OutputResponse.model_validate(existing_output)


@router.get("/{output_id}", response_model=OutputDetailResponse)
async def get_output(
    output_id: str,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> OutputDetailResponse:
    """
    Get output by ID.

    Args:
        output_id: Output ID to retrieve
        current_user: Current authenticated user (optional)
        db: Database session

    Returns:
        Output details

    Raises:
        HTTPException: If output not found or not accessible
    """
    # Find output with author information
    result = await db.execute(
        select(Output, User)
        .join(User, User.id == Output.user_id)
        .where(Output.id == output_id)
    )
    row = result.first()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    output, author = row

    # Check visibility permissions
    if output.visibility == VisibilityEnum.PRIVATE:
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to view this output",
            )

        # Private outputs are visible to:
        # 1. The author
        # 2. Followers of the author
        if output.user_id != current_user.id:
            # Check if current user follows the author
            follow_result = await db.execute(
                select(Follow).where(
                    Follow.follower_id == current_user.id,
                    Follow.followed_id == output.user_id,
                )
            )
            if follow_result.scalar_one_or_none() is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view this output",
                )

    # Get citation count (outputs citing this one)
    citation_count = await db.scalar(
        select(func.count()).select_from(Citation).where(Citation.target_output_id == output.id)
    ) or 0

    # Get agreement count
    agreement_count = await db.scalar(
        select(func.count()).select_from(Agreement).where(Agreement.output_id == output.id)
    ) or 0

    # Build response
    response_data = {
        **output.__dict__,
        "author": {
            "id": author.id,
            "username": author.username,
            "display_name": author.display_name,
            "avatar_url": author.avatar_url,
        },
        "citation_count": citation_count,
        "agreement_count": agreement_count,
    }

    return OutputDetailResponse(**response_data)


@router.get("/{output_id}/history", response_model=list[OutputHistoryResponse])
async def get_output_history(
    output_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[OutputHistoryResponse]:
    """
    Get edit history for an output.

    Args:
        output_id: Output ID to get history for
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of historical versions

    Raises:
        HTTPException: If output not found
    """
    # Verify output exists
    result = await db.execute(select(Output).where(Output.id == output_id))
    output = result.scalar_one_or_none()

    if output is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    # Get history entries
    history_result = await db.execute(
        select(OutputHistory)
        .where(OutputHistory.output_id == output_id)
        .order_by(OutputHistory.version.desc())
    )
    history_entries = history_result.scalars().all()

    return [OutputHistoryResponse.model_validate(entry) for entry in history_entries]


@router.get("/", response_model=list[OutputResponse])
async def get_timeline(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    visibility: str | None = Query(None, description="Filter by visibility (PUBLIC/PRIVATE)"),
    category: str | None = Query(None, description="Filter by category"),
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[OutputResponse]:
    """
    Get timeline of outputs.

    Public outputs are visible to everyone.
    Private outputs are only visible to authenticated users who follow the author.

    Args:
        limit: Maximum number of results
        offset: Number of results to skip
        visibility: Optional visibility filter
        category: Optional category filter
        current_user: Current authenticated user (optional)
        db: Database session

    Returns:
        List of outputs
    """
    # Build base query
    query = select(Output)

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

    # Category filter
    if category:
        query = query.where(Output.category == category)

    # Order and paginate
    query = query.order_by(Output.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    outputs = result.scalars().all()

    return [OutputResponse.model_validate(output) for output in outputs]


@router.get("/user/{username}", response_model=list[OutputResponse])
async def get_user_outputs(
    username: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[OutputResponse]:
    """
    Get outputs for a specific user.

    Args:
        username: Username to get outputs for
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Current authenticated user (optional)
        db: Database session

    Returns:
        List of user's outputs

    Raises:
        HTTPException: If user not found
    """
    # Find user
    user_result = await db.execute(
        select(User).where(
            User.username == username,
            User.is_active == True,  # noqa: E712
            User.deleted_at.is_(None),
        )
    )
    user = user_result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Build query
    query = select(Output).where(Output.user_id == user.id)

    # Visibility filtering
    if current_user and current_user.id == user.id:
        # Own outputs: show all
        pass
    elif current_user:
        # Check if following
        follow_result = await db.execute(
            select(Follow).where(
                Follow.follower_id == current_user.id,
                Follow.followed_id == user.id,
            )
        )
        if follow_result.scalar_one_or_none():
            # Following: show PUBLIC + PRIVATE
            pass
        else:
            # Not following: only PUBLIC
            query = query.where(Output.visibility == VisibilityEnum.PUBLIC)
    else:
        # Not authenticated: only PUBLIC
        query = query.where(Output.visibility == VisibilityEnum.PUBLIC)

    # Order and paginate
    query = query.order_by(Output.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    outputs = result.scalars().all()

    return [OutputResponse.model_validate(output) for output in outputs]
