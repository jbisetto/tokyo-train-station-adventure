"""
Tests for the NPC Dialogue API.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from src.api import create_app


@pytest.fixture
def client():
    """Create a test client for the API."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def valid_dialogue_request():
    """Create a valid dialogue request for testing."""
    return {
        "playerContext": {
            "playerId": "player123",
            "sessionId": "session456",
            "languageLevel": "N5",
            "learningProgress": {
                "vocabularyMastered": 42,
                "grammarPoints": 11,
                "conversationSuccess": 0.82
            }
        },
        "gameContext": {
            "location": "ticket_machine_area",
            "currentQuest": "buy_ticket_to_odawara",
            "questStep": "find_ticket_machine",
            "interactionHistory": [
                {
                    "npcId": "info_attendant",
                    "completed": True
                }
            ],
            "timeOfDay": "morning",
            "gameFlags": {
                "tutorialCompleted": True
            }
        },
        "npcId": "ticket_operator",
        "playerInput": {
            "text": "小田原までの切符をください。",
            "inputType": "keyboard",
            "language": "japanese",
            "selectedOptionId": None
        },
        "conversationContext": {
            "conversationId": None,
            "previousExchanges": []
        }
    }


def test_npc_dialogue_endpoint_exists(client):
    """Test that the NPC dialogue endpoint exists."""
    response = client.post("/api/npc/dialogue", json={})
    # Even though the request is invalid, the endpoint should exist
    assert response.status_code != 404


def test_npc_dialogue_request_validation(client):
    """Test validation of NPC dialogue requests."""
    # Missing required fields
    response = client.post("/api/npc/dialogue", json={})
    assert response.status_code == 422
    
    # Missing playerContext
    invalid_request = {
        "gameContext": {"location": "ticket_machine_area"},
        "npcId": "ticket_operator",
        "playerInput": {
            "text": "Hello",
            "inputType": "keyboard",
            "language": "english"
        }
    }
    response = client.post("/api/npc/dialogue", json=invalid_request)
    assert response.status_code == 422
    
    # Missing npcId
    invalid_request = {
        "playerContext": {"playerId": "player123", "sessionId": "session456"},
        "gameContext": {"location": "ticket_machine_area"},
        "playerInput": {
            "text": "Hello",
            "inputType": "keyboard",
            "language": "english"
        }
    }
    response = client.post("/api/npc/dialogue", json=invalid_request)
    assert response.status_code == 422
    
    # Missing playerInput
    invalid_request = {
        "playerContext": {"playerId": "player123", "sessionId": "session456"},
        "gameContext": {"location": "ticket_machine_area"},
        "npcId": "ticket_operator"
    }
    response = client.post("/api/npc/dialogue", json=invalid_request)
    assert response.status_code == 422


def test_npc_dialogue_successful_request(client, valid_dialogue_request):
    """Test a successful NPC dialogue request."""
    response = client.post("/api/npc/dialogue", json=valid_dialogue_request)
    
    # Check that the response is successful
    assert response.status_code == 200
    
    # Check that the response contains the expected fields
    data = response.json()
    assert "conversationId" in data
    assert "npcResponse" in data
    assert "text" in data["npcResponse"]
    assert "japanese" in data["npcResponse"]
    assert "animation" in data["npcResponse"]
    assert "emotion" in data["npcResponse"]
    assert "feedback" in data["npcResponse"]
    assert "expectedInput" in data
    assert "type" in data["expectedInput"]
    assert "gameStateChanges" in data
    assert "meta" in data


def test_npc_dialogue_nonexistent_npc(client, valid_dialogue_request):
    """Test dialogue with a non-existent NPC."""
    # Modify the request to use a non-existent NPC
    valid_dialogue_request["npcId"] = "nonexistent_npc"
    
    response = client.post("/api/npc/dialogue", json=valid_dialogue_request)
    
    # Check that the response is not found
    assert response.status_code == 404
    
    # Check that the response contains an error message
    data = response.json()
    assert "error" in data
    assert "message" in data
    assert "NPC" in data["message"]
    assert "not found" in data["message"].lower()


def test_npc_dialogue_invalid_language(client, valid_dialogue_request):
    """Test dialogue with an invalid language."""
    # Modify the request to use an invalid language
    valid_dialogue_request["playerInput"]["language"] = "french"
    
    response = client.post("/api/npc/dialogue", json=valid_dialogue_request)
    
    # Check that the response is unprocessable entity
    assert response.status_code == 422
    
    # Check that the response contains an error message
    data = response.json()
    assert "error" in data
    assert "message" in data
    assert "language" in data["message"].lower()


def test_npc_dialogue_conversation_continuation(client, valid_dialogue_request):
    """Test continuation of a conversation with an NPC."""
    # First request to start a conversation
    response = client.post("/api/npc/dialogue", json=valid_dialogue_request)
    assert response.status_code == 200
    data = response.json()
    conversation_id = data["conversationId"]
    
    # Modify the request to continue the conversation
    valid_dialogue_request["conversationContext"]["conversationId"] = conversation_id
    valid_dialogue_request["conversationContext"]["previousExchanges"] = [
        {
            "speaker": "player",
            "text": valid_dialogue_request["playerInput"]["text"],
            "timestamp": datetime.now().isoformat()
        },
        {
            "speaker": "npc",
            "text": data["npcResponse"]["japanese"],
            "timestamp": datetime.now().isoformat()
        }
    ]
    valid_dialogue_request["playerInput"]["text"] = "片道です。"
    
    response = client.post("/api/npc/dialogue", json=valid_dialogue_request)
    
    # Check that the response is successful
    assert response.status_code == 200
    
    # Check that the response contains the expected fields
    data = response.json()
    assert data["conversationId"] == conversation_id  # Same conversation ID
    assert "npcResponse" in data
    assert "gameStateChanges" in data 