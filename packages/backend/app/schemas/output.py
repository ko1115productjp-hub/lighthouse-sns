"""Output (Post) related Pydantic schemas."""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID

from app.models.output import VisibilityEnum, AIReviewStatus, CategoryEnum


class OutputBase(BaseModel):
    """Base Output schema with common fields."""

    content: str = Field(..., min_length=1, max_length=50000)
    category: CategoryEnum
    tags: list[str] = Field(default_factory=list, max_length=10)


class OutputCreate(OutputBase):
    """Schema for creating a new output."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "# My First Post\n\nThis is a markdown content...",
                "category": "philosophy",
                "tags": ["existentialism", "consciousness"],
            }
        }
    )


class OutputUpdate(BaseModel):
    """Schema for updating an output."""

    content: str | None = Field(None, min_length=1, max_length=50000)
    category: CategoryEnum | None = None
    tags: list[str] | None = Field(None, max_length=10)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "# Updated Post\n\nUpdated content...",
                "category": "technology",
                "tags": ["updated", "tags"],
            }
        }
    )


class OutputAuthorResponse(BaseModel):
    """Schema for output author information."""

    id: UUID
    username: str
    display_name: str
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class OutputResponse(BaseModel):
    """Schema for basic output response."""

    id: str
    user_id: UUID | None = None
    content: str
    category: CategoryEnum
    tags: list[str]
    visibility: VisibilityEnum
    ai_review_status: AIReviewStatus
    novelty_score: float | None = None
    content_hash: str  # SHA-256 of content only
    hash: str  # SHA-256 of full output (content + metadata + timestamp)
    previous_hash: str | None = None  # Hash of previous version (for edit history chain)
    version: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class OutputDetailResponse(BaseModel):
    """Schema for detailed output response with author and stats."""

    id: str
    user_id: UUID | None = None
    content: str
    category: CategoryEnum
    tags: list[str]
    visibility: VisibilityEnum
    ai_review_status: AIReviewStatus
    novelty_score: float | None = None
    citation_count: int = 0
    agreement_count: int = 0
    content_hash: str  # SHA-256 of content only
    hash: str  # SHA-256 of full output
    previous_hash: str | None = None  # Hash of previous version
    version: int
    created_at: datetime
    updated_at: datetime | None = None
    author: OutputAuthorResponse

    model_config = ConfigDict(from_attributes=True)


class OutputListResponse(BaseModel):
    """Schema for output in a list (preview)."""

    id: str
    content: str = Field(..., description="Truncated content for preview")
    category: CategoryEnum
    tags: list[str]
    visibility: VisibilityEnum
    novelty_score: float | None = None
    citation_count: int = 0
    agreement_count: int = 0
    created_at: datetime
    author: OutputAuthorResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class OutputHistoryResponse(BaseModel):
    """Schema for output history entry."""

    version: int
    content: str
    hash: str
    previous_hash: str | None = None
    edited_by: UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginationMeta(BaseModel):
    """Schema for pagination metadata."""

    cursor: str | None = None
    has_next: bool = False
    count: int = 0


class OutputListWithPagination(BaseModel):
    """Schema for paginated output list."""

    data: list[OutputListResponse]
    pagination: PaginationMeta


class HashVerificationResponse(BaseModel):
    """Schema for hash verification response."""

    output_id: str
    content_hash_valid: bool
    full_hash_valid: bool
    hash_chain_valid: bool  # Whether the chain from original to current version is valid
    message: str
