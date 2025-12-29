"""
Tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "memoir-cloud-api"


def test_get_years_empty(client, mocker):
    """Test get years when no containers exist."""
    # Mock blob service to return empty list
    mocker.patch(
        "app.services.blob_service.blob_service.get_available_years",
        return_value=[]
    )
    
    response = client.get("/api/years")
    assert response.status_code == 200
    data = response.json()
    assert data["years"] == []
    assert data["default"] is None


def test_telemetry_endpoint(client):
    """Test telemetry endpoint accepts events."""
    response = client.post(
        "/api/telemetry",
        json={
            "event": "page_view",
            "sessionId": "test-session-123",
            "timestamp": "2025-12-28T10:00:00Z"
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "recorded"


def test_telemetry_photo_view(client):
    """Test telemetry endpoint for photo view events."""
    response = client.post(
        "/api/telemetry",
        json={
            "event": "photo_view",
            "photoId": "test-photo-uuid",
            "sessionId": "test-session-123",
            "timestamp": "2025-12-28T10:00:00Z"
        }
    )
    assert response.status_code == 200
