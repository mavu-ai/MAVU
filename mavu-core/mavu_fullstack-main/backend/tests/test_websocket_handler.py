"""Test WebSocket handler functionality."""
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert data["version"] == "1.0.0"


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_websocket_connection(client):
    """Test WebSocket connection endpoint."""
    with client.websocket_connect("/realtime?user_id=test_user") as websocket:
        # Should receive a session ready message
        data = websocket.receive_json()
        assert data is not None
        # WebSocket should be connected
        assert websocket is not None
