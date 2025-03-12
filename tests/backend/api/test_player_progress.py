"""
Tests for the player progress API endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from backend.api import create_app


@pytest.fixture
def client():
    """Create a test client for the API."""
    app = create_app()
    return TestClient(app)


def test_get_player_progress_success(client):
    """Test successful retrieval of player progress."""
    # Make a request to the endpoint
    response = client.get("/api/player/progress/player123")
    
    # Check the response status code
    assert response.status_code == 200
    
    # Check the response content
    data = response.json()
    assert data["player"]["id"] == "player123"
    assert data["player"]["level"] == "N5"
    
    # Check progress metrics
    assert "vocabulary" in data["progress"]
    assert "grammar" in data["progress"]
    assert "conversation" in data["progress"]
    
    # Check vocabulary progress
    assert "mastered" in data["vocabulary"]
    assert "learning" in data["vocabulary"]
    assert "forReview" in data["vocabulary"]
    
    # Check grammar progress
    assert "mastered" in data["grammarPoints"]
    assert "learning" in data["grammarPoints"]
    assert "forReview" in data["grammarPoints"]
    
    # Check visualization data
    assert "skillPentagon" in data["visualizationData"]
    assert "progressOverTime" in data["visualizationData"]


def test_get_player_progress_not_found(client):
    """Test player not found error."""
    # Make a request with a non-existent player ID
    response = client.get("/api/player/progress/nonexistent")
    
    # Check the response status code
    assert response.status_code == 404
    
    # Check the error message
    data = response.json()
    assert data["error"]["error"] == "Not Found"
    assert "Player with ID nonexistent not found" in data["error"]["message"]


def test_get_player_progress_invalid_id(client):
    """Test invalid player ID error."""
    # Make a request with an invalid player ID (too short)
    response = client.get("/api/player/progress/ab")
    
    # Check the response status code
    assert response.status_code == 400
    
    # Check the error message
    data = response.json()
    assert data["error"]["error"] == "Bad Request"
    assert "Invalid player ID format" in data["error"]["message"] 