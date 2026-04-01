"""Output (post) management API endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user, get_optional_current_user
from app.models.user import User
from app.models.output import Output, VisibilityEnum, AIReviewStatus, CategoryEnum
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
from app.utils.embeddings import generate_embedding
from app.utils.similarity_search import find_similar_outputs
from app.utils.web_search import search_web_for_content
from app.utils.originality_check import (
    check_originality_with_llm,
    generate_originality_warnings,
    should_approve_for_public,
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

    Performs only content moderation synchronously (~2s).
    If moderation passes, saves with ai_review_status=PENDING and returns immediately.
    Full review pipeline (embeddings, similarity, originality) runs via POST /outputs/{id}/review.

    Args:
        output_data: Output creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created output information

    Raises:
        HTTPException: If user has not agreed to protocol or content moderation fails
    """
    # Check if user has agreed to the Lighthouse Protocol
    if not current_user.has_agreed_to_protocol:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must agree to the Lighthouse Protocol before creating outputs. All public outputs are permanently stored and cannot be deleted.",
        )

    # Check content safety with AI moderation (category-aware)
    moderation_result = await check_content_safety(
        output_data.content, category=output_data.category.value
    )

    # Get creation timestamp
    created_at = datetime.now(timezone.utc)

    # Generate content hash (content only, for deduplication)
    content_hash = generate_content_hash(content=output_data.content)

    if not moderation_result.is_safe:
        # Rejected: Store as private draft with feedback
        ai_review_status = AIReviewStatus.REJECTED
        ai_review_flagged_categories = moderation_result.flagged_categories
        ai_review_feedback = moderation_result.get_user_feedback()
        visibility = VisibilityEnum.PRIVATE

        # Simplified hashing for rejected content (not part of hash chain)
        full_hash = content_hash  # Use content hash as full hash
    else:
        # Moderation passed: save as PENDING, skip full review pipeline
        ai_review_status = AIReviewStatus.PENDING
        ai_review_flagged_categories = None
        ai_review_feedback = None
        visibility = VisibilityEnum.PRIVATE  # Will be updated after review

        # Generate full hash (content + metadata + timestamp) for hash chain
        full_hash = generate_full_hash(
            content=output_data.content,
            user_id=str(current_user.id),
            category=output_data.category.value,
            tags=output_data.tags or [],
            created_at=created_at,
            previous_hash=None,
            referenced_entity_type=output_data.referenced_entity_type,
            referenced_entity_id=output_data.referenced_entity_id,
            referenced_entity_data=output_data.referenced_entity_data,
        )

    # Generate output ID
    output_id = generate_output_id(full_hash, created_at)

    # Check for ID collision (very rare)
    existing = await db.execute(select(Output).where(Output.id == output_id))
    if existing.scalar_one_or_none() is not None:
        # Add timestamp suffix to make it unique
        timestamp_suffix = str(int(created_at.timestamp()))[-4:]
        output_id = f"{output_id}-{timestamp_suffix}"

    # Create output - pass enum directly (str enum works with SQLAlchemy)
    new_output = Output(
        id=output_id,
        user_id=current_user.id,
        title=output_data.title,
        content=output_data.content,
        category=output_data.category,  # Pass enum directly
        tags=output_data.tags or [],
        visibility=visibility,
        ai_review_status=ai_review_status,
        ai_review_flagged_categories=ai_review_flagged_categories,
        ai_review_feedback=ai_review_feedback,
        novelty_score=None,
        content_embedding=None,
        originality_score=None,
        ai_generated_probability=None,
        originality_warnings=None,
        originality_reasoning=None,
        referenced_entity_type=output_data.referenced_entity_type,
        referenced_entity_id=output_data.referenced_entity_id,
        referenced_entity_data=output_data.referenced_entity_data,
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


@router.post("/{output_id}/review", response_model=OutputResponse)
async def review_output(
    output_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> OutputResponse:
    """
    Run the full AI review pipeline for an output (background review step).

    Executes embeddings generation, similarity search, web search, and LLM originality check.
    Updates the output's ai_review_status, visibility, and originality scores.
    This endpoint is idempotent - safe to call multiple times.

    Args:
        output_id: Output ID to review
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated output information

    Raises:
        HTTPException: If output not found, user not authorized, or output was rejected
    """
    # Load the output from DB
    result = await db.execute(select(Output).where(Output.id == output_id))
    output = result.scalar_one_or_none()

    if output is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    # Only the author can trigger review
    if output.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to review this output",
        )

    # Skip review if already rejected (content moderation failed)
    if output.ai_review_status == AIReviewStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot review a rejected output",
        )

    # Idempotent: if already reviewed (APPROVED), return as-is
    if output.ai_review_status == AIReviewStatus.APPROVED:
        return OutputResponse.model_validate(output)

    # === Phase 1.2: Embeddings Generation ===
    content_embedding = await generate_embedding(output.content)

    # === Phase 1.3: Similarity Check (Internal Database) ===
    similar_outputs = []
    if content_embedding:
        similar_outputs = await find_similar_outputs(
            db=db,
            embedding=content_embedding,
            threshold=0.85,
            limit=5,
        )

    # === Phase 1.4: Web Search Check (External Plagiarism) ===
    web_results = await search_web_for_content(
        content=output.content,
        num_phrases=3,
        results_per_phrase=3,
    )

    # === Phase 1.5: LLM Originality Judgment ===
    originality_judgment = await check_originality_with_llm(
        content=output.content,
        similar_outputs=similar_outputs,
        web_search_results=web_results,
    )

    # Initialize originality fields
    originality_score = None
    ai_generated_probability = None
    originality_warnings = []
    originality_reasoning = None
    novelty_score = None
    ai_review_feedback = None

    if originality_judgment:
        originality_score = originality_judgment.originality_score
        ai_generated_probability = originality_judgment.ai_generated_probability
        originality_reasoning = originality_judgment.reasoning

        # Generate warning messages
        originality_warnings = generate_originality_warnings(
            judgment=originality_judgment,
            similar_outputs=similar_outputs,
            web_results=web_results,
        )

        # Check if approved for public based on originality
        is_approved, approval_reason = should_approve_for_public(
            judgment=originality_judgment,
            threshold=60,  # Default threshold from Lighthouse Protocol
            similar_outputs=similar_outputs,
            web_results=web_results,
        )

        if not is_approved:
            # Demote to private due to low originality
            visibility = VisibilityEnum.PRIVATE
            ai_review_feedback = approval_reason
        else:
            # Calculate novelty score and determine visibility
            novelty_score = await calculate_novelty_score(output.content)
            visibility_str = await determine_visibility(novelty_score)
            visibility = VisibilityEnum(visibility_str)
    else:
        # No originality judgment available (API error, etc.)
        # Fallback to novelty-based visibility
        novelty_score = await calculate_novelty_score(output.content)
        visibility_str = await determine_visibility(novelty_score)
        visibility = VisibilityEnum(visibility_str)

    # Update output with review results
    output.ai_review_status = AIReviewStatus.APPROVED
    output.ai_review_feedback = ai_review_feedback
    output.visibility = visibility
    output.content_embedding = content_embedding
    output.novelty_score = novelty_score
    output.originality_score = originality_score
    output.ai_generated_probability = ai_generated_probability
    output.originality_warnings = originality_warnings if originality_warnings else None
    output.originality_reasoning = originality_reasoning

    await db.commit()
    await db.refresh(output)

    return OutputResponse.model_validate(output)
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

    # Check content safety if content changed (category-aware)
    if output_data.content is not None and output_data.content != existing_output.content:
        # Use updated category if provided, otherwise use existing category
        category_for_moderation = (
            output_data.category.value
            if output_data.category
            else existing_output.category.value
        )
        moderation_result = await check_content_safety(
            output_data.content, category=category_for_moderation
        )
        if not moderation_result.is_safe:
            # Reject the edit with detailed feedback
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Content violates safety policies",
                    "flagged_categories": moderation_result.flagged_categories,
                    "feedback": moderation_result.get_user_feedback(),
                },
            )

    # Update fields
    new_title = output_data.title if output_data.title is not None else existing_output.title
    new_content = output_data.content if output_data.content is not None else existing_output.content
    new_category = output_data.category if output_data.category is not None else existing_output.category
    new_tags = output_data.tags if output_data.tags is not None else existing_output.tags
    new_referenced_entity_type = output_data.referenced_entity_type if output_data.referenced_entity_type is not None else existing_output.referenced_entity_type
    new_referenced_entity_id = output_data.referenced_entity_id if output_data.referenced_entity_id is not None else existing_output.referenced_entity_id
    new_referenced_entity_data = output_data.referenced_entity_data if output_data.referenced_entity_data is not None else existing_output.referenced_entity_data

    # Recalculate originality and visibility if content changed
    if output_data.content is not None and output_data.content != existing_output.content:
        # === Phase 1.2: Generate embedding for similarity search ===
        content_embedding = await generate_embedding(new_content)

        # === Phase 1.3: Similar Content Search (Internal Database) ===
        similar_outputs = []
        if content_embedding:
            similar_outputs = await find_similar_outputs(
                db=db,
                embedding=content_embedding,
                threshold=0.7,
                limit=5,
                exclude_output_id=existing_output.id,  # Exclude the output being edited
            )

        # === Phase 1.4: Web Search Check (External Plagiarism) ===
        web_results = await search_web_for_content(
            content=new_content,
            num_phrases=3,
            results_per_phrase=3,
        )

        # === Phase 1.5: LLM Originality Judgment ===
        originality_judgment = await check_originality_with_llm(
            content=new_content,
            similar_outputs=similar_outputs,
            web_search_results=web_results,
        )

        # Initialize originality fields with defaults
        originality_score = None
        ai_generated_probability = None
        originality_warnings = []
        originality_reasoning = None
        novelty_score = None
        visibility = "private"  # Default to private

        # Determine visibility based on originality judgment
        if originality_judgment:
            originality_score = originality_judgment.originality_score
            ai_generated_probability = originality_judgment.ai_generated_probability
            originality_reasoning = originality_judgment.reasoning

            # Generate warning messages
            originality_warnings = generate_originality_warnings(
                judgment=originality_judgment,
                similar_outputs=similar_outputs,
                web_results=web_results,
            )

            # Check if approved for public based on originality
            is_approved, approval_reason = should_approve_for_public(
                judgment=originality_judgment,
                threshold=60,  # Default threshold from Lighthouse Protocol
                similar_outputs=similar_outputs,
                web_results=web_results,
            )

            if not is_approved:
                # Demote to private due to low originality
                visibility = "private"
                existing_output.ai_review_feedback = approval_reason
            else:
                # Calculate novelty score (Phase 2 feature, optional)
                novelty_score = await calculate_novelty_score(new_content)
                # Determine visibility (can be public or private based on novelty)
                visibility = await determine_visibility(novelty_score)
        else:
            # No originality judgment available (API error, etc.)
            # Fallback to novelty-based visibility
            novelty_score = await calculate_novelty_score(new_content)
            visibility = await determine_visibility(novelty_score)

        # Update all fields
        existing_output.novelty_score = novelty_score
        existing_output.visibility = VisibilityEnum(visibility)
        existing_output.originality_score = originality_score
        existing_output.ai_generated_probability = ai_generated_probability
        existing_output.originality_warnings = originality_warnings if originality_warnings else None
        existing_output.originality_reasoning = originality_reasoning

        # Update embedding only for public outputs (for similarity search)
        if visibility == "public" and content_embedding:
            existing_output.content_embedding = content_embedding
        elif visibility == "private":
            existing_output.content_embedding = None  # Clear embedding for private outputs

        # If previously rejected, now approve it and clear feedback
        if existing_output.ai_review_status == AIReviewStatus.REJECTED:
            existing_output.ai_review_status = AIReviewStatus.APPROVED
            existing_output.ai_review_flagged_categories = None
            existing_output.ai_review_feedback = None

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
        referenced_entity_type=new_referenced_entity_type,
        referenced_entity_id=new_referenced_entity_id,
        referenced_entity_data=new_referenced_entity_data,
    )

    # Update output
    existing_output.title = new_title
    existing_output.content = new_content
    existing_output.category = new_category
    existing_output.tags = new_tags
    existing_output.referenced_entity_type = new_referenced_entity_type
    existing_output.referenced_entity_id = new_referenced_entity_id
    existing_output.referenced_entity_data = new_referenced_entity_data
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

    # Visibility filtering (normalize to uppercase for comparison)
    visibility_upper = visibility.upper() if visibility else None
    if current_user:
        # Authenticated: show PUBLIC + PRIVATE from followed users
        if visibility_upper == "PUBLIC":
            query = query.where(Output.visibility == VisibilityEnum.PUBLIC)
        elif visibility_upper == "PRIVATE":
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

    # Get citation information for each output
    output_responses = []
    for output in outputs:
        # Get citations where this output is the source (outgoing citations)
        citations_result = await db.execute(
            select(Citation).where(Citation.source_output_id == output.id)
        )
        citations = citations_result.scalars().all()

        # Create OutputResponse with citation info
        output_dict = OutputResponse.model_validate(output).model_dump()
        output_dict["citing_outputs"] = [
            {
                "target_output_id": c.target_output_id,
                "citation_type": c.citation_type.value,
                "excerpt": c.excerpt,
            }
            for c in citations
        ]
        output_responses.append(OutputResponse.model_validate(output_dict))

    return output_responses


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

    # Get citation information for each output
    output_responses = []
    for output in outputs:
        # Get citations where this output is the source (outgoing citations)
        citations_result = await db.execute(
            select(Citation).where(Citation.source_output_id == output.id)
        )
        citations = citations_result.scalars().all()

        # Create OutputResponse with citation info
        output_dict = OutputResponse.model_validate(output).model_dump()
        output_dict["citing_outputs"] = [
            {
                "target_output_id": c.target_output_id,
                "citation_type": c.citation_type.value,
                "excerpt": c.excerpt,
            }
            for c in citations
        ]
        output_responses.append(OutputResponse.model_validate(output_dict))

    return output_responses


@router.get("/me/rejected", response_model=list[OutputResponse])
async def get_my_rejected_outputs(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[OutputResponse]:
    """
    Get current user's rejected outputs.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of rejected outputs
    """
    result = await db.execute(
        select(Output)
        .where(
            Output.user_id == current_user.id,
            Output.ai_review_status == AIReviewStatus.REJECTED,
        )
        .order_by(Output.created_at.desc())
    )
    outputs = result.scalars().all()

    return [OutputResponse.model_validate(output) for output in outputs]
