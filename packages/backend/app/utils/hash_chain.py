"""Hash chain utilities for output immutability."""

import hashlib
from datetime import datetime, timezone
import json


def generate_content_hash(content: str) -> str:
    """
    Generate SHA-256 hash for output content only.
    This hash is purely based on content and can be used for deduplication.

    Args:
        content: The output content text

    Returns:
        SHA-256 hash string (64 characters)
    """
    # Hash only the content for purity
    hash_object = hashlib.sha256(content.encode("utf-8"))
    return hash_object.hexdigest()


def generate_full_hash(
    content: str,
    user_id: str,
    category: str,
    tags: list[str],
    created_at: datetime,
    previous_hash: str | None = None,
    referenced_entity_type: str | None = None,
    referenced_entity_id: str | None = None,
    referenced_entity_data: dict | None = None,
) -> str:
    """
    Generate SHA-256 hash for full output (content + metadata + timestamp).
    This hash includes all data and the creation timestamp for uniqueness.

    Args:
        content: The output content text
        user_id: User ID who created the output
        category: Output category
        tags: List of tags
        created_at: Creation timestamp (fixed for verification)
        previous_hash: Hash of the previous version (for edit history chain)
        referenced_entity_type: Type of referenced entity (place, book, movie, etc.)
        referenced_entity_id: External API ID for the referenced entity
        referenced_entity_data: Metadata from external APIs

    Returns:
        SHA-256 hash string (64 characters)
    """
    # Create a canonical representation of the data
    data = {
        "content": content,
        "user_id": user_id,
        "category": category,
        "tags": sorted(tags),  # Sort tags for consistency
        "created_at": created_at.isoformat(),  # Use stored timestamp
        "previous_hash": previous_hash,
        "referenced_entity_type": referenced_entity_type,
        "referenced_entity_id": referenced_entity_id,
        "referenced_entity_data": referenced_entity_data,
    }

    # Convert to JSON string with sorted keys for consistency
    data_string = json.dumps(data, sort_keys=True, ensure_ascii=False)

    # Generate SHA-256 hash
    hash_object = hashlib.sha256(data_string.encode("utf-8"))
    return hash_object.hexdigest()


def generate_output_id(hash_value: str, created_at: datetime | None = None) -> str:
    """
    Generate output ID in format OUT-YYYY-MMDD-HASH.

    Args:
        hash_value: The SHA-256 hash of the full output
        created_at: Optional creation timestamp (uses now if not provided)

    Returns:
        Output ID string (e.g., "OUT-2026-0324-abc123...")
    """
    timestamp = created_at if created_at else datetime.now(timezone.utc)
    date_string = timestamp.strftime("%Y-%m%d")

    # Use first 8 characters of the hash for the ID
    hash_suffix = hash_value[:8]

    return f"OUT-{date_string}-{hash_suffix}"


def verify_content_hash(content: str, claimed_hash: str) -> bool:
    """
    Verify that the claimed content hash matches the actual content.

    Args:
        content: The output content text
        claimed_hash: The content_hash stored in the database

    Returns:
        True if hash is valid, False otherwise
    """
    if not claimed_hash or len(claimed_hash) != 64:
        return False

    # Verify it's a valid hex string
    try:
        int(claimed_hash, 16)
    except ValueError:
        return False

    # Regenerate hash and compare
    actual_hash = generate_content_hash(content)
    return actual_hash == claimed_hash


def verify_full_hash(
    content: str,
    user_id: str,
    category: str,
    tags: list[str],
    created_at: datetime,
    claimed_hash: str,
    previous_hash: str | None = None,
    referenced_entity_type: str | None = None,
    referenced_entity_id: str | None = None,
    referenced_entity_data: dict | None = None,
) -> bool:
    """
    Verify that the claimed full hash matches the actual output data.

    Args:
        content: The output content text
        user_id: User ID who created the output
        category: Output category
        tags: List of tags
        created_at: Creation timestamp
        claimed_hash: The hash stored in the database
        previous_hash: Hash of the previous version (for edits)
        referenced_entity_type: Type of referenced entity (place, book, movie, etc.)
        referenced_entity_id: External API ID for the referenced entity
        referenced_entity_data: Metadata from external APIs

    Returns:
        True if hash is valid, False otherwise
    """
    if not claimed_hash or len(claimed_hash) != 64:
        return False

    # Verify it's a valid hex string
    try:
        int(claimed_hash, 16)
    except ValueError:
        return False

    # Regenerate hash and compare
    actual_hash = generate_full_hash(
        content=content,
        user_id=user_id,
        category=category,
        tags=tags,
        created_at=created_at,
        previous_hash=previous_hash,
        referenced_entity_type=referenced_entity_type,
        referenced_entity_id=referenced_entity_id,
        referenced_entity_data=referenced_entity_data,
    )
    return actual_hash == claimed_hash


def create_merkle_root(hashes: list[str]) -> str:
    """
    Create a Merkle root hash from a list of output hashes.
    Used for daily anchoring to external blockchain.

    Args:
        hashes: List of output hash strings

    Returns:
        Merkle root hash
    """
    if not hashes:
        return hashlib.sha256(b"").hexdigest()

    if len(hashes) == 1:
        return hashes[0]

    # Build Merkle tree
    current_level = hashes.copy()

    while len(current_level) > 1:
        next_level = []

        # Process pairs
        for i in range(0, len(current_level), 2):
            if i + 1 < len(current_level):
                # Combine two hashes
                combined = current_level[i] + current_level[i + 1]
                hash_object = hashlib.sha256(combined.encode("utf-8"))
                next_level.append(hash_object.hexdigest())
            else:
                # Odd number, promote the last hash
                next_level.append(current_level[i])

        current_level = next_level

    return current_level[0]
