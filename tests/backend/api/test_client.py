"""
Command-line test client for the API.
"""

import json
import argparse
import requests
from typing import Dict, Any


def send_companion_assist_request(base_url: str, player_id: str, session_id: str, location: str, request_type: str, text: str) -> Dict[str, Any]:
    """
    Send a companion assist request to the API.
    
    Args:
        base_url: The base URL of the API
        player_id: The player ID
        session_id: The session ID
        location: The player's location
        request_type: The type of request
        text: The request text
        
    Returns:
        The API response
    """
    # Create the request data
    request_data = {
        "playerId": player_id,
        "sessionId": session_id,
        "gameContext": {
            "location": location,
            "currentQuest": "buy_ticket_to_odawara",
            "questStep": "find_ticket_machine",
            "nearbyEntities": ["ticket_machine_1", "station_map", "information_booth"],
            "lastInteraction": "station_map"
        },
        "request": {
            "type": request_type,
            "text": text,
            "targetEntity": "ticket_machine_1",
            "language": "english"
        }
    }
    
    # Send the request
    response = requests.post(
        f"{base_url}/api/companion/assist",
        json=request_data,
        headers={"Content-Type": "application/json"}
    )
    
    # Return the response
    return {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "body": response.json() if response.status_code == 200 else response.text
    }


def main():
    """
    Main entry point for the command-line test client.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Test client for the Tokyo Train Station Adventure API")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--player-id", default="player123", help="Player ID")
    parser.add_argument("--session-id", default="session456", help="Session ID")
    parser.add_argument("--location", default="ticket_machine_area", help="Player's location")
    parser.add_argument("--type", default="vocabulary", help="Request type")
    parser.add_argument("--text", default="What does 切符 mean?", help="Request text")
    args = parser.parse_args()
    
    # Send the request
    print(f"Sending companion assist request to {args.url}...")
    response = send_companion_assist_request(
        base_url=args.url,
        player_id=args.player_id,
        session_id=args.session_id,
        location=args.location,
        request_type=args.type,
        text=args.text
    )
    
    # Print the response
    print(f"Status code: {response['status_code']}")
    print("Headers:")
    for key, value in response["headers"].items():
        print(f"  {key}: {value}")
    print("Body:")
    if isinstance(response["body"], dict):
        print(json.dumps(response["body"], indent=2))
    else:
        print(response["body"])


if __name__ == "__main__":
    main() 