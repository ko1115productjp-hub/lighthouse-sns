"""Tests for user management API endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import get_db, Base
from app.models.user import User
from app.models.follow import Follow
from app.utils.security import get_password_hash

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@postgres:5432/sns_test"


@pytest.fixture(scope="function")
async def test_db():
    """Create a test database and session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    TestSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with TestSessionLocal() as session:
        yield session

    await engine.dispose()


@pytest.fixture(scope="function")
async def client(test_db: AsyncSession):
    """Create a test client with dependency override."""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(test_db: AsyncSession):
    """Create a test user."""
    user = User(
        email="testuser@example.com",
        username="testuser",
        display_name="Test User",
        password_hash=get_password_hash("TestPass123!"),
        age_verified=True,
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def test_user2(test_db: AsyncSession):
    """Create a second test user."""
    user = User(
        email="user2@example.com",
        username="user2",
        display_name="User Two",
        password_hash=get_password_hash("TestPass123!"),
        age_verified=True,
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def auth_token(client: AsyncClient, test_user: User):
    """Get authentication token for test user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "TestPass123!"},
    )
    return response.json()["access_token"]


class TestUpdateProfile:
    """Tests for profile update endpoint."""

    @pytest.mark.asyncio
    async def test_update_profile_success(
        self, client: AsyncClient, auth_token: str, test_db: AsyncSession
    ):
        """Test successful profile update."""
        response = await client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "display_name": "Updated Name",
                "bio": "Updated bio",
                "avatar_url": "https://example.com/avatar.jpg",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Name"
        assert data["bio"] == "Updated bio"
        assert data["avatar_url"] == "https://example.com/avatar.jpg"

    @pytest.mark.asyncio
    async def test_update_profile_partial(
        self, client: AsyncClient, auth_token: str
    ):
        """Test partial profile update."""
        response = await client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"display_name": "Only Name Updated"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Only Name Updated"

    @pytest.mark.asyncio
    async def test_update_profile_unauthorized(self, client: AsyncClient):
        """Test profile update without authentication."""
        response = await client.patch(
            "/api/v1/users/me",
            json={"display_name": "Should Fail"},
        )

        assert response.status_code == 403


class TestSearchUsers:
    """Tests for user search endpoint."""

    @pytest.mark.asyncio
    async def test_search_users_success(
        self,
        client: AsyncClient,
        auth_token: str,
        test_user: User,
        test_user2: User,
    ):
        """Test successful user search."""
        response = await client.get(
            "/api/v1/users/search?q=user",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_search_users_by_username(
        self, client: AsyncClient, auth_token: str, test_user2: User
    ):
        """Test search by exact username."""
        response = await client.get(
            "/api/v1/users/search?q=user2",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["username"] == "user2"

    @pytest.mark.asyncio
    async def test_search_users_pagination(
        self, client: AsyncClient, auth_token: str, test_user: User
    ):
        """Test search with pagination."""
        response = await client.get(
            "/api/v1/users/search?q=test&limit=1&offset=0",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 1


class TestGetUserByUsername:
    """Tests for get user by username endpoint."""

    @pytest.mark.asyncio
    async def test_get_user_success(
        self, client: AsyncClient, auth_token: str, test_user2: User
    ):
        """Test successfully getting user by username."""
        response = await client.get(
            f"/api/v1/users/{test_user2.username}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user2.username
        assert data["display_name"] == test_user2.display_name
        assert "followers_count" in data
        assert "following_count" in data

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client: AsyncClient, auth_token: str):
        """Test getting non-existent user."""
        response = await client.get(
            "/api/v1/users/nonexistentuser",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 404


class TestFollowUnfollow:
    """Tests for follow/unfollow endpoints."""

    @pytest.mark.asyncio
    async def test_follow_user_success(
        self,
        client: AsyncClient,
        auth_token: str,
        test_user: User,
        test_user2: User,
        test_db: AsyncSession,
    ):
        """Test successfully following a user."""
        response = await client.post(
            f"/api/v1/users/{test_user2.username}/follow",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_following"] is True
        assert "followed_at" in data

        # Verify in database
        result = await test_db.execute(
            select(Follow).where(
                Follow.follower_id == test_user.id,
                Follow.followed_id == test_user2.id,
            )
        )
        assert result.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_follow_user_already_following(
        self,
        client: AsyncClient,
        auth_token: str,
        test_user: User,
        test_user2: User,
        test_db: AsyncSession,
    ):
        """Test following a user that is already followed."""
        # Create existing follow
        follow = Follow(follower_id=test_user.id, followed_id=test_user2.id)
        test_db.add(follow)
        await test_db.commit()

        response = await client.post(
            f"/api/v1/users/{test_user2.username}/follow",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        assert response.json()["is_following"] is True

    @pytest.mark.asyncio
    async def test_follow_self(self, client: AsyncClient, auth_token: str, test_user: User):
        """Test attempting to follow yourself."""
        response = await client.post(
            f"/api/v1/users/{test_user.username}/follow",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 400
        assert "Cannot follow yourself" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_follow_nonexistent_user(
        self, client: AsyncClient, auth_token: str
    ):
        """Test following a non-existent user."""
        response = await client.post(
            "/api/v1/users/nonexistentuser/follow",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unfollow_user_success(
        self,
        client: AsyncClient,
        auth_token: str,
        test_user: User,
        test_user2: User,
        test_db: AsyncSession,
    ):
        """Test successfully unfollowing a user."""
        # Create follow relationship first
        follow = Follow(follower_id=test_user.id, followed_id=test_user2.id)
        test_db.add(follow)
        await test_db.commit()

        response = await client.delete(
            f"/api/v1/users/{test_user2.username}/follow",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        assert "Successfully unfollowed" in response.json()["message"]

        # Verify removed from database
        result = await test_db.execute(
            select(Follow).where(
                Follow.follower_id == test_user.id,
                Follow.followed_id == test_user2.id,
            )
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_unfollow_not_following(
        self, client: AsyncClient, auth_token: str, test_user2: User
    ):
        """Test unfollowing a user you're not following."""
        response = await client.delete(
            f"/api/v1/users/{test_user2.username}/follow",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 404


class TestFollowersFollowing:
    """Tests for followers and following list endpoints."""

    @pytest.mark.asyncio
    async def test_get_followers(
        self,
        client: AsyncClient,
        test_user: User,
        test_user2: User,
        test_db: AsyncSession,
    ):
        """Test getting followers list."""
        # user2 follows test_user
        follow = Follow(follower_id=test_user2.id, followed_id=test_user.id)
        test_db.add(follow)
        await test_db.commit()

        response = await client.get(f"/api/v1/users/{test_user.username}/followers")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["username"] == test_user2.username
        assert "followed_at" in data[0]

    @pytest.mark.asyncio
    async def test_get_following(
        self,
        client: AsyncClient,
        test_user: User,
        test_user2: User,
        test_db: AsyncSession,
    ):
        """Test getting following list."""
        # test_user follows user2
        follow = Follow(follower_id=test_user.id, followed_id=test_user2.id)
        test_db.add(follow)
        await test_db.commit()

        response = await client.get(f"/api/v1/users/{test_user.username}/following")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["username"] == test_user2.username

    @pytest.mark.asyncio
    async def test_get_followers_pagination(
        self, client: AsyncClient, test_user: User, test_db: AsyncSession
    ):
        """Test followers list pagination."""
        # Create multiple followers
        for i in range(3):
            follower = User(
                email=f"follower{i}@example.com",
                username=f"follower{i}",
                display_name=f"Follower {i}",
                password_hash=get_password_hash("TestPass123!"),
                age_verified=True,
            )
            test_db.add(follower)
            await test_db.flush()

            follow = Follow(follower_id=follower.id, followed_id=test_user.id)
            test_db.add(follow)

        await test_db.commit()

        response = await client.get(
            f"/api/v1/users/{test_user.username}/followers?limit=2&offset=0"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_followers_nonexistent_user(self, client: AsyncClient):
        """Test getting followers for non-existent user."""
        response = await client.get("/api/v1/users/nonexistentuser/followers")

        assert response.status_code == 404
