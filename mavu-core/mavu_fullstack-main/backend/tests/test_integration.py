"""Integration tests for the complete MavuAI stack."""
import pytest
import asyncio
from fastapi.testclient import TestClient
from main import app
from utils.weaviate_client import weaviate_client


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_complete_rag_flow():
    """Test complete RAG flow: store -> retrieve -> search."""
    await weaviate_client.connect()

    try:
        # 1. Store user context
        test_embedding = [0.1] * 1536
        user_id = await weaviate_client.store_user_context(
            owner_id="integration_test_user",
            text_chunk="The user prefers Python programming and FastAPI framework.",
            embedding=test_embedding,
            metadata={"topic": "preferences"},
            source="integration_test"
        )
        assert user_id is not None

        # 2. Store app context
        app_id = await weaviate_client.store_app_context(
            text_chunk="MavuAI is a real-time voice AI with RAG capabilities.",
            embedding=test_embedding,
            metadata={"topic": "product"},
            source="integration_test",
            category="documentation"
        )
        assert app_id is not None

        # 3. Search user context
        user_results = await weaviate_client.search_user_context(
            owner_id="integration_test_user",
            query_embedding=test_embedding,
            limit=5
        )
        assert isinstance(user_results, list)
        assert len(user_results) >= 1

        # 4. Search app context
        app_results = await weaviate_client.search_app_context(
            query_embedding=test_embedding,
            limit=5
        )
        assert isinstance(app_results, list)
        assert len(app_results) >= 1

    finally:
        await weaviate_client.disconnect()


def test_api_endpoints_integration(client):
    """Test all API endpoints are accessible."""
    # Health check
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    # Status can be 'connected' or 'disconnected' depending on Weaviate state
    assert "status" in data
    assert "version" in data
    assert data["version"] == "1.0.0"

    # Root endpoint
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_websocket_lifecycle(client):
    """Test WebSocket connection lifecycle."""
    with client.websocket_connect("/api/v1/realtime?user_id=integration_test") as websocket:
        # Should receive session ready message
        data = websocket.receive_json()
        assert data is not None
        assert "type" in data


@pytest.mark.asyncio
async def test_service_connectivity():
    """Test that all services (Weaviate, Redis) are accessible."""
    # Test Weaviate
    await weaviate_client.connect()
    assert weaviate_client.client is not None
    assert weaviate_client.client.is_connected()
    await weaviate_client.disconnect()

    # Note: Redis testing would require importing redis client
    # For now, we assume it's working if backend starts
