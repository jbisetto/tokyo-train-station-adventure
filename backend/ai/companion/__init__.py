"""
Tokyo Train Station Adventure - Companion AI Module

This module implements the companion dog AI that assists the player
with Japanese language learning and navigation through the train station.
"""

__version__ = "0.1.0"

# Import core components for easier access
# These imports will be uncommented as we implement each component
from backend.ai.companion.core.request_handler import RequestHandler
from backend.ai.companion.core.intent_classifier import IntentClassifier
from backend.ai.companion.core.processor_framework import ProcessorFactory
from backend.ai.companion.core.response_formatter import ResponseFormatter

# Main function to process companion requests
def process_companion_request(request_data, game_context=None):
    """
    Process a request to the companion AI.
    
    Args:
        request_data: Dictionary containing the request data
        game_context: Optional game context information
        
    Returns:
        Dictionary containing the companion's response
    """
    # Create a request handler
    handler = RequestHandler()
    
    # Process the request
    response = handler.process_request(request_data, game_context)
    
    return response 