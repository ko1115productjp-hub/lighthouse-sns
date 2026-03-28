"""Similarity search using PostgreSQL pgvector."""

from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.output import Output


class SimilarOutput:
    """Result of similarity search."""

    def __init__(self, output: Output, similarity: float):
        """
        Initialize similar output result.

        Args:
            output: The similar output found
            similarity: Cosine similarity score (0-1, where 1 is identical)
        """
        self.output = output
        self.similarity = similarity


async def find_similar_outputs(
    db: AsyncSession,
    embedding: list[float],
    threshold: float = 0.85,
    limit: int = 5,
    exclude_output_id: Optional[str] = None,
) -> list[SimilarOutput]:
    """
    Find outputs similar to the given embedding vector using pgvector.

    Uses cosine similarity (calculated as 1 - cosine distance) to find
    semantically similar content. Only returns PUBLIC outputs to avoid
    privacy issues.

    Args:
        db: Database session
        embedding: 1536-dimensional embedding vector to search for
        threshold: Minimum similarity score (0-1) to return. Default 0.85
        limit: Maximum number of results to return. Default 5
        exclude_output_id: Optional output ID to exclude from results (e.g., when updating)

    Returns:
        List of SimilarOutput objects sorted by similarity (highest first)

    Example similarity thresholds:
        - > 0.90: Highly similar, likely duplicate or plagiarized
        - 0.85-0.90: Very similar, may be derivative work
        - 0.70-0.85: Moderately similar, shared topic/theme
        - < 0.70: Somewhat related but distinct
    """
    if not embedding or len(embedding) != 1536:
        print(f"⚠️ Invalid embedding dimensions: {len(embedding) if embedding else 0}")
        return []

    try:
        # Convert embedding to string format for pgvector
        # pgvector expects format: '[0.1, 0.2, ...]'
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

        # Build query with cosine similarity
        # Operator <=> is cosine distance, so we use (1 - distance) for similarity
        query = select(
            Output,
            (1 - Output.content_embedding.cosine_distance(text(f"'{embedding_str}'"))).label(
                "similarity"
            ),
        ).where(
            # Only search public outputs
            Output.visibility == "public",
            # Only outputs with embeddings
            Output.content_embedding.isnot(None),
            # Similarity threshold
            (1 - Output.content_embedding.cosine_distance(text(f"'{embedding_str}'")))
            >= threshold,
        )

        # Exclude specific output if provided (useful for update operations)
        if exclude_output_id:
            query = query.where(Output.id != exclude_output_id)

        # Order by similarity (highest first) and limit
        query = query.order_by(text("similarity DESC")).limit(limit)

        result = await db.execute(query)
        rows = result.all()

        # Convert to SimilarOutput objects
        similar_outputs = [SimilarOutput(output=row[0], similarity=row[1]) for row in rows]

        return similar_outputs

    except Exception as e:
        print(f"⚠️ Error during similarity search: {e}")
        return []


async def check_duplicate_content(
    db: AsyncSession,
    embedding: list[float],
    exclude_output_id: Optional[str] = None,
) -> tuple[bool, Optional[SimilarOutput]]:
    """
    Check if content is a duplicate or near-duplicate of existing output.

    This is a convenience function that checks for very high similarity (>0.90)
    which typically indicates duplicate or plagiarized content.

    Args:
        db: Database session
        embedding: 1536-dimensional embedding vector to check
        exclude_output_id: Optional output ID to exclude from check

    Returns:
        Tuple of (is_duplicate, most_similar_output)
        - is_duplicate: True if similarity > 0.90
        - most_similar_output: The most similar output found, or None
    """
    similar = await find_similar_outputs(
        db=db,
        embedding=embedding,
        threshold=0.90,
        limit=1,
        exclude_output_id=exclude_output_id,
    )

    if similar:
        return True, similar[0]
    else:
        return False, None
