"""Agreement management API endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user, get_optional_current_user
from app.models.user import User
from app.models.output import Output
from app.models.agreement import Agreement
from app.schemas.agreement import AgreementResponse, AgreementUserResponse
from app.schemas.output import OutputResponse
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/agreements", tags=["Agreements"])


@router.post("/", response_model=AgreementResponse, status_code=status.HTTP_201_CREATED)
async def agree_to_output(
    output_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AgreementResponse:
    """
    Agree with an output (post).

    Args:
        output_id: Output ID to agree with
        current_user: Current authenticated user
        db: Database session

    Returns:
        Agreement information

    Raises:
        HTTPException: If output not found or already agreed
    """
    # Verify output exists
    output_result = await db.execute(select(Output).where(Output.id == output_id))
    output = output_result.scalar_one_or_none()

    if output is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    # Check if already agreed
    existing_result = await db.execute(
        select(Agreement).where(
            Agreement.user_id == current_user.id,
            Agreement.output_id == output_id,
        )
    )
    existing_agreement = existing_result.scalar_one_or_none()

    if existing_agreement is not None:
        # Already agreed, return existing agreement
        return AgreementResponse(
            output_id=existing_agreement.output_id,
            agreed_at=existing_agreement.created_at,
        )

    # Create new agreement
    new_agreement = Agreement(
        user_id=current_user.id,
        output_id=output_id,
    )

    db.add(new_agreement)
    await db.commit()
    await db.refresh(new_agreement)

    return AgreementResponse(
        output_id=new_agreement.output_id,
        agreed_at=new_agreement.created_at,
    )


@router.delete("/{output_id}", response_model=MessageResponse)
async def remove_agreement(
    output_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Remove agreement from an output.

    Args:
        output_id: Output ID to remove agreement from
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If output not found or not agreed
    """
    # Find agreement
    result = await db.execute(
        select(Agreement).where(
            Agreement.user_id == current_user.id,
            Agreement.output_id == output_id,
        )
    )
    agreement = result.scalar_one_or_none()

    if agreement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You have not agreed with this output",
        )

    # Delete agreement
    await db.delete(agreement)
    await db.commit()

    return MessageResponse(message="Agreement removed successfully")


@router.get("/output/{output_id}", response_model=list[AgreementUserResponse])
async def get_users_who_agreed(
    output_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AgreementUserResponse]:
    """
    Get list of users who agreed with an output.

    Args:
        output_id: Output ID to get agreements for
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Current authenticated user (optional)
        db: Database session

    Returns:
        List of users who agreed

    Raises:
        HTTPException: If output not found
    """
    # Verify output exists
    output_result = await db.execute(select(Output).where(Output.id == output_id))
    if output_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    # Get agreements with user information
    query = (
        select(User, Agreement.created_at)
        .join(Agreement, Agreement.user_id == User.id)
        .where(Agreement.output_id == output_id)
        .order_by(Agreement.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    # Build response
    users_who_agreed = []
    for user, agreed_at in rows:
        users_who_agreed.append(
            AgreementUserResponse(
                id=user.id,
                username=user.username,
                display_name=user.display_name,
                avatar_url=user.avatar_url,
                agreed_at=agreed_at,
            )
        )

    return users_who_agreed


@router.get("/user/{username}", response_model=list[OutputResponse])
async def get_user_agreed_outputs(
    username: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[OutputResponse]:
    """
    Get outputs that a user has agreed with.

    Args:
        username: Username to get agreements for
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Current authenticated user (optional)
        db: Database session

    Returns:
        List of outputs the user agreed with

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

    # Get outputs the user agreed with
    query = (
        select(Output)
        .join(Agreement, Agreement.output_id == Output.id)
        .where(Agreement.user_id == user.id)
        .order_by(Agreement.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(query)
    outputs = result.scalars().all()

    return [OutputResponse.model_validate(output) for output in outputs]


@router.get("/output/{output_id}/count")
async def get_agreement_count(
    output_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get agreement count for an output.

    Args:
        output_id: Output ID to get count for
        db: Database session

    Returns:
        Agreement count

    Raises:
        HTTPException: If output not found
    """
    # Verify output exists
    output_result = await db.execute(select(Output).where(Output.id == output_id))
    if output_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    # Count agreements
    count = await db.scalar(
        select(func.count()).select_from(Agreement).where(Agreement.output_id == output_id)
    )

    return {
        "output_id": output_id,
        "agreement_count": count or 0,
    }


@router.get("/check/{output_id}")
async def check_user_agreement(
    output_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Check if current user has agreed with an output.

    Args:
        output_id: Output ID to check
        current_user: Current authenticated user
        db: Database session

    Returns:
        Agreement status

    Raises:
        HTTPException: If output not found
    """
    # Verify output exists
    output_result = await db.execute(select(Output).where(Output.id == output_id))
    if output_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    # Check if user has agreed
    result = await db.execute(
        select(Agreement).where(
            Agreement.user_id == current_user.id,
            Agreement.output_id == output_id,
        )
    )
    agreement = result.scalar_one_or_none()

    if agreement:
        return {
            "output_id": output_id,
            "has_agreed": True,
            "agreed_at": agreement.created_at,
        }
    else:
        return {
            "output_id": output_id,
            "has_agreed": False,
            "agreed_at": None,
        }
