"""Hash verification endpoint for output integrity checking."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_optional_current_user
from app.models.user import User
from app.models.output import Output
from app.models.output_history import OutputHistory
from app.schemas.output import HashVerificationResponse
from app.utils.hash_chain import verify_content_hash, verify_full_hash

router = APIRouter(prefix="/outputs", tags=["Hash Verification"])


@router.get("/{output_id}/verify", response_model=HashVerificationResponse)
async def verify_output_hash(
    output_id: str,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> HashVerificationResponse:
    """
    Verify the hash integrity of a PUBLIC output and its edit history chain.

    This endpoint validates:
    1. Content hash (SHA-256 of content only)
    2. Full hash (SHA-256 of content + metadata + timestamp)
    3. Hash chain (ensures the chain from original to current version is valid)

    IMPORTANT: Hash verification is only available for PUBLIC outputs.
    This ensures transparency and allows anyone to verify the immutability
    of public content on the platform.

    Args:
        output_id: Output ID to verify
        current_user: Current authenticated user (optional)
        db: Database session

    Returns:
        Hash verification results

    Raises:
        HTTPException: If output not found or output is private
    """
    # Find output
    result = await db.execute(select(Output).where(Output.id == output_id))
    output = result.scalar_one_or_none()

    if output is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found",
        )

    # Only allow verification of public outputs
    if output.visibility.value == "private":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hash verification is only available for public outputs",
        )

    # Verify content hash
    content_hash_valid = verify_content_hash(
        content=output.content,
        claimed_hash=output.content_hash,
    )

    # Verify full hash
    # DEBUG: Log the parameters for debugging
    import logging
    logger = logging.getLogger(__name__)

    # Generate the hash to see what we get
    from app.utils.hash_chain import generate_full_hash
    actual_hash = generate_full_hash(
        content=output.content,
        user_id=str(output.user_id) if output.user_id else "",
        category=output.category.value,
        tags=output.tags or [],  # Convert None to empty list like in creation
        created_at=output.created_at,
        previous_hash=output.previous_hash,
        referenced_entity_type=output.referenced_entity_type,
        referenced_entity_id=output.referenced_entity_id,
        referenced_entity_data=output.referenced_entity_data,
    )

    logger.info(f"Hash verification for output {output_id}:")
    logger.info(f"  Claimed hash: {output.hash}")
    logger.info(f"  Actual hash:  {actual_hash}")
    logger.info(f"  Match: {actual_hash == output.hash}")
    logger.info(f"  Tags: {output.tags}")
    logger.info(f"  Referenced entity type: {output.referenced_entity_type}")
    logger.info(f"  Referenced entity data: {output.referenced_entity_data}")

    full_hash_valid = verify_full_hash(
        content=output.content,
        user_id=str(output.user_id) if output.user_id else "",
        category=output.category.value,
        tags=output.tags or [],  # Convert None to empty list like in creation
        created_at=output.created_at,
        claimed_hash=output.hash,
        previous_hash=output.previous_hash,
        referenced_entity_type=output.referenced_entity_type,
        referenced_entity_id=output.referenced_entity_id,
        referenced_entity_data=output.referenced_entity_data,
    )

    # Verify hash chain by checking history
    hash_chain_valid = True
    verification_messages = []

    if output.version > 1 and output.previous_hash:
        # Check if previous_hash exists in history
        history_result = await db.execute(
            select(OutputHistory)
            .where(OutputHistory.output_id == output_id)
            .order_by(OutputHistory.version.desc())
        )
        history_entries = history_result.scalars().all()

        if history_entries:
            # Find the entry with hash matching previous_hash
            previous_version_found = False
            for entry in history_entries:
                if entry.hash == output.previous_hash:
                    previous_version_found = True
                    break

            if not previous_version_found:
                hash_chain_valid = False
                verification_messages.append(
                    f"Previous hash {output.previous_hash[:16]}... not found in history"
                )
        else:
            hash_chain_valid = False
            verification_messages.append(
                "No history found but output has previous_hash (version > 1)"
            )

    # Build message
    if content_hash_valid and full_hash_valid and hash_chain_valid:
        message = "✅ All hashes verified successfully. This output has not been tampered with."
    else:
        issues = []
        if not content_hash_valid:
            issues.append("content hash mismatch")
        if not full_hash_valid:
            issues.append("full hash mismatch")
        if not hash_chain_valid:
            issues.append("hash chain broken")
        message = f"⚠️ Verification failed: {', '.join(issues)}"
        if verification_messages:
            message += f". Details: {'; '.join(verification_messages)}"

    return HashVerificationResponse(
        output_id=output_id,
        content_hash_valid=content_hash_valid,
        full_hash_valid=full_hash_valid,
        hash_chain_valid=hash_chain_valid,
        message=message,
    )
