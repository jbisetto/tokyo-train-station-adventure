"""
Tests for the dialogue process endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from backend.api import create_app

app = create_app()
client = TestClient(app)


def test_dialogue_process_endpoint_exists():
    """Test that the dialogue process endpoint exists."""
    response = client.post(
        "/api/dialogue/process",
        json={
            "playerId": "test-player",
            "sessionId": "test-session",
            "speakerId": "station-attendant",
            "speakerType": "npc",
            "dialogueInput": {
                "text": "Hello",
                "language": "english",
                "inputType": "text"
            },
            "gameContext": {
                "location": "tokyo_station"
            }
        }
    )
    assert response.status_code != 404, "Dialogue process endpoint should exist"


def test_dialogue_process_request_validation():
    """Test that the dialogue process endpoint validates requests."""
    # Missing required fields
    response = client.post(
        "/api/dialogue/process",
        json={}
    )
    assert response.status_code == 422, "Should return 422 for missing required fields"

    # Invalid speakerId
    response = client.post(
        "/api/dialogue/process",
        json={
            "playerId": "test-player",
            "sessionId": "test-session",
            "speakerId": "",  # Empty speaker ID
            "speakerType": "npc",
            "dialogueInput": {
                "text": "Hello",
                "language": "english",
                "inputType": "text"
            },
            "gameContext": {
                "location": "tokyo_station"
            }
        }
    )
    assert response.status_code == 422, "Should return 422 for invalid speaker ID"

    # Invalid dialogueInput
    response = client.post(
        "/api/dialogue/process",
        json={
            "playerId": "test-player",
            "sessionId": "test-session",
            "speakerId": "station-attendant",
            "speakerType": "npc",
            "dialogueInput": {
                "text": "",  # Empty text
                "language": "english",
                "inputType": "text"
            },
            "gameContext": {
                "location": "tokyo_station"
            }
        }
    )
    assert response.status_code == 422, "Should return 422 for empty dialogue text"

    # Invalid language
    response = client.post(
        "/api/dialogue/process",
        json={
            "playerId": "test-player",
            "sessionId": "test-session",
            "speakerId": "station-attendant",
            "speakerType": "npc",
            "dialogueInput": {
                "text": "Hello",
                "language": "french",  # Invalid language
                "inputType": "text"
            },
            "gameContext": {
                "location": "tokyo_station"
            }
        }
    )
    assert response.status_code == 422, "Should return 422 for invalid language"


def test_dialogue_process_successful_request():
    """Test that the dialogue process endpoint returns a successful response."""
    response = client.post(
        "/api/dialogue/process",
        json={
            "playerId": "test-player",
            "sessionId": "test-session",
            "speakerId": "station-attendant",
            "speakerType": "npc",
            "dialogueInput": {
                "text": "How do I buy a ticket?",
                "language": "english",
                "inputType": "text"
            },
            "gameContext": {
                "location": "tokyo_station"
            }
        }
    )
    # Print response content for debugging
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content.decode()}")
    
    assert response.status_code == 200, "Should return 200 for a valid request"
    
    # Check response structure
    data = response.json()
    assert "dialogueContent" in data, "Response should include dialogueContent"
    assert "responseText" in data["dialogueContent"], "dialogueContent should include responseText"
    
    assert "uiElements" in data, "Response should include uiElements"
    assert "gameStateUpdates" in data, "Response should include gameStateUpdates"
    assert "metadata" in data, "Response should include metadata" 