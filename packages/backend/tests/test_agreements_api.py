"""Tests for Agreement API endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import get_db, Base
from app.models.user import User
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


async def create_test_output(
    async_client: AsyncClient, auth_headers: dict[str, str], content: str
) -> str:
    """Helper function to create a test output."""
    response = await async_client.post(
        "/api/v1/outputs/",
        json={
            "content": content,
            "category": "science",
            "tags": [],
        },
        headers=auth_headers,
    )
    return response.json()["id"]


class TestAgreeToOutput:
    """Tests for POST /api/v1/agreements/"""

    @pytest.mark.asyncio
    async def test_agree_to_output_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test successful agreement creation."""
        # Create output
        output_id = await create_test_output(
            async_client, auth_headers, "Test output for agreement"
        )

        # Agree to output
        response = await async_client.post(
            f"/api/v1/agreements/?output_id={output_id}",
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["output_id"] == output_id
        assert "agreed_at" in data

    @pytest.mark.asyncio
    async def test_agree_to_output_duplicate(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test agreeing to same output twice returns existing agreement."""
        output_id = await create_test_output(
            async_client, auth_headers, "Test output"
        )

        # First agreement
        response1 = await async_client.post(
            f"/api/v1/agreements/?output_id={output_id}",
            headers=auth_headers,
        )
        assert response1.status_code == 201

        # Second agreement (duplicate)
        response2 = await async_client.post(
            f"/api/v1/agreements/?output_id={output_id}",
            headers=auth_headers,
        )
        assert response2.status_code == 201  # Returns existing agreement

    @pytest.mark.asyncio
    async def test_agree_to_nonexistent_output(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test agreeing to non-existent output."""
        response = await async_client.post(
            "/api/v1/agreements/?output_id=OUT-2026-0324-FAKE123",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_agree_without_auth(self, async_client: AsyncClient):
        """Test agreeing without authentication."""
        response = await async_client.post(
            "/api/v1/agreements/?output_id=OUT-2026-0324-TEST123"
        )
        assert response.status_code == 403


class TestRemoveAgreement:
    """Tests for DELETE /api/v1/agreements/{output_id}"""

    @pytest.mark.asyncio
    async def test_remove_agreement_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test successful agreement removal."""
        # Create output and agree
        output_id = await create_test_output(
            async_client, auth_headers, "Test output"
        )
        await async_client.post(
            f"/api/v1/agreements/?output_id={output_id}",
            headers=auth_headers,
        )

        # Remove agreement
        response = await async_client.delete(
            f"/api/v1/agreements/{output_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_remove_nonexistent_agreement(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test removing agreement that doesn't exist."""
        # Create output but don't agree
        output_id = await create_test_output(
            async_client, auth_headers, "Test output"
        )

        response = await async_client.delete(
            f"/api/v1/agreements/{output_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestGetUsersWhoAgreed:
    """Tests for GET /api/v1/agreements/output/{output_id}"""

    @pytest.mark.asyncio
    async def test_get_users_who_agreed(
        self,
        async_client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test getting users who agreed with an output."""
        # Create output
        output_id = await create_test_output(
            async_client, auth_headers, "Popular output"
        )

        # Current user agrees
        await async_client.post(
            f"/api/v1/agreements/?output_id={output_id}",
            headers=auth_headers,
        )

        # Create second user and agree
        second_user_data = {
            "email": "second@example.com",
            "username": "seconduser",
            "password": "SecurePass456!",
            "display_name": "Second User",
            "age_verified": True,
        }
        await async_client.post("/api/v1/auth/register", json=second_user_data)
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "second@example.com", "password": "SecurePass456!"},
        )
        second_headers = {
            "Authorization": f"Bearer {login_response.json()['access_token']}"
        }

        await async_client.post(
            f"/api/v1/agreements/?output_id={output_id}",
            headers=second_headers,
        )

        # Get users who agreed
        response = await async_client.get(
            f"/api/v1/agreements/output/{output_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("username" in user for user in data)
        assert all("agreed_at" in user for user in data)

    @pytest.mark.asyncio
    async def test_get_users_who_agreed_empty(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test getting users when no one agreed."""
        output_id = await create_test_output(
            async_client, auth_headers, "Unpopular output"
        )

        response = await async_client.get(
            f"/api/v1/agreements/output/{output_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestGetUserAgreedOutputs:
    """Tests for GET /api/v1/agreements/user/{username}"""

    @pytest.mark.asyncio
    async def test_get_user_agreed_outputs(
        self,
        async_client: AsyncClient,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test getting outputs a user agreed with."""
        # Create outputs and agree with them
        output1_id = await create_test_output(
            async_client, auth_headers, "Output 1"
        )
        output2_id = await create_test_output(
            async_client, auth_headers, "Output 2"
        )

        await async_client.post(
            f"/api/v1/agreements/?output_id={output1_id}",
            headers=auth_headers,
        )
        await async_client.post(
            f"/api/v1/agreements/?output_id={output2_id}",
            headers=auth_headers,
        )

        # Get agreed outputs
        response = await async_client.get(
            f"/api/v1/agreements/user/{test_user.username}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_user_agreed_outputs_nonexistent_user(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test getting agreed outputs for non-existent user."""
        response = await async_client.get(
            "/api/v1/agreements/user/nonexistentuser",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestGetAgreementCount:
    """Tests for GET /api/v1/agreements/output/{output_id}/count"""

    @pytest.mark.asyncio
    async def test_get_agreement_count(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test getting agreement count for an output."""
        # Create output
        output_id = await create_test_output(
            async_client, auth_headers, "Test output"
        )

        # Agree
        await async_client.post(
            f"/api/v1/agreements/?output_id={output_id}",
            headers=auth_headers,
        )

        # Get count
        response = await async_client.get(
            f"/api/v1/agreements/output/{output_id}/count"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["output_id"] == output_id
        assert data["agreement_count"] == 1

    @pytest.mark.asyncio
    async def test_get_agreement_count_zero(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test getting agreement count when zero."""
        output_id = await create_test_output(
            async_client, auth_headers, "Test output"
        )

        response = await async_client.get(
            f"/api/v1/agreements/output/{output_id}/count"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["agreement_count"] == 0


class TestCheckUserAgreement:
    """Tests for GET /api/v1/agreements/check/{output_id}"""

    @pytest.mark.asyncio
    async def test_check_user_has_agreed(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test checking if user has agreed."""
        output_id = await create_test_output(
            async_client, auth_headers, "Test output"
        )

        # Agree
        await async_client.post(
            f"/api/v1/agreements/?output_id={output_id}",
            headers=auth_headers,
        )

        # Check
        response = await async_client.get(
            f"/api/v1/agreements/check/{output_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_agreed"] is True
        assert data["output_id"] == output_id
        assert "agreed_at" in data

    @pytest.mark.asyncio
    async def test_check_user_has_not_agreed(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test checking if user has not agreed."""
        output_id = await create_test_output(
            async_client, auth_headers, "Test output"
        )

        # Check without agreeing
        response = await async_client.get(
            f"/api/v1/agreements/check/{output_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_agreed"] is False
        assert data["output_id"] == output_id
        assert data["agreed_at"] is None
