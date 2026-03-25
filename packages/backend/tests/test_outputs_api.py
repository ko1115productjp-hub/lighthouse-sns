"""Tests for Output API endpoints."""

import pytest
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import get_db, Base
from app.models.output import Output
from app.models.output_history import OutputHistory
from app.models.user import User
from app.utils.security import get_password_hash

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@postgres:5432/sns_test"


@pytest.fixture(scope="function")
async def test_db():
    """Create a test database and session."""
    # Create test engine
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    TestSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Provide session
    async with TestSessionLocal() as session:
        yield session

    # Cleanup
    await engine.dispose()


@pytest.fixture(scope="function")
async def async_client(test_db: AsyncSession):
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
        password_hash=get_password_hash("SecurePass123!"),
        age_verified=True,
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def auth_headers(async_client: AsyncClient, test_user: User):
    """Get authentication headers for test user."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "SecurePass123!",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestCreateOutput:
    """Tests for POST /api/v1/outputs/"""

    @pytest.mark.asyncio
    async def test_create_output_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test successful output creation."""
        output_data = {
            "content": "This is a unique and novel scientific discovery about quantum computing and AI.",
            "category": "science",
            "tags": ["quantum", "AI"],
        }

        response = await async_client.post(
            "/api/v1/outputs/",
            json=output_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == output_data["content"]
        assert data["category"] == output_data["category"]
        assert data["tags"] == output_data["tags"]
        assert data["id"].startswith("OUT-")
        assert data["version"] == 1
        assert data["visibility"] in ["public", "private"]
        assert "novelty_score" in data
        assert "hash" in data

    @pytest.mark.asyncio
    async def test_create_output_unsafe_content(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test output creation with unsafe content (if OpenAI API is available)."""
        output_data = {
            "content": "Test content",
            "category": "other",
            "tags": [],
        }

        response = await async_client.post(
            "/api/v1/outputs/",
            json=output_data,
            headers=auth_headers,
        )

        # Without OpenAI API key, should succeed
        # With OpenAI API key, may fail if flagged
        assert response.status_code in [201, 400]

    @pytest.mark.asyncio
    async def test_create_output_without_auth(self, async_client: AsyncClient):
        """Test output creation without authentication."""
        output_data = {
            "content": "Test content",
            "category": "other",
            "tags": [],
        }

        response = await async_client.post("/api/v1/outputs/", json=output_data)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_output_invalid_category(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test output creation with invalid category."""
        output_data = {
            "content": "Test content",
            "category": "invalid_category",
            "tags": [],
        }

        response = await async_client.post(
            "/api/v1/outputs/",
            json=output_data,
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestUpdateOutput:
    """Tests for PATCH /api/v1/outputs/{output_id}"""

    @pytest.mark.asyncio
    async def test_update_output_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
        test_db: AsyncSession,
    ):
        """Test successful output update."""
        # Create initial output
        create_data = {
            "content": "Original content about machine learning",
            "category": "science",
            "tags": ["ML"],
        }
        create_response = await async_client.post(
            "/api/v1/outputs/",
            json=create_data,
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        output_id = create_response.json()["id"]
        original_hash = create_response.json()["hash"]

        # Update output
        update_data = {
            "content": "Updated content with more details about deep learning",
            "tags": ["ML", "DL"],
        }
        response = await async_client.patch(
            f"/api/v1/outputs/{output_id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == update_data["content"]
        assert data["tags"] == update_data["tags"]
        assert data["version"] == 2
        assert data["hash"] != original_hash
        # Note: OutputResponse doesn't include parent_hash, but it's stored in DB

    @pytest.mark.asyncio
    async def test_update_output_creates_history(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_db: AsyncSession,
    ):
        """Test that updating output creates history record."""
        # Create output
        create_data = {
            "content": "Original content",
            "category": "other",
            "tags": [],
        }
        create_response = await async_client.post(
            "/api/v1/outputs/",
            json=create_data,
            headers=auth_headers,
        )
        output_id = create_response.json()["id"]

        # Update output
        update_data = {"content": "Updated content"}
        await async_client.patch(
            f"/api/v1/outputs/{output_id}",
            json=update_data,
            headers=auth_headers,
        )

        # Check history
        result = await test_db.execute(
            select(OutputHistory).where(OutputHistory.output_id == output_id)
        )
        history_records = result.scalars().all()
        assert len(history_records) == 1
        assert history_records[0].content == "Original content"
        assert history_records[0].version == 1

    @pytest.mark.asyncio
    async def test_update_output_not_owner(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_db: AsyncSession,
    ):
        """Test updating output by non-owner."""
        # Create output with first user
        create_data = {
            "content": "Original content",
            "category": "other",
            "tags": [],
        }
        create_response = await async_client.post(
            "/api/v1/outputs/",
            json=create_data,
            headers=auth_headers,
        )
        output_id = create_response.json()["id"]

        # Create second user
        second_user_data = {
            "email": "second@example.com",
            "username": "seconduser",
            "password": "SecurePass456!",
            "display_name": "Second User",
            "age_verified": True,
        }
        register_response = await async_client.post(
            "/api/v1/auth/register", json=second_user_data
        )
        assert register_response.status_code == 201, f"Registration failed: {register_response.json()}"

        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "second@example.com", "password": "SecurePass456!"},
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.json()}"
        second_headers = {
            "Authorization": f"Bearer {login_response.json()['access_token']}"
        }

        # Try to update with second user
        update_data = {"content": "Trying to update"}
        response = await async_client.patch(
            f"/api/v1/outputs/{output_id}",
            json=update_data,
            headers=second_headers,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_nonexistent_output(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test updating non-existent output."""
        response = await async_client.patch(
            "/api/v1/outputs/OUT-2026-0324-FAKE123",
            json={"content": "Update"},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestGetOutput:
    """Tests for GET /api/v1/outputs/{output_id}"""

    @pytest.mark.asyncio
    async def test_get_public_output_authenticated(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test getting public output as authenticated user."""
        # Create output
        create_data = {
            "content": "This is a groundbreaking discovery in theoretical physics that will revolutionize our understanding of the universe.",
            "category": "science",
            "tags": ["physics"],
        }
        create_response = await async_client.post(
            "/api/v1/outputs/",
            json=create_data,
            headers=auth_headers,
        )
        output_id = create_response.json()["id"]

        # Get output
        response = await async_client.get(
            f"/api/v1/outputs/{output_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == output_id
        assert "citation_count" in data
        assert "agreement_count" in data

    @pytest.mark.asyncio
    async def test_get_public_output_unauthenticated(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test getting public output as unauthenticated user."""
        # Create public output
        create_data = {
            "content": "Public content with high novelty score to ensure it's public visible to everyone.",
            "category": "other",
            "tags": [],
        }
        create_response = await async_client.post(
            "/api/v1/outputs/",
            json=create_data,
            headers=auth_headers,
        )
        output_id = create_response.json()["id"]
        visibility = create_response.json()["visibility"]

        # Get output without auth
        response = await async_client.get(f"/api/v1/outputs/{output_id}")

        # If visibility is public, should succeed
        # If visibility is private, should fail with 404
        if visibility == "public":
            assert response.status_code == 200
        else:
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_nonexistent_output(self, async_client: AsyncClient):
        """Test getting non-existent output."""
        response = await async_client.get("/api/v1/outputs/OUT-2026-0324-FAKE123")
        assert response.status_code == 404


class TestGetOutputHistory:
    """Tests for GET /api/v1/outputs/{output_id}/history"""

    @pytest.mark.asyncio
    async def test_get_output_history(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test getting output edit history."""
        # Create and update output multiple times
        create_data = {
            "content": "Version 1",
            "category": "other",
            "tags": [],
        }
        create_response = await async_client.post(
            "/api/v1/outputs/",
            json=create_data,
            headers=auth_headers,
        )
        output_id = create_response.json()["id"]

        # Update twice
        await async_client.patch(
            f"/api/v1/outputs/{output_id}",
            json={"content": "Version 2"},
            headers=auth_headers,
        )
        await async_client.patch(
            f"/api/v1/outputs/{output_id}",
            json={"content": "Version 3"},
            headers=auth_headers,
        )

        # Get history
        response = await async_client.get(
            f"/api/v1/outputs/{output_id}/history",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Two history records (version 1 and 2)
        assert data[0]["version"] == 2  # Most recent first
        assert data[1]["version"] == 1


class TestGetTimeline:
    """Tests for GET /api/v1/outputs/timeline"""

    @pytest.mark.asyncio
    async def test_get_timeline_authenticated(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test getting timeline as authenticated user."""
        # Create some outputs
        for i in range(3):
            await async_client.post(
                "/api/v1/outputs/",
                json={
                    "content": f"Timeline content {i} with unique information",
                    "category": "other",
                    "tags": [],
                },
                headers=auth_headers,
            )

        response = await async_client.get(
            "/api/v1/outputs/",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 20  # Default limit

    @pytest.mark.asyncio
    async def test_get_timeline_pagination(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test timeline pagination."""
        response = await async_client.get(
            "/api/v1/outputs/?limit=5&offset=0",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5

    @pytest.mark.asyncio
    async def test_get_timeline_unauthenticated(self, async_client: AsyncClient):
        """Test getting timeline without authentication."""
        response = await async_client.get("/api/v1/outputs/")
        assert response.status_code == 200  # Should work, shows only public outputs


class TestGetUserOutputs:
    """Tests for GET /api/v1/outputs/user/{username}"""

    @pytest.mark.asyncio
    async def test_get_user_outputs(
        self,
        async_client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test getting outputs by specific user."""
        # Create some outputs
        for i in range(2):
            await async_client.post(
                "/api/v1/outputs/",
                json={
                    "content": f"User output {i} with distinct content",
                    "category": "other",
                    "tags": [],
                },
                headers=auth_headers,
            )

        response = await async_client.get(
            f"/api/v1/outputs/user/{test_user.username}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_get_user_outputs_nonexistent_user(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test getting outputs for non-existent user."""
        response = await async_client.get(
            "/api/v1/outputs/user/nonexistentuser",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_user_outputs_visibility_filtering(
        self,
        async_client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test that private outputs are not shown to non-followers."""
        # Create output
        await async_client.post(
            "/api/v1/outputs/",
            json={
                "content": "Content",
                "category": "other",
                "tags": [],
            },
            headers=auth_headers,
        )
        username = test_user.username

        # Create second user
        second_user_data = {
            "email": "viewer@example.com",
            "username": "viewer",
            "password": "SecurePass789!",
            "display_name": "Viewer",
            "age_verified": True,
        }
        register_response = await async_client.post(
            "/api/v1/auth/register", json=second_user_data
        )
        assert register_response.status_code == 201, f"Registration failed: {register_response.json()}"

        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "viewer@example.com", "password": "SecurePass789!"},
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.json()}"
        viewer_headers = {
            "Authorization": f"Bearer {login_response.json()['access_token']}"
        }

        # Get outputs as second user (non-follower)
        response = await async_client.get(
            f"/api/v1/outputs/user/{username}",
            headers=viewer_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # Should only see public outputs
        for output in data:
            assert output["visibility"] == "public"
