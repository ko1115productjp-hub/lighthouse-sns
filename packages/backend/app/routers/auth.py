"""Authentication API endpoints."""

import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.auth import LoginRequest, Token, RefreshTokenRequest
from app.schemas.user import UserCreate, UserResponse
from app.schemas.oauth import OAuthCallbackParams, TokenResponse
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.utils.oauth import GoogleOAuth, LINEOAuth
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)) -> UserResponse:
    """
    Register a new user account.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user information

    Raises:
        HTTPException: If email or username already exists
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Create new user
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        display_name=user_data.display_name,
        password_hash=get_password_hash(user_data.password),
        age_verified=user_data.age_verified,
        bio=user_data.bio,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse.model_validate(new_user)


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)) -> Token:
    """
    Authenticate user and return access and refresh tokens.

    Args:
        login_data: Login credentials
        db: Database session

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if user is None or not verify_password(login_data.password, user.password_hash or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # Check if user is deleted
    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deleted",
        )

    # Create tokens
    token_data = {"sub": str(user.id), "username": user.username}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Build user response
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        display_name=user.display_name,
        bio=user.bio,
        avatar_url=user.avatar_url,
        has_agreed_to_protocol=user.has_agreed_to_protocol,
        followers_count=0,  # TODO: Query actual counts
        following_count=0,
        outputs_count=0,
        created_at=user.created_at,
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_response,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Refresh access token using a valid refresh token.

    Args:
        refresh_data: Refresh token
        db: Database session

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Verify refresh token
    token_data = verify_token(refresh_data.refresh_token, token_type="refresh")

    if token_data is None or token_data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user still exists and is active
    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new tokens
    new_token_data = {"sub": str(user.id), "username": user.username}
    access_token = create_access_token(new_token_data)
    new_refresh_token = create_refresh_token(new_token_data)

    # Build user response
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        display_name=user.display_name,
        bio=user.bio,
        avatar_url=user.avatar_url,
        has_agreed_to_protocol=user.has_agreed_to_protocol,
        followers_count=0,  # TODO: Query actual counts
        following_count=0,
        outputs_count=0,
        created_at=user.created_at,
    )

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_response,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    return UserResponse.model_validate(current_user)


# ============================================================================
# OAuth Endpoints
# ============================================================================


@router.get("/google")
async def google_login():
    """Redirect to Google OAuth authorization page."""
    authorization_url = GoogleOAuth.get_authorization_url(state="random_state_string")
    return RedirectResponse(url=authorization_url)


@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    """
    Handle Google OAuth callback.

    Args:
        code: Authorization code from Google
        db: Database session

    Returns:
        Redirect to frontend with tokens
    """
    try:
        # Exchange code for access token
        token_data = await GoogleOAuth.exchange_code_for_token(code)
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get access token from Google",
            )

        # Get user info from Google
        user_info = await GoogleOAuth.get_user_info(access_token)

        # Check if user already exists (by OAuth ID or email)
        result = await db.execute(
            select(User).where(
                or_(
                    User.oauth_id == user_info.oauth_id,
                    User.email == user_info.email,
                )
            )
        )
        user = result.scalar_one_or_none()

        if user:
            # Update OAuth fields if not set
            if not user.oauth_provider:
                user.oauth_provider = user_info.provider
                user.oauth_id = user_info.oauth_id
                await db.commit()
        else:
            # Create new user
            # Generate unique username from email
            base_username = user_info.email.split("@")[0]
            username = base_username
            counter = 1

            while True:
                result = await db.execute(select(User).where(User.username == username))
                if result.scalar_one_or_none() is None:
                    break
                username = f"{base_username}{counter}"
                counter += 1

            user = User(
                email=user_info.email,
                username=username,
                display_name=user_info.display_name,
                avatar_url=user_info.avatar_url,
                oauth_provider=user_info.provider,
                oauth_id=user_info.oauth_id,
                password_hash=None,  # No password for OAuth users
                age_verified=True,  # Assume age verification through OAuth
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Create JWT tokens
        token_data_dict = {"sub": str(user.id), "username": user.username}
        jwt_access_token = create_access_token(token_data_dict)
        jwt_refresh_token = create_refresh_token(token_data_dict)

        # Redirect to frontend with tokens
        redirect_url = f"{settings.FRONTEND_URL}/oauth-callback?access_token={jwt_access_token}&refresh_token={jwt_refresh_token}"
        return RedirectResponse(url=redirect_url)

    except Exception as e:
        # Log the error for debugging
        logging.error(f"OAuth callback error: {str(e)}", exc_info=True)

        # Redirect to frontend with error
        try:
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=oauth_failed")
        except Exception as redirect_error:
            logging.error(f"Failed to redirect after OAuth error: {str(redirect_error)}")
            return RedirectResponse(url="https://lighthouse-sns-frontend.vercel.app/login?error=oauth_failed")


@router.get("/line")
async def line_login():
    """Redirect to LINE OAuth authorization page."""
    authorization_url = LINEOAuth.get_authorization_url(state="random_state_string")
    return RedirectResponse(url=authorization_url)


@router.get("/line/callback")
async def line_callback(code: str, db: AsyncSession = Depends(get_db)):
    """
    Handle LINE OAuth callback.

    Args:
        code: Authorization code from LINE
        db: Database session

    Returns:
        Redirect to frontend with tokens
    """
    try:
        # Exchange code for access token
        token_data = await LINEOAuth.exchange_code_for_token(code)
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get access token from LINE",
            )

        # Get user info from LINE
        user_info = await LINEOAuth.get_user_info(access_token)

        # Check if user already exists (by OAuth ID or email)
        result = await db.execute(
            select(User).where(
                or_(
                    User.oauth_id == user_info.oauth_id,
                    User.email == user_info.email,
                )
            )
        )
        user = result.scalar_one_or_none()

        if user:
            # Update OAuth fields if not set
            if not user.oauth_provider:
                user.oauth_provider = user_info.provider
                user.oauth_id = user_info.oauth_id
                await db.commit()
        else:
            # Create new user
            # Generate unique username from LINE user ID
            base_username = f"line_{user_info.oauth_id[:8]}"
            username = base_username
            counter = 1

            while True:
                result = await db.execute(select(User).where(User.username == username))
                if result.scalar_one_or_none() is None:
                    break
                username = f"{base_username}_{counter}"
                counter += 1

            user = User(
                email=user_info.email,
                username=username,
                display_name=user_info.display_name,
                avatar_url=user_info.avatar_url,
                oauth_provider=user_info.provider,
                oauth_id=user_info.oauth_id,
                password_hash=None,  # No password for OAuth users
                age_verified=True,  # Assume age verification through OAuth
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Create JWT tokens
        token_data_dict = {"sub": str(user.id), "username": user.username}
        jwt_access_token = create_access_token(token_data_dict)
        jwt_refresh_token = create_refresh_token(token_data_dict)

        # Redirect to frontend with tokens
        redirect_url = f"{settings.FRONTEND_URL}/oauth-callback?access_token={jwt_access_token}&refresh_token={jwt_refresh_token}"
        return RedirectResponse(url=redirect_url)

    except Exception as e:
        # Log the error for debugging
        logging.error(f"OAuth callback error: {str(e)}", exc_info=True)

        # Redirect to frontend with error
        try:
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=oauth_failed")
        except Exception as redirect_error:
            logging.error(f"Failed to redirect after OAuth error: {str(redirect_error)}")
            return RedirectResponse(url="https://lighthouse-sns-frontend.vercel.app/login?error=oauth_failed")
