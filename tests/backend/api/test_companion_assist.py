"""
Tests for the companion assist endpoint.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add the project root to the path so we can import the backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from src.main import app


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.
    """
    return TestClient(app)


def test_companion_assist_endpoint_exists(client):
    """
    Test that the companion assist endpoint exists.
    """
    # Using a simple request to check if the endpoint exists
    # This should return 422 (Unprocessable Entity) if the endpoint exists but validation fails
    # rather than 404 (Not Found) if the endpoint doesn't exist
    response = client.post("/api/companion/assist", json={})
    assert response.status_code != 404


def test_companion_assist_request_validation(client):
    """
    Test that the companion assist endpoint validates requests.
    """
    # Send an empty request, which should fail validation
    response = client.post("/api/companion/assist", json={})
    assert response.status_code == 422
    
    # Send a request with missing required fields
    response = client.post("/api/companion/assist", json={"playerId": "player123"})
    assert response.status_code == 422


def test_companion_assist_successful_request(client):
    """
    Test that the companion assist endpoint processes valid requests successfully.
    """
    # Create a valid request based on the API specification
    request_data = {
        "playerId": "player123",
        "sessionId": "session456",
        "gameContext": {
            "location": "ticket_machine_area",
            "currentQuest": "buy_ticket_to_odawara",
            "questStep": "find_ticket_machine",
            "nearbyEntities": ["ticket_machine_1", "station_map", "information_booth"],
            "lastInteraction": "station_map"
        },
        "request": {
            "type": "vocabulary",
            "text": "What does 切符 mean?",
            "targetEntity": "ticket_machine_1",
            "language": "english"
        }
    }
    
    response = client.post("/api/companion/assist", json=request_data)
    assert response.status_code == 200
    
    # Check that the response has the expected structure
    response_data = response.json()
    assert "dialogue" in response_data
    assert "text" in response_data["dialogue"]
    assert "companion" in response_data
    assert "ui" in response_data
    assert "gameState" in response_data
    assert "meta" in response_data 