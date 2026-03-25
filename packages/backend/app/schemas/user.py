"""User-related Pydantic schemas."""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """Base User schema with common fields."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    display_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str = Field(..., min_length=8, max_length=100)
    age_verified: bool = Field(..., description="User confirms they are 18 years or older")
    bio: str | None = Field(None, max_length=1000)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "display_name": "John Doe",
                "password": "SecurePass123!",
                "age_verified": True,
                "bio": "Software engineer and philosopher",
            }
        }
    )


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    display_name: str | None = Field(None, min_length=1, max_length=100)
    bio: str | None = Field(None, max_length=1000)
    avatar_url: str | None = Field(None, max_length=500)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "display_name": "John D.",
                "bio": "Updated bio text",
                "avatar_url": "https://cdn.example.com/avatars/new.jpg",
            }
        }
    )


class UserResponse(BaseModel):
    """Schema for user profile response (own profile)."""

    id: UUID
    email: EmailStr
    username: str
    display_name: str
    bio: str | None = None
    avatar_url: str | None = None
    has_agreed_to_protocol: bool = False
    followers_count: int = 0
    following_count: int = 0
    outputs_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserPublicResponse(BaseModel):
    """Schema for public user profile (viewed by others)."""

    id: UUID
    username: str
    display_name: str
    bio: str | None = None
    avatar_url: str | None = None
    followers_count: int = 0
    following_count: int = 0
    outputs_count: int = 0
    is_following: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListItemResponse(BaseModel):
    """Schema for user in a list (followers/following)."""

    id: UUID
    username: str
    display_name: str
    avatar_url: str | None = None
    followed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
