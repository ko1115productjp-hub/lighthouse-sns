"""Authentication-related Pydantic schemas."""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID
from typing import Any


class LoginRequest(BaseModel):
    """Schema for login request."""

    email: EmailStr
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
            }
        }
    )


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    refresh_token: str
    expires_in: int = 900  # 15 minutes in seconds
    token_type: str = "bearer"
    user: Any  # User information included in login response


class TokenData(BaseModel):
    """Schema for decoded token data."""

    user_id: UUID | None = None
    username: str | None = None


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""

    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
