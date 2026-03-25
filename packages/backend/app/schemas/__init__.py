"""Pydantic schemas for request/response validation."""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserPublicResponse,
    UserListItemResponse,
)
from app.schemas.output import (
    OutputBase,
    OutputCreate,
    OutputUpdate,
    OutputResponse,
    OutputDetailResponse,
    OutputListResponse,
    OutputHistoryResponse,
    PaginationMeta,
    OutputListWithPagination,
)
from app.schemas.citation import (
    CitationCreate,
    CitationResponse,
    CitationWithOutputResponse,
    CitationGraphNode,
    CitationGraphResponse,
)
from app.schemas.agreement import (
    AgreementResponse,
    AgreementUserResponse,
)
from app.schemas.follow import (
    FollowResponse,
)
from app.schemas.auth import (
    Token,
    TokenData,
    LoginRequest,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.schemas.common import (
    SuccessResponse,
    ErrorResponse,
    MessageResponse,
)

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserPublicResponse",
    "UserListItemResponse",
    # Output
    "OutputBase",
    "OutputCreate",
    "OutputUpdate",
    "OutputResponse",
    "OutputDetailResponse",
    "OutputListResponse",
    "OutputHistoryResponse",
    "PaginationMeta",
    "OutputListWithPagination",
    # Citation
    "CitationCreate",
    "CitationResponse",
    "CitationWithOutputResponse",
    "CitationGraphNode",
    "CitationGraphResponse",
    # Agreement
    "AgreementResponse",
    "AgreementUserResponse",
    # Follow
    "FollowResponse",
    # Auth
    "Token",
    "TokenData",
    "LoginRequest",
    "RefreshTokenRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    # Common
    "SuccessResponse",
    "ErrorResponse",
    "MessageResponse",
]
