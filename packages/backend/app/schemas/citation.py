"""Citation-related Pydantic schemas."""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID

from app.models.citation import CitationType
from app.models.output import CategoryEnum


class CitationCreate(BaseModel):
    """Schema for creating a citation."""

    source_output_id: str = Field(..., description="Output that is citing")
    target_output_id: str = Field(..., description="Output being cited")
    citation_type: CitationType
    excerpt: str | None = Field(None, max_length=500, description="Excerpt from cited work")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_output_id": "OUT-2026-0324-A1B2C3",
                "target_output_id": "OUT-2026-0320-XYZ123",
                "citation_type": "agree",
                "excerpt": "The key idea here is that...",
            }
        }
    )


class CitationAuthorPreview(BaseModel):
    """Schema for author preview in citation."""

    id: UUID
    username: str
    display_name: str
    avatar_url: str | None = None


class CitationOutputPreview(BaseModel):
    """Schema for output preview in citation."""

    id: str
    content: str = Field(..., description="Content preview")
    category: CategoryEnum
    created_at: datetime
    author: CitationAuthorPreview


class CitationResponse(BaseModel):
    """Schema for basic citation response."""

    id: UUID
    source_output_id: str
    target_output_id: str
    citation_type: CitationType
    excerpt: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CitationWithOutputResponse(BaseModel):
    """Schema for citation with output information."""

    id: UUID
    source_output_id: str
    target_output_id: str
    citation_type: CitationType
    excerpt: str | None = None
    created_at: datetime
    source_output: CitationOutputPreview

    model_config = ConfigDict(from_attributes=True)


class CitationGraphNode(BaseModel):
    """Schema for citation graph node."""

    id: str
    title: str
    category: CategoryEnum
    author_username: str
    created_at: datetime
    citation_count: int


class CitationGraphResponse(BaseModel):
    """Schema for citation graph data."""

    root_output_id: str
    nodes: list[CitationGraphNode]
    edges: list[dict]
