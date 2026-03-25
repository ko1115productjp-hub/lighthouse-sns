"""OAuth schemas for social login."""

from pydantic import BaseModel, Field
from typing import Optional


class OAuthCallbackParams(BaseModel):
    """OAuth callback parameters."""

    code: str = Field(..., description="Authorization code from OAuth provider")
    state: Optional[str] = Field(None, description="State parameter for CSRF protection")


class OAuthUserInfo(BaseModel):
    """User information from OAuth provider."""

    provider: str = Field(..., description="OAuth provider name (google, line)")
    oauth_id: str = Field(..., description="User ID from OAuth provider")
    email: str = Field(..., description="User email")
    display_name: str = Field(..., description="User display name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")


class TokenResponse(BaseModel):
    """Token response for OAuth login."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict
