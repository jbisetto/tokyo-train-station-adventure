"""
Test client for the Game State API.
"""

import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List


class GameStateTestClient:
    """
    Test client for the Game State API.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the test client.
        
        Args:
            base_url: The base URL of the API.
        """
        self.base_url = base_url
    
    def save_game_state(self, player_id: str, session_id: str, location: Dict[str, Any],
                        quest_state: Dict[str, Any], inventory: Optional[List[str]] = None,
                        game_flags: Optional[Dict[str, Any]] = None,
                        companions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Save a game state.
        
        Args:
            player_id: The ID of the player.
            session_id: The ID of the session.
            location: The player's location.
            quest_state: The current quest state.
            inventory: The player's inventory.
            game_flags: Game state flags.
            companions: Companion states.
            
        Returns:
            The response from the API.
        """
        url = f"{self.base_url}/api/game/state"
        
        # Create the request body
        data = {
            "playerId": player_id,
            "sessionId": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "location": location,
            "questState": quest_state,
            "inventory": inventory or [],
            "gameFlags": game_flags or {},
            "companions": companions or {}
        }
        
        # Send the request
        response = requests.post(url, json=data)
        
        # Return the response
        return response.json()
    
    def load_game_state(self, player_id: str, save_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Load a game state.
        
        Args:
            player_id: The ID of the player.
            save_id: The ID of the save to load. If None, the most recent save is loaded.
            
        Returns:
            The response from the API.
        """
        url = f"{self.base_url}/api/game/state/{player_id}"
        
        # Add save_id parameter if provided
        if save_id:
            url += f"?save_id={save_id}"
        
        # Send the request
        response = requests.get(url)
        
        # Return the response
        return response.json()
    
    def list_saved_games(self, player_id: str) -> Dict[str, Any]:
        """
        List all saved games for a player.
        
        Args:
            player_id: The ID of the player.
            
        Returns:
            The response from the API.
        """
        url = f"{self.base_url}/api/game/saves/{player_id}"
        
        # Send the request
        response = requests.get(url)
        
        # Return the response
        return response.json()


if __name__ == "__main__":
    # Create a test client
    client = GameStateTestClient()
    
    # Example usage
    try:
        # Save a game state
        save_response = client.save_game_state(
            player_id="test_player",
            session_id="test_session",
            location={
                "area": "tokyo_station_entrance",
                "position": {
                    "x": 100,
                    "y": 200
                }
            },
            quest_state={
                "activeQuest": "find_platform",
                "questStep": "talk_to_station_attendant",
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
            inventory=["wallet", "phone", "station_map"],
            game_flags={
                "tutorialCompleted": True,
                "metCharacters": ["station_guard"]
            },
            companions={
                "hachi": {
                    "relationship": 0.5,
                    "assistanceUsed": 2
                }
            }
        )
        
        print("Save Game State Response:")
        print(json.dumps(save_response, indent=2))
        print()
        
        # Get the save ID
        save_id = save_response["saveId"]
        
        # Load the game state
        load_response = client.load_game_state("test_player", save_id)
        
        print("Load Game State Response:")
        print(json.dumps(load_response, indent=2))
        print()
        
        # List saved games
        list_response = client.list_saved_games("test_player")
        
        print("List Saved Games Response:")
        print(json.dumps(list_response, indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}") 