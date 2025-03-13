"""
Tests for the NPC Information API.
"""

import pytest
from fastapi.testclient import TestClient

from backend.api import create_app
from backend.data.npc import _npcs, _npc_configs, _interaction_states


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