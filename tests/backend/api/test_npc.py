"""
Tests for the NPC Information API.
"""

import pytest
from fastapi.testclient import TestClient

from src.api import create_app
from src.data.npc import _npcs, _npc_configs, _interaction_states


@pytest.fixture
def client():
    """Create a test client for the API."""
    app = create_app()
    return TestClient(app)


def test_get_npc_information(client):
    """Test getting NPC information."""
    # Get a valid NPC ID from the mock data
    npc_id = next(iter(_npcs.keys()))
    
    # Send a GET request to get NPC information
    response = client.get(f"/api/npc/{npc_id}")
    
    # Check that the response is successful
    assert response.status_code == 200
    
    # Check that the response contains the expected fields
    data = response.json()
    assert data["npcId"] == npc_id
    assert "name" in data
    assert "role" in data
    assert "location" in data
    assert "availableDialogueTopics" in data
    assert "visualAppearance" in data
    assert "status" in data


def test_get_npc_information_not_found(client):
    """Test getting information for a non-existent NPC."""
    # Send a GET request to get information for a non-existent NPC
    response = client.get("/api/npc/nonexistent")
    
    # Check that the response is not found
    assert response.status_code == 404
    
    # Check that the response contains an error message
    data = response.json()
    assert "error" in data
    assert "message" in data
    assert "not found" in data["message"].lower()


def test_get_npc_configuration(client):
    """Test getting NPC configuration."""
    # Get a valid NPC ID from the mock data
    npc_id = next(iter(_npc_configs.keys()))
    
    # Send a GET request to get NPC configuration
    response = client.get(f"/api/npc/config/{npc_id}")
    
    # Check that the response is successful
    assert response.status_code == 200
    
    # Check that the response contains the expected fields
    data = response.json()
    assert data["npcId"] == npc_id
    assert "profile" in data
    assert "languageProfile" in data
    assert "promptTemplates" in data
    assert "conversationParameters" in data


def test_get_npc_configuration_not_found(client):
    """Test getting configuration for a non-existent NPC."""
    # Send a GET request to get configuration for a non-existent NPC
    response = client.get("/api/npc/config/nonexistent")
    
    # Check that the response is not found
    assert response.status_code == 404
    
    # Check that the response contains an error message
    data = response.json()
    assert "error" in data
    assert "message" in data
    assert "not found" in data["message"].lower()


def test_get_npc_interaction_state(client):
    """Test getting NPC interaction state."""
    # Get a valid player ID and NPC ID from the mock data
    player_id = next(iter(_interaction_states.keys()))
    npc_id = next(iter(_interaction_states[player_id].keys()))
    
    # Send a GET request to get NPC interaction state
    response = client.get(f"/api/npc/state/{player_id}/{npc_id}")
    
    # Check that the response is successful
    assert response.status_code == 200
    
    # Check that the response contains the expected fields
    data = response.json()
    assert data["playerId"] == player_id
    assert data["npcId"] == npc_id
    assert "relationshipMetrics" in data
    assert "conversationState" in data
    assert "gameProgressUnlocks" in data


def test_get_npc_interaction_state_player_not_found(client):
    """Test getting interaction state for a non-existent player."""
    # Get a valid NPC ID from the mock data
    npc_id = next(iter(_npc_configs.keys()))
    
    # Send a GET request to get interaction state for a non-existent player
    response = client.get(f"/api/npc/state/nonexistent/{npc_id}")
    
    # Check that the response is not found
    assert response.status_code == 404
    
    # Check that the response contains an error message
    data = response.json()
    assert "error" in data
    assert "message" in data
    assert "not found" in data["message"].lower()


def test_get_npc_interaction_state_npc_not_found(client):
    """Test getting interaction state for a non-existent NPC."""
    # Get a valid player ID from the mock data
    player_id = next(iter(_interaction_states.keys()))
    
    # Send a GET request to get interaction state for a non-existent NPC
    response = client.get(f"/api/npc/state/{player_id}/nonexistent")
    
    # Check that the response is not found
    assert response.status_code == 404
    
    # Check that the response contains an error message
    data = response.json()
    assert "error" in data
    assert "message" in data
    # Check that the message contains information about the interaction state not being found
    assert "interaction state" in data["message"].lower()


