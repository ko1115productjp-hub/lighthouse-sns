"""Embeddings generation utility using OpenAI API."""

import hashlib
from typing import Optional

import openai
from openai import OpenAI

from app.config import settings


def get_content_hash(content: str) -> str:
    """
    Generate SHA-256 hash of content for caching purposes.

    Args:
        content: Text content to hash

    Returns:
        Hex string of SHA-256 hash
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def generate_embedding(content: str) -> Optional[list[float]]:
    """
    Generate OpenAI embedding vector for the given content.

    Uses text-embedding-3-small model which produces 1536-dimensional vectors.
    Embeddings are used for similarity search to detect duplicate or similar content.

    Args:
        content: Text content to embed

    Returns:
        List of 1536 floats representing the embedding vector, or None on error

    Raises:
        No exceptions - returns None on error and logs warning
    """
    if not settings.OPENAI_API_KEY:
        print("⚠️ OPENAI_API_KEY not set - skipping embedding generation")
        return None

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # Truncate content if too long (max ~8000 tokens for embedding model)
        # Approximate: 1 token ≈ 4 characters in Japanese/English mix
        max_chars = 30000
        truncated_content = content[:max_chars] if len(content) > max_chars else content

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=truncated_content,
            encoding_format="float",
        )

        embedding = response.data[0].embedding

        # Verify dimensions
        if len(embedding) != 1536:
            print(f"⚠️ Unexpected embedding dimensions: {len(embedding)} (expected 1536)")
            return None

        return embedding

    except openai.APIError as e:
        print(f"⚠️ OpenAI API error during embedding generation: {e}")
        return None
    except openai.RateLimitError as e:
        print(f"⚠️ OpenAI rate limit exceeded during embedding generation: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Unexpected error during embedding generation: {e}")
        return None


async def generate_embedding_with_cache(
    content: str,
    cache: Optional[dict[str, list[float]]] = None,
) -> Optional[list[float]]:
    """
    Generate embedding with optional in-memory caching.

    This function checks if an embedding for the same content (identified by hash)
    already exists in the provided cache dictionary. If found, returns cached value.
    Otherwise, generates new embedding and stores it in cache.

    Note: For production use, consider using Redis for persistent caching.

    Args:
        content: Text content to embed
        cache: Optional dictionary mapping content_hash -> embedding vector

    Returns:
        List of 1536 floats representing the embedding vector, or None on error
    """
    if cache is not None:
        content_hash = get_content_hash(content)

        # Check cache
        if content_hash in cache:
            return cache[content_hash]

        # Generate and cache
        embedding = await generate_embedding(content)
        if embedding is not None:
            cache[content_hash] = embedding

        return embedding
    else:
        # No cache provided, generate directly
        return await generate_embedding(content)
