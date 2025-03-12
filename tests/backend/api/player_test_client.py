"""
Test client for the player progress API endpoint.
"""

import argparse
import json
import requests
from typing import Dict, Any


def get_player_progress(base_url: str, player_id: str) -> Dict[str, Any]:
    """
    Get player progress from the API.
    
    Args:
        base_url: The base URL of the API
        player_id: The player ID
        
    Returns:
        The player progress data
    """
    url = f"{base_url}/api/player/progress/{player_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return {}


def main():
    """Run the test client."""
    parser = argparse.ArgumentParser(description="Test client for the player progress API endpoint")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--player-id", default="player123", help="Player ID")
    
    args = parser.parse_args()
    
    print(f"Getting progress for player {args.player_id}...")
    progress = get_player_progress(args.base_url, args.player_id)
    
    if progress:
        print("Player progress:")
        print(json.dumps(progress, indent=2))


if __name__ == "__main__":
    main() 