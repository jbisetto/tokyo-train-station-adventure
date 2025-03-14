"""
Tokyo Train Station Adventure - Request Handler

This module implements the request handler for the companion AI system.
It coordinates the flow of requests through the system.
"""

import logging
import traceback
import inspect
from typing import Optional, Any, Dict, Tuple

from backend.ai.companion.core.models import (
    CompanionRequest,
    ClassifiedRequest,
    CompanionResponse,
    ConversationContext,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)


class RequestHandler:
    """
    Handles requests to the companion AI system.
    
    This class is responsible for:
    1. Receiving requests from the player
    2. Classifying the intent and complexity of the request
    3. Routing the request to the appropriate processor
    4. Formatting the response
    5. Tracking conversation context
    """
    
    def __init__(self, intent_classifier, processor_factory, response_formatter):
        """
        Initialize the request handler.
        
        Args:
            intent_classifier: Component that classifies request intent and complexity
            processor_factory: Factory that provides processors for different tiers
            response_formatter: Component that formats responses
        """
        self.intent_classifier = intent_classifier
        self.processor_factory = processor_factory
        self.response_formatter = response_formatter
        self.logger = logging.getLogger(__name__)
    
    async def handle_request(self, request: CompanionRequest, 
                      conversation_context: Optional[ConversationContext] = None) -> str:
        """
        Handle a request from the player.
        
        Args:
            request: The request from the player
            conversation_context: Optional conversation context for multi-turn interactions
            
        Returns:
            A formatted response string
        """
        try:
            # Log the incoming request
            self.logger.info(f"Handling request: {request.request_id} - {request.player_input}")
            
            # Classify the request
            intent, complexity, tier, confidence, entities = self.intent_classifier.classify(request)
            
            # Create a classified request
            classified_request = ClassifiedRequest.from_companion_request(
                request=request,
                intent=intent,
                complexity=complexity,
                processing_tier=tier,
                confidence=confidence,
                extracted_entities=entities
            )
            
            # Get the appropriate processor for the tier
            processor = self.processor_factory.get_processor(tier)
            
            # Process the request
            # Check if the processor's process method is async
            if inspect.iscoroutinefunction(processor.process):
                # If it's async, await it
                processor_response = await processor.process(classified_request)
            else:
                # If it's not async, call it normally
                processor_response = processor.process(classified_request)
            
            # Format the response
            response = self.response_formatter.format_response(
                processor_response=processor_response,
                classified_request=classified_request
            )
            
            # Update conversation context if provided
            if conversation_context:
                # Create a companion response object
                companion_response = CompanionResponse(
                    request_id=request.request_id,
                    response_text=response,
                    intent=intent,
                    processing_tier=tier
                )
                
                # Add the interaction to the conversation context
                conversation_context.add_interaction(request, companion_response)
            
            return response
            
        except Exception as e:
            # Log the error
            self.logger.error(f"Error handling request: {str(e)}")
            self.logger.debug(traceback.format_exc())
            
            # Return a fallback response
            return f"I'm sorry, I encountered an error while processing your request. Please try again." 