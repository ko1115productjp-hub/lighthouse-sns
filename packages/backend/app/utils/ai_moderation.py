"""AI moderation utilities using OpenAI Moderation API."""

from openai import AsyncOpenAI
from app.config import settings


class ModerationResult:
    """Result from AI moderation check."""

    def __init__(
        self,
        is_safe: bool,
        flagged_categories: list[str] | None = None,
        novelty_score: float | None = None,
    ):
        self.is_safe = is_safe
        self.flagged_categories = flagged_categories or []
        self.novelty_score = novelty_score


async def check_content_safety(content: str) -> ModerationResult:
    """
    Check if content is safe using OpenAI Moderation API.

    Args:
        content: The content to check

    Returns:
        ModerationResult with safety information
    """
    # If no API key is set, skip moderation (for development)
    if not settings.OPENAI_API_KEY:
        return ModerationResult(is_safe=True)

    try:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.moderations.create(input=content)

        # Get the first result
        result = response.results[0]

        # Check if content was flagged
        if result.flagged:
            # Collect flagged categories
            flagged = [
                category
                for category, flagged in result.categories.model_dump().items()
                if flagged
            ]

            return ModerationResult(is_safe=False, flagged_categories=flagged)

        return ModerationResult(is_safe=True)

    except Exception as e:
        # Log the error in production
        print(f"Moderation API error: {e}")
        # Default to safe if API fails
        return ModerationResult(is_safe=True)


async def calculate_novelty_score(
    content: str, existing_outputs: list[str] | None = None
) -> float:
    """
    Calculate novelty score for content.

    This is a placeholder for Phase 2 implementation.
    In Phase 2, this will use OpenAI Embeddings + vector similarity search.

    Args:
        content: The content to score
        existing_outputs: Optional list of existing content to compare against

    Returns:
        Novelty score between 0.0 and 1.0
    """
    # Phase 1: Simple placeholder - return high novelty for all content
    # Phase 2: Will use embeddings + Pinecone/Weaviate for similarity search

    # For now, basic heuristic:
    # - Very short content (< 50 chars) gets lower score
    # - Longer, more detailed content gets higher score

    content_length = len(content)

    if content_length < 50:
        return 0.3
    elif content_length < 200:
        return 0.6
    elif content_length < 500:
        return 0.8
    else:
        return 0.9


async def determine_visibility(novelty_score: float, threshold: float = 0.5) -> str:
    """
    Determine if output should be public or private based on novelty score.

    Args:
        novelty_score: The calculated novelty score (0.0 to 1.0)
        threshold: Minimum score required for public visibility

    Returns:
        "public" or "private"
    """
    return "public" if novelty_score >= threshold else "private"
