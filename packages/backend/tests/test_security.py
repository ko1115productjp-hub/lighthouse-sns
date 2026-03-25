"""Tests for security utilities."""

import pytest
from datetime import timedelta
from uuid import uuid4

from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_password_hash(self):
        """Test password hashing."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        # Hash should be different from original
        assert hashed != password

        # Hash should be verifiable
        assert verify_password(password, hashed) is True

        # Wrong password should not verify
        assert verify_password("WrongPassword", hashed) is False

    def test_different_hashes(self):
        """Test that same password generates different hashes."""
        password = "SamePassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Different hashes
        assert hash1 != hash2

        # But both should verify
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Tests for JWT token functions."""

    def test_create_access_token(self):
        """Test access token creation."""
        user_id = uuid4()
        data = {"sub": str(user_id), "username": "testuser"}

        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = uuid4()
        data = {"sub": str(user_id), "username": "testuser"}

        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_access_token(self):
        """Test access token verification."""
        user_id = uuid4()
        username = "testuser"
        data = {"sub": str(user_id), "username": username}

        token = create_access_token(data)
        token_data = verify_token(token, token_type="access")

        assert token_data is not None
        assert token_data.user_id == user_id
        assert token_data.username == username

    def test_verify_refresh_token(self):
        """Test refresh token verification."""
        user_id = uuid4()
        username = "testuser"
        data = {"sub": str(user_id), "username": username}

        token = create_refresh_token(data)
        token_data = verify_token(token, token_type="refresh")

        assert token_data is not None
        assert token_data.user_id == user_id
        assert token_data.username == username

    def test_verify_wrong_token_type(self):
        """Test that access token cannot be verified as refresh token."""
        user_id = uuid4()
        data = {"sub": str(user_id), "username": "testuser"}

        access_token = create_access_token(data)
        token_data = verify_token(access_token, token_type="refresh")

        # Should fail because token type mismatch
        assert token_data is None

    def test_verify_invalid_token(self):
        """Test verification of invalid token."""
        token_data = verify_token("invalid.token.here", token_type="access")

        assert token_data is None

    def test_verify_expired_token(self):
        """Test verification of expired token."""
        user_id = uuid4()
        data = {"sub": str(user_id), "username": "testuser"}

        # Create token that expires immediately
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        token_data = verify_token(token, token_type="access")

        # Should fail because token is expired
        assert token_data is None

    def test_verify_token_without_sub(self):
        """Test verification of token without user_id."""
        data = {"username": "testuser"}  # Missing 'sub'

        token = create_access_token(data)
        token_data = verify_token(token, token_type="access")

        # Should fail because no user_id
        assert token_data is None
