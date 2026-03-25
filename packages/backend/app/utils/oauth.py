"""OAuth integration utilities for Google and LINE."""

import httpx
from typing import Dict, Optional
from urllib.parse import urlencode

from app.config import settings
from app.schemas.oauth import OAuthUserInfo


class GoogleOAuth:
    """Google OAuth integration."""

    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    @staticmethod
    def get_authorization_url(state: str = "") -> str:
        """Get Google OAuth authorization URL."""
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "state": state,
        }
        return f"{GoogleOAuth.AUTH_URL}?{urlencode(params)}"

    @staticmethod
    async def exchange_code_for_token(code: str) -> Dict[str, str]:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GoogleOAuth.TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_user_info(access_token: str) -> OAuthUserInfo:
        """Get user information from Google."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GoogleOAuth.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json()

            return OAuthUserInfo(
                provider="google",
                oauth_id=data["id"],
                email=data["email"],
                display_name=data.get("name", data["email"].split("@")[0]),
                avatar_url=data.get("picture"),
            )


class LINEOAuth:
    """LINE OAuth integration."""

    AUTH_URL = "https://access.line.me/oauth2/v2.1/authorize"
    TOKEN_URL = "https://api.line.me/oauth2/v2.1/token"
    PROFILE_URL = "https://api.line.me/v2/profile"

    @staticmethod
    def get_authorization_url(state: str = "") -> str:
        """Get LINE OAuth authorization URL."""
        params = {
            "response_type": "code",
            "client_id": settings.LINE_CHANNEL_ID,
            "redirect_uri": settings.LINE_REDIRECT_URI,
            "state": state,
            "scope": "profile openid email",
        }
        return f"{LINEOAuth.AUTH_URL}?{urlencode(params)}"

    @staticmethod
    async def exchange_code_for_token(code: str) -> Dict[str, str]:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LINEOAuth.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.LINE_REDIRECT_URI,
                    "client_id": settings.LINE_CHANNEL_ID,
                    "client_secret": settings.LINE_CHANNEL_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_user_info(access_token: str) -> OAuthUserInfo:
        """Get user information from LINE."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                LINEOAuth.PROFILE_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json()

            return OAuthUserInfo(
                provider="line",
                oauth_id=data["userId"],
                email=data.get("email", f"{data['userId']}@line.me"),  # LINE may not provide email
                display_name=data.get("displayName", "LINE User"),
                avatar_url=data.get("pictureUrl"),
            )
