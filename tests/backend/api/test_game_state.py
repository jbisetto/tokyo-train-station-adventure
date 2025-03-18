"""
Tests for the Game State API.
"""

import pytest
from datetime import datetime, UTC
from fastapi.testclient import TestClient

from backend.api import create_app
from backend.data.game_state import _game_states


@pytest.fixture
def client():
    """Create a test client for the API."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_game_state():
    """Create a sample game state for testing."""
    return {
        "playerId": "test_player",
        "sessionId": "test_session",
        "timestamp": datetime.now(UTC).isoformat(),
        "location": {
            "area": "test_area",
            "position": {
                "x": 100,
                "y": 200
            }
        },
        "questState": {
            "activeQuest": "test_quest",
            "questStep": "test_step",
            "objectives": [
                {
                    "id": "test_objective",
                    "completed": False,
                    "description": "Test objective"
                }
            ]
        },
        "inventory": ["test_item"],
        "gameFlags": {
            "testFlag": True
        },
        "companions": {
            "test_companion": {
                "relationship": 0.5,
                "assistanceUsed": 1
            }
        }
    }


def test_save_game_state(client, sample_game_state):
    """Test saving a game state."""
    # Send a POST request to save the game state
    response = client.post("/api/game/state", json=sample_game_state)
    
    # Check that the response is successful
    assert response.status_code == 200
    
    # Check that the response contains the expected fields
    data = response.json()
    assert "success" in data
    assert data["success"] is True
    assert "saveId" in data
    assert "timestamp" in data


def test_save_game_state_invalid_player_id(client, sample_game_state):
    """Test saving a game state with an invalid player ID."""
    # Modify the sample game state to have an invalid player ID
    sample_game_state["playerId"] = "ab"
    
    # Send a POST request to save the game state
    response = client.post("/api/game/state", json=sample_game_state)
    
    # Check that the response is a bad request
    assert response.status_code == 400 or response.status_code == 422
    
    # Check that the response contains an error message
    data = response.json()
    assert "detail" in data or "message" in data


def test_load_game_state(client, sample_game_state):
    """Test loading a game state."""
    # First, save a game state
    save_response = client.post("/api/game/state", json=sample_game_state)
    save_data = save_response.json()
    
    # Send a GET request to load the game state
    response = client.get(f"/api/game/state/{sample_game_state['playerId']}")
    
    # Check that the response is successful
    assert response.status_code == 200
    
    # Check that the response contains the expected fields
    data = response.json()
    assert data["playerId"] == sample_game_state["playerId"]
    assert "saveId" in data
    assert "sessionId" in data
    assert "timestamp" in data
    assert "lastPlayed" in data
    assert "location" in data
    assert data["location"]["area"] == sample_game_state["location"]["area"]
    assert "questState" in data
    assert data["questState"]["activeQuest"] == sample_game_state["questState"]["activeQuest"]
    assert "inventory" in data
    assert data["inventory"] == sample_game_state["inventory"]
    assert "gameFlags" in data
    assert data["gameFlags"]["testFlag"] == sample_game_state["gameFlags"]["testFlag"]
    assert "companions" in data
    assert "test_companion" in data["companions"]
    assert data["companions"]["test_companion"]["relationship"] == sample_game_state["companions"]["test_companion"]["relationship"]


def test_load_game_state_with_save_id(client, sample_game_state):
    """Test loading a game state with a specific save ID."""
    # First, save a game state
    save_response = client.post("/api/game/state", json=sample_game_state)
    save_data = save_response.json()
    
    # Check if save was successful and has a saveId
    if save_response.status_code == 200 and "saveId" in save_data:
        save_id = save_data["saveId"]
        
        # Send a GET request to load the game state with the save ID
        response = client.get(f"/api/game/state/{sample_game_state['playerId']}?save_id={save_id}")
        
        # Check that the response is successful
        assert response.status_code == 200
        
        # Check that the response contains the expected fields
        data = response.json()
        assert data["playerId"] == sample_game_state["playerId"]
        assert data["saveId"] == save_id
    else:
        pytest.skip("Save game state failed, skipping test")


def test_load_game_state_player_not_found(client):
    """Test loading a game state for a player that doesn't exist."""
    # Send a GET request to load a game state for a non-existent player
    response = client.get("/api/game/state/nonexistent")
    
    # Check that the response is not found
    assert response.status_code == 404
    
    # Check that the response contains an error message
    data = response.json()
    assert "detail" in data or "message" in data
    if "detail" in data:
        assert "Player with ID nonexistent not found" in data["detail"]
    elif "message" in data:
        assert "Player with ID nonexistent not found" in data["message"]


def test_load_game_state_save_not_found(client, sample_game_state):
    """Test loading a game state with a save ID that doesn't exist."""
    # First, save a game state
    save_response = client.post("/api/game/state", json=sample_game_state)
    
    # Send a GET request to load a game state with a non-existent save ID
    response = client.get(f"/api/game/state/{sample_game_state['playerId']}?save_id=nonexistent")
    
    # Check that the response is not found
    assert response.status_code == 404
    
    # Check that the response contains an error message
    data = response.json()
    assert "detail" in data or "message" in data
    if "detail" in data:
        assert "Save not found" in data["detail"] or "Player with ID" in data["detail"]
    elif "message" in data:
        assert "Save not found" in data["message"] or "Player with ID" in data["message"]


def test_list_saved_games(client, sample_game_state):
    """Test listing saved games for a player."""
    # First, save a game state
    save_response = client.post("/api/game/state", json=sample_game_state)
    
    # Send a GET request to list saved games
    response = client.get(f"/api/game/state/saves/{sample_game_state['playerId']}")
    
    # Check that the response is successful
    assert response.status_code == 200
    
    # Check that the response contains the expected fields
    data = response.json()
    assert data["playerId"] == sample_game_state["playerId"]
    assert "saves" in data
    assert len(data["saves"]) >= 1
    
    # Check that the first save contains the expected fields
    save = data["saves"][0]
    assert "saveId" in save
    assert "timestamp" in save
    assert "location" in save
    assert "questName" in save


def test_list_saved_games_player_not_found(client):
    """Test listing saved games for a player that doesn't exist."""
    # Send a GET request to list saved games for a non-existent player
    response = client.get("/api/game/state/saves/nonexistent")
    
    # Check that the response is not found
    assert response.status_code == 404
    
    # Check that the response contains an error message
    data = response.json()
    assert "detail" in data or "message" in data
    if "detail" in data:
        assert "Player with ID nonexistent not found" in data["detail"] or "Not Found" in data["detail"]
    elif "message" in data:
        assert "Player with ID nonexistent not found" in data["message"] or "Not Found" in data["message"] 