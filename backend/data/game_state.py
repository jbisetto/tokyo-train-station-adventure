"""
Data access layer for game state operations.
"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC

# In-memory storage for game states (in a real implementation, this would be a database)
_game_states: Dict[str, Dict[str, Any]] = {}


class GameStateError(Exception):
    """Base exception for game state errors."""
    pass


class PlayerNotFoundError(GameStateError):
    """Exception raised when a player is not found."""
    pass


class SaveNotFoundError(GameStateError):
    """Exception raised when a save is not found."""
    pass


class InvalidPlayerIdError(GameStateError):
    """Exception raised when a player ID is invalid."""
    pass


def validate_player_id(player_id: str) -> None:
    """
    Validate a player ID.
    
    Args:
        player_id: The player ID to validate.
        
    Raises:
        InvalidPlayerIdError: If the player ID is invalid.
    """
    if not player_id or len(player_id) < 3:
        raise InvalidPlayerIdError(f"Invalid player ID format: {player_id}")


def save_game_state(game_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save a game state.
    
    Args:
        game_state: The game state to save.
        
    Returns:
        A dictionary containing the save ID and timestamp.
        
    Raises:
        InvalidPlayerIdError: If the player ID is invalid.
    """
    player_id = game_state.get("player_id")
    validate_player_id(player_id)
    
    # Generate a unique save ID
    save_id = str(uuid.uuid4())
    timestamp = game_state.get("timestamp", datetime.now(UTC))
    
    # Create a new save entry
    save_entry = {
        "save_id": save_id,
        "timestamp": timestamp,
        "last_played": timestamp,
        "player_id": player_id,
        "session_id": game_state.get("session_id"),
        "location": game_state.get("location", {}),
        "quest_state": game_state.get("quest_state", {}),
        "inventory": game_state.get("inventory", []),
        "game_flags": game_state.get("game_flags", {}),
        "companions": game_state.get("companions", {})
    }
    
    # Initialize player's saves if not exists
    if player_id not in _game_states:
        _game_states[player_id] = {}
    
    # Store the save
    _game_states[player_id][save_id] = save_entry
    
    return {
        "success": True,
        "save_id": save_id,
        "timestamp": timestamp
    }


def load_game_state(player_id: str, save_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Load a game state.
    
    Args:
        player_id: The ID of the player.
        save_id: The ID of the save to load. If None, the most recent save is loaded.
        
    Returns:
        The loaded game state.
        
    Raises:
        InvalidPlayerIdError: If the player ID is invalid.
        PlayerNotFoundError: If the player is not found.
        SaveNotFoundError: If the save is not found.
    """
    validate_player_id(player_id)
    
    # Check if player exists
    if player_id not in _game_states:
        raise PlayerNotFoundError(f"Player with ID {player_id} not found")
    
    player_saves = _game_states[player_id]
    
    # If no save ID is provided, get the most recent save
    if save_id is None:
        if not player_saves:
            raise SaveNotFoundError(f"No saves found for player {player_id}")
        
        # Find the most recent save
        most_recent_save = max(
            player_saves.values(),
            key=lambda save: save["timestamp"]
        )
        return most_recent_save
    
    # Check if save exists
    if save_id not in player_saves:
        raise SaveNotFoundError(f"Save with ID {save_id} not found for player {player_id}")
    
    return player_saves[save_id]


def list_saved_games(player_id: str) -> Dict[str, Any]:
    """
    List all saved games for a player.
    
    Args:
        player_id: The ID of the player.
        
    Returns:
        A dictionary containing the player ID and a list of save metadata.
        
    Raises:
        InvalidPlayerIdError: If the player ID is invalid.
        PlayerNotFoundError: If the player is not found.
    """
    validate_player_id(player_id)
    
    # Check if player exists
    if player_id not in _game_states:
        raise PlayerNotFoundError(f"Player with ID {player_id} not found")
    
    player_saves = _game_states[player_id]
    
    # Create save metadata list
    saves = []
    for save_id, save in player_saves.items():
        location_name = save["location"].get("area", "Unknown")
        quest_name = save["quest_state"].get("active_quest", "Unknown")
        
        saves.append({
            "save_id": save_id,
            "timestamp": save["timestamp"],
            "location_name": location_name,
            "quest_name": quest_name,
            "level": None  # Level is not implemented yet
        })
    
    # Sort saves by timestamp (newest first)
    saves.sort(key=lambda save: save["timestamp"], reverse=True)
    
    return {
        "player_id": player_id,
        "saves": saves
    }


# Create some mock data for testing
def _create_mock_data():
    """Create mock game state data for testing."""
    # Player 1: player123
    player1_id = "player123"
    
    # Save 1: Tokyo Station
    save_game_state({
        "player_id": player1_id,
        "session_id": "session1",
        "timestamp": datetime.now(UTC) - timedelta(days=2),
        "location": {
            "area": "tokyo_station_entrance",
            "position": {
                "x": 100,
                "y": 200
            }
        },
        "quest_state": {
            "active_quest": "find_platform",
            "quest_step": "talk_to_station_attendant",
            "objectives": [
                {
                    "id": "find_station_map",
                    "completed": True,
                    "description": "Find a station map"
                },
                {
                    "id": "talk_to_attendant",
                    "completed": False,
                    "description": "Ask the station attendant for directions"
                }
            ]
        },
        "inventory": ["wallet", "phone", "station_map"],
        "game_flags": {
            "tutorialCompleted": True,
            "metCharacters": ["station_guard"]
        },
        "companions": {
            "hachi": {
                "relationship": 0.5,
                "assistance_used": 2
            }
        }
    })
    
    # Save 2: Ticket Machine Area
    save_game_state({
        "player_id": player1_id,
        "session_id": "session2",
        "timestamp": datetime.now(UTC) - timedelta(hours=5),
        "location": {
            "area": "ticket_machine_area",
            "position": {
                "x": 320,
                "y": 240
            }
        },
        "quest_state": {
            "active_quest": "buy_ticket_to_odawara",
            "quest_step": "find_ticket_machine",
            "objectives": [
                {
                    "id": "speak_to_information_desk",
                    "completed": True,
                    "description": "Speak to the information desk attendant"
                },
                {
                    "id": "locate_ticket_machine",
                    "completed": True,
                    "description": "Find a ticket machine"
                },
                {
                    "id": "purchase_ticket",
                    "completed": False,
                    "description": "Purchase a ticket to Odawara"
                }
            ]
        },
        "inventory": ["wallet", "phone", "station_map", "notebook"],
        "game_flags": {
            "tutorialCompleted": True,
            "metCharacters": ["station_guard", "info_attendant"]
        },
        "companions": {
            "hachi": {
                "relationship": 0.65,
                "assistance_used": 3
            }
        }
    })
    
    # Player 2: player456
    player2_id = "player456"
    
    # Save 1: Platform Area
    save_game_state({
        "player_id": player2_id,
        "session_id": "session1",
        "timestamp": datetime.now(UTC) - timedelta(days=1),
        "location": {
            "area": "platform_3",
            "position": {
                "x": 450,
                "y": 180
            }
        },
        "quest_state": {
            "active_quest": "board_train_to_kyoto",
            "quest_step": "wait_for_train",
            "objectives": [
                {
                    "id": "find_platform",
                    "completed": True,
                    "description": "Find Platform 3"
                },
                {
                    "id": "validate_ticket",
                    "completed": True,
                    "description": "Validate your ticket"
                },
                {
                    "id": "board_train",
                    "completed": False,
                    "description": "Board the train when it arrives"
                }
            ]
        },
        "inventory": ["wallet", "phone", "validated_ticket", "bento_box"],
        "game_flags": {
            "tutorialCompleted": True,
            "metCharacters": ["ticket_inspector", "fellow_passenger"]
        },
        "companions": {
            "hachi": {
                "relationship": 0.8,
                "assistance_used": 5
            }
        }
    })


# Create mock data when module is imported
_create_mock_data() 