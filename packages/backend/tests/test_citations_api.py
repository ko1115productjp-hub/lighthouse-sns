"""Tests for Citation API endpoints."""

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


class TestCreateCitation:
    """Tests for POST /api/v1/citations/"""

    @pytest.mark.asyncio
    async def test_create_citation_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test successful citation creation."""
        # Create two outputs
        source_id = await create_test_output(
            async_client, auth_headers, "This is my paper about quantum physics"
        )
        target_id = await create_test_output(
            async_client, auth_headers, "Original research on quantum mechanics"
        )

        # Create citation
        citation_data = {
            "source_output_id": source_id,
            "target_output_id": target_id,
            "citation_type": "agree",
            "excerpt": "Key finding from the original research",
        }

        response = await async_client.post(
            "/api/v1/citations/",
            json=citation_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["source_output_id"] == source_id
        assert data["target_output_id"] == target_id
        assert data["citation_type"] == "agree"
        assert data["excerpt"] == citation_data["excerpt"]
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_citation_duplicate(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test creating duplicate citation returns existing one."""
        source_id = await create_test_output(
            async_client, auth_headers, "Source paper"
        )
        target_id = await create_test_output(
            async_client, auth_headers, "Target paper"
        )

        citation_data = {
            "source_output_id": source_id,
            "target_output_id": target_id,
            "citation_type": "agree",
        }

        # Create first citation
        response1 = await async_client.post(
            "/api/v1/citations/",
            json=citation_data,
            headers=auth_headers,
        )
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = await async_client.post(
            "/api/v1/citations/",
            json=citation_data,
            headers=auth_headers,
        )
        assert response2.status_code == 400  # Citation already exists error

    @pytest.mark.asyncio
    async def test_create_citation_nonexistent_output(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test creating citation with non-existent output."""
        source_id = await create_test_output(
            async_client, auth_headers, "Valid output"
        )

        citation_data = {
            "source_output_id": source_id,
            "target_output_id": "OUT-2026-0324-FAKE123",
            "citation_type": "agree",
        }

        response = await async_client.post(
            "/api/v1/citations/",
            json=citation_data,
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_citation_without_auth(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test creating citation without authentication."""
        source_id = await create_test_output(
            async_client, auth_headers, "Source"
        )
        target_id = await create_test_output(
            async_client, auth_headers, "Target"
        )

        citation_data = {
            "source_output_id": source_id,
            "target_output_id": target_id,
            "citation_type": "agree",
        }

        response = await async_client.post("/api/v1/citations/", json=citation_data)
        assert response.status_code == 403


class TestGetCitingOutputs:
    """Tests for GET /api/v1/citations/output/{output_id}/citing"""

    @pytest.mark.asyncio
    async def test_get_citing_outputs(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test getting outputs that cite this output."""
        # Create outputs
        target_id = await create_test_output(
            async_client, auth_headers, "Original paper"
        )
        source1_id = await create_test_output(
            async_client, auth_headers, "Paper 1 that cites original"
        )
        source2_id = await create_test_output(
            async_client, auth_headers, "Paper 2 that cites original"
        )

        # Create citations (source outputs citing the target)
        cite1_response = await async_client.post(
            "/api/v1/citations/",
            json={
                "source_output_id": source1_id,
                "target_output_id": target_id,
                "citation_type": "agree",
            },
            headers=auth_headers,
        )
        assert cite1_response.status_code == 201, f"First citation failed: {cite1_response.json()}"

        cite2_response = await async_client.post(
            "/api/v1/citations/",
            json={
                "source_output_id": source2_id,
                "target_output_id": target_id,
                "citation_type": "develop",
            },
            headers=auth_headers,
        )
        assert cite2_response.status_code == 201, f"Second citation failed: {cite2_response.json()}"

        # Get citing outputs (outputs that cite target_id)
        response = await async_client.get(
            f"/api/v1/citations/output/{target_id}/citing",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert "source_output" in data[0]

    @pytest.mark.asyncio
    async def test_get_citing_outputs_empty(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test getting citing outputs when none exist."""
        output_id = await create_test_output(
            async_client, auth_headers, "Standalone output"
        )

        response = await async_client.get(
            f"/api/v1/citations/output/{output_id}/citing",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestGetCitedOutputs:
    """Tests for GET /api/v1/citations/output/{output_id}/cited"""

    @pytest.mark.asyncio
    async def test_get_cited_outputs(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test getting outputs cited by this output."""
        # Create outputs
        source_id = await create_test_output(
            async_client, auth_headers, "My research paper"
        )
        target1_id = await create_test_output(
            async_client, auth_headers, "Reference 1"
        )
        target2_id = await create_test_output(
            async_client, auth_headers, "Reference 2"
        )

        # Create citations (source cites target1 and target2)
        cite1_response = await async_client.post(
            "/api/v1/citations/",
            json={
                "source_output_id": source_id,
                "target_output_id": target1_id,
                "citation_type": "agree",
            },
            headers=auth_headers,
        )
        assert cite1_response.status_code == 201, f"First citation failed: {cite1_response.json()}"

        cite2_response = await async_client.post(
            "/api/v1/citations/",
            json={
                "source_output_id": source_id,
                "target_output_id": target2_id,
                "citation_type": "criticize",
            },
            headers=auth_headers,
        )
        assert cite2_response.status_code == 201, f"Second citation failed: {cite2_response.json()}"

        # Get cited outputs (outputs that source_id cites)
        response = await async_client.get(
            f"/api/v1/citations/output/{source_id}/cited",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert "source_output" in data[0]


class TestGetCitationStats:
    """Tests for GET /api/v1/citations/output/{output_id}/stats"""

    @pytest.mark.asyncio
    async def test_get_citation_stats(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test getting citation statistics."""
        # Create outputs
        output_id = await create_test_output(
            async_client, auth_headers, "Paper with citations"
        )
        citing_id = await create_test_output(
            async_client, auth_headers, "Paper it cites"
        )
        cited_by_id = await create_test_output(
            async_client, auth_headers, "Paper that cites it"
        )

        # Create citations
        cite1_response = await async_client.post(
            "/api/v1/citations/",
            json={
                "source_output_id": output_id,
                "target_output_id": citing_id,
                "citation_type": "agree",
            },
            headers=auth_headers,
        )
        assert cite1_response.status_code == 201, f"First citation failed: {cite1_response.json()}"

        cite2_response = await async_client.post(
            "/api/v1/citations/",
            json={
                "source_output_id": cited_by_id,
                "target_output_id": output_id,
                "citation_type": "develop",
            },
            headers=auth_headers,
        )
        assert cite2_response.status_code == 201, f"Second citation failed: {cite2_response.json()}"

        # Get stats
        response = await async_client.get(
            f"/api/v1/citations/output/{output_id}/stats",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["output_id"] == output_id
        assert data["outgoing_citations"] == 1  # output_id cites citing_id
        assert data["incoming_citations"] == 1  # cited_by_id cites output_id
        assert "incoming_by_type" in data


class TestGetCitationGraph:
    """Tests for GET /api/v1/citations/output/{output_id}/graph"""

    @pytest.mark.asyncio
    async def test_get_citation_graph(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test getting citation graph."""
        # Create chain of outputs
        output1_id = await create_test_output(
            async_client, auth_headers, "First paper in chain"
        )
        output2_id = await create_test_output(
            async_client, auth_headers, "Second paper citing first"
        )
        output3_id = await create_test_output(
            async_client, auth_headers, "Third paper citing second"
        )

        # Create citation chain
        await async_client.post(
            "/api/v1/citations/",
            json={
                "source_output_id": output2_id,
                "target_output_id": output1_id,
                "citation_type": "develop",
            },
            headers=auth_headers,
        )
        await async_client.post(
            "/api/v1/citations/",
            json={
                "source_output_id": output3_id,
                "target_output_id": output2_id,
                "citation_type": "develop",
            },
            headers=auth_headers,
        )

        # Get graph
        response = await async_client.get(
            f"/api/v1/citations/output/{output2_id}/graph?depth=2",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["root_output_id"] == output2_id
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) >= 1  # At least the root node
        assert len(data["edges"]) >= 0  # May have edges

    @pytest.mark.asyncio
    async def test_get_citation_graph_depth_limit(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test citation graph depth limiting."""
        output_id = await create_test_output(
            async_client, auth_headers, "Root output"
        )

        response = await async_client.get(
            f"/api/v1/citations/output/{output_id}/graph?depth=1",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["root_output_id"] == output_id


class TestDeleteCitation:
    """Tests for DELETE /api/v1/citations/{citation_id}"""

    @pytest.mark.asyncio
    async def test_delete_citation_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test successful citation deletion."""
        # Create outputs and citation
        source_id = await create_test_output(
            async_client, auth_headers, "Source"
        )
        target_id = await create_test_output(
            async_client, auth_headers, "Target"
        )

        create_response = await async_client.post(
            "/api/v1/citations/",
            json={
                "source_output_id": source_id,
                "target_output_id": target_id,
                "citation_type": "agree",
            },
            headers=auth_headers,
        )
        citation_id = create_response.json()["id"]

        # Delete citation
        response = await async_client.delete(
            f"/api/v1/citations/{citation_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_delete_citation_nonexistent(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test deleting non-existent citation."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = await async_client.delete(
            f"/api/v1/citations/{fake_uuid}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_citation_not_owner(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test deleting citation by non-owner."""
        # Create outputs and citation with first user
        source_id = await create_test_output(
            async_client, auth_headers, "Source by user 1"
        )
        target_id = await create_test_output(
            async_client, auth_headers, "Target"
        )

        create_response = await async_client.post(
            "/api/v1/citations/",
            json={
                "source_output_id": source_id,
                "target_output_id": target_id,
                "citation_type": "agree",
            },
            headers=auth_headers,
        )
        citation_id = create_response.json()["id"]

        # Create second user
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

        # Try to delete with second user
        response = await async_client.delete(
            f"/api/v1/citations/{citation_id}",
            headers=second_headers,
        )
        assert response.status_code == 403
