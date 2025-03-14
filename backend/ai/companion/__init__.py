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
from backend.ai.companion.core.models import CompanionResponse, IntentCategory, ProcessingTier

# Main function to process companion requests
async def process_companion_request(request_data, game_context=None):
    """
    Process a request to the companion AI.
    
    Args:
        request_data: Dictionary containing the request data
        game_context: Optional game context information
        
    Returns:
        Dictionary containing the companion's response
    """
    # Create the required components
    intent_classifier = IntentClassifier()
    processor_factory = ProcessorFactory()
    response_formatter = ResponseFormatter()
    
    # Create a request handler with the components
    handler = RequestHandler(
        intent_classifier=intent_classifier,
        processor_factory=processor_factory,
        response_formatter=response_formatter
    )
    
    # Process the request to get the response text
    response_text = await handler.handle_request(request_data, game_context)
    
    # Get the intent and tier from the classifier
    intent, complexity, tier, confidence, entities = intent_classifier.classify(request_data)
    
    # Create a CompanionResponse object
    response = CompanionResponse(
        request_id=request_data.request_id,
        response_text=response_text,
        intent=intent,
        processing_tier=tier,
        suggested_actions=["How do I buy a ticket?", "What is 'platform' in Japanese?"],
        learning_cues={
            "japanese_text": entities.get("word", ""),
            "pronunciation": entities.get("pronunciation", ""),
            "learning_moments": [intent.value],
            "vocabulary_unlocked": [entities.get("word", "")]
        },
        emotion="helpful",
        confidence=confidence,
        debug_info={
            "complexity": complexity.value,
            "tier": tier.value,
            "entities": entities
        }
    )
    
    return response 