"""
Test client for the dialogue process endpoint.
"""

import requests
import json
import sys
from pprint import pprint

# Default values
DEFAULT_URL = "http://localhost:8000/api/dialogue/process"
DEFAULT_PLAYER_ID = "test-player"
DEFAULT_SESSION_ID = "test-session"
DEFAULT_SPEAKER_ID = "station-attendant"
DEFAULT_SPEAKER_TYPE = "npc"
DEFAULT_TEXT = "How do I buy a ticket to Odawara?"
DEFAULT_LANGUAGE = "english"
DEFAULT_INPUT_TYPE = "text"
DEFAULT_LOCATION = "tokyo_station"


def send_dialogue_request(
    url=DEFAULT_URL,
    player_id=DEFAULT_PLAYER_ID,
    session_id=DEFAULT_SESSION_ID,
    speaker_id=DEFAULT_SPEAKER_ID,
    speaker_type=DEFAULT_SPEAKER_TYPE,
    text=DEFAULT_TEXT,
    language=DEFAULT_LANGUAGE,
    input_type=DEFAULT_INPUT_TYPE,
    location=DEFAULT_LOCATION,
    conversation_id=None,
    conversation_history=None
):
    """
    Send a request to the dialogue process endpoint.
    
    Args:
        url: The URL of the dialogue process endpoint
        player_id: The ID of the player
        session_id: The ID of the session
        speaker_id: The ID of the speaker (NPC or companion)
        speaker_type: The type of speaker (npc or companion)
        text: The text input from the player
        language: The language of the text input (english or japanese)
        input_type: The type of input (text, voice, or selection)
        location: The current location in the game
        conversation_id: Optional conversation ID for continuing a conversation
        conversation_history: Optional history of previous exchanges
        
    Returns:
        The response from the endpoint
    """
    # Prepare the request payload
    payload = {
        "playerId": player_id,
        "sessionId": session_id,
        "speakerId": speaker_id,
        "speakerType": speaker_type,
        "dialogueInput": {
            "text": text,
            "language": language,
            "inputType": input_type
        },
        "gameContext": {
            "location": location
        }
    }
    
    # Add optional fields if provided
    if conversation_id:
        payload["conversationId"] = conversation_id
    
    if conversation_history:
        payload["conversationHistory"] = conversation_history
    
    # Send the request
    try:
        response = requests.post(url, json=payload)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return None


def main():
    """
    Main function to run the test client.
    """
    # Parse command line arguments
    if len(sys.argv) > 1:
        text = sys.argv[1]
    else:
        text = DEFAULT_TEXT
        
    if len(sys.argv) > 2:
        speaker_id = sys.argv[2]
    else:
        speaker_id = DEFAULT_SPEAKER_ID
        
    if len(sys.argv) > 3:
        speaker_type = sys.argv[3]
    else:
        speaker_type = DEFAULT_SPEAKER_TYPE
    
    # Send the request
    print(f"Sending dialogue request to {DEFAULT_URL}")
    print(f"Speaker: {speaker_id} ({speaker_type})")
    print(f"Text: {text}")
    print("-" * 50)
    
    response = send_dialogue_request(
        text=text,
        speaker_id=speaker_id,
        speaker_type=speaker_type
    )
    
    if response:
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            # Pretty print the response
            pprint(response.json())
        else:
            print(f"Error: {response.text}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 