"""Agreement-related Pydantic schemas."""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID


class AgreementResponse(BaseModel):
    """Schema for agreement response."""

    output_id: str
    agreed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgreementUserResponse(BaseModel):
    """Schema for user who agreed."""

    id: UUID
    username: str
    display_name: str
    avatar_url: str | None = None
    agreed_at: datetime

    model_config = ConfigDict(from_attributes=True)
