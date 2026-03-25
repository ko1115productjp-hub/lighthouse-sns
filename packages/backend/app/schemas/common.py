"""Common schemas for API responses."""

from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime


class MetaResponse(BaseModel):
    """Metadata for API responses."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str | None = None


class SuccessResponse(BaseModel):
    """Standard success response."""

    data: Any
    meta: MetaResponse = Field(default_factory=MetaResponse)


class ErrorDetail(BaseModel):
    """Error detail for validation errors."""

    field: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response."""

    code: str
    message: str
    details: list[ErrorDetail] | None = None
    meta: MetaResponse = Field(default_factory=MetaResponse)


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str