def test_update_npc_configuration(client):
    """Test updating NPC configuration."""
    # Get a valid NPC ID from the mock data
    npc_id = next(iter(_npc_configs.keys()))
    
    # Get the current configuration
    original_config = _npc_configs[npc_id].copy()
    
    # Create an updated configuration
    updated_config = {
        "profile": {
            "name": "Updated Name",
            "role": "Updated Role",
            "location": "Updated Location",
            "personality": ["friendly", "helpful", "patient"],
            "expertise": ["tickets", "train schedules", "local attractions"],
            "limitations": ["technical train details", "international travel"]
        },
        "languageProfile": {
            "defaultLanguage": "Japanese",
            "japaneseLevel": "N3",
            "speechPatterns": ["polite", "formal"],
            "commonPhrases": ["いらっしゃいませ", "ありがとうございます"],
            "vocabularyFocus": ["train station", "travel", "directions"]
        },
        "promptTemplates": {
            "initialGreeting": "こんにちは、いらっしゃいませ！",
            "responseFormat": "Simple and clear responses with Japanese terms highlighted",
            "errorHandling": "すみません、わかりません。",
            "conversationClose": "良い旅を！"
        },
        "conversationParameters": {
            "maxTurns": 10,
            "temperatureDefault": 0.7,
            "contextWindowSize": 5
        }
    }
    
    # Send a PUT request to update the NPC configuration
    response = client.put(f"/api/npc/config/{npc_id}", json=updated_config)
    
    # Check that the response is successful
    assert response.status_code == 200
    
    # Check that the response contains the updated configuration
    data = response.json()
    assert data["npcId"] == npc_id
    assert data["profile"]["name"] == "Updated Name"
    assert data["profile"]["role"] == "Updated Role"
    assert data["languageProfile"]["japaneseLevel"] == "N3"
    assert "いらっしゃいませ" in data["promptTemplates"]["initialGreeting"]
    assert data["conversationParameters"]["maxTurns"] == 10
    
    # Verify that the configuration was actually updated in the data store
    assert _npc_configs[npc_id]["profile"]["name"] == "Updated Name"
    assert _npc_configs[npc_id]["profile"]["role"] == "Updated Role"
    
    # Restore the original configuration for other tests
    _npc_configs[npc_id] = original_config


def test_update_npc_configuration_not_found(client):
    """Test updating configuration for a non-existent NPC."""
    # Create a configuration update
    updated_config = {
        "profile": {
            "name": "Updated Name",
            "role": "Updated Role",
            "location": "Updated Location",
            "personality": ["friendly", "helpful"],
            "expertise": ["tickets", "schedules"],
            "limitations": ["technical details"]
        },
        "languageProfile": {
            "defaultLanguage": "Japanese",
            "japaneseLevel": "N3",
            "speechPatterns": ["polite"],
            "commonPhrases": ["いらっしゃいませ"],
            "vocabularyFocus": ["train station"]
        },
        "promptTemplates": {
            "initialGreeting": "こんにちは",
            "responseFormat": "Simple responses",
            "errorHandling": "すみません",
            "conversationClose": "良い旅を"
        },
        "conversationParameters": {
            "maxTurns": 10,
            "temperatureDefault": 0.7,
            "contextWindowSize": 5
        }
    }
    
    # Send a PUT request to update a non-existent NPC configuration
    response = client.put("/api/npc/config/nonexistent", json=updated_config)
    
    # Check that the response is not found
    assert response.status_code == 404
    
    # Check that the response contains an error message
    data = response.json()
    assert "error" in data
    assert "message" in data
    assert "not found" in data["message"].lower()


def test_update_npc_configuration_invalid_data(client):
    """Test updating NPC configuration with invalid data."""
    # Get a valid NPC ID from the mock data
    npc_id = next(iter(_npc_configs.keys()))
    
    # Create an invalid configuration update (missing required fields)
    invalid_config = {
        "profile": {
            "name": "Updated Name"
            # Missing required fields
        }
    }
    
    # Send a PUT request with invalid data
    response = client.put(f"/api/npc/config/{npc_id}", json=invalid_config)
    
    # Check that the response is a validation error
    assert response.status_code == 422
    
    # Check that the response contains validation error details
    data = response.json()
    assert "error" in data
    assert "message" in data
    assert "details" in data
    assert "fieldErrors" in data["details"] 