"""
Tokyo Train Station Adventure - Request Handler

This module implements the request handler for the companion AI system.
It coordinates the flow of requests through the system.
"""

import logging
import traceback
import inspect
import time
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
        request_id = getattr(request, 'request_id', 'unknown')
        start_time = time.time()
        self.logger.info(f"Handling request: {request_id} - {request.player_input}")
        
        try:
            # Classify the request
            self.logger.debug(f"Classifying request: {request_id}")
            classification_start = time.time()
            intent, complexity, tier, confidence, entities = self.intent_classifier.classify(request)
            classification_time = time.time() - classification_start
            self.logger.debug(f"Request classified in {classification_time:.3f}s as intent={intent.name}, complexity={complexity.name}, tier={tier.name}, confidence={confidence:.2f}: {request_id}")
            
            # Create a classified request
            self.logger.debug(f"Creating classified request: {request_id}")
            classified_request = ClassifiedRequest.from_companion_request(
                request=request,
                intent=intent,
                complexity=complexity,
                processing_tier=tier,
                confidence=confidence,
                extracted_entities=entities
            )
            
            # Log the tier selection at INFO level
            self.logger.info(f"Request {request_id} routed to {tier.name} processor with intent={intent.name}, complexity={complexity.name}, confidence={confidence:.2f}")
            
            # Get the appropriate processor for the tier
            self.logger.debug(f"Getting processor for tier {tier.name}: {request_id}")
            processor_start = time.time()
            processor = self.processor_factory.get_processor(tier)
            self.logger.debug(f"Using processor: {processor.__class__.__name__}: {request_id}")
            
            # Process the request
            self.logger.debug(f"Processing request with {processor.__class__.__name__}: {request_id}")
            # Check if the processor's process method is async
            is_async = inspect.iscoroutinefunction(processor.process)
            self.logger.debug(f"Processor.process is {'async' if is_async else 'sync'}: {request_id}")
            
            if is_async:
                # If it's async, await it
                self.logger.debug(f"Awaiting async processor.process: {request_id}")
                processor_response = await processor.process(classified_request)
            else:
                # If it's not async, call it normally
                self.logger.debug(f"Calling sync processor.process: {request_id}")
                processor_response = processor.process(classified_request)
                
            processor_time = time.time() - processor_start
            self.logger.debug(f"Request processed in {processor_time:.3f}s: {request_id}")
            
            # Format the response
            self.logger.debug(f"Formatting response: {request_id}")
            format_start = time.time()
            response = self.response_formatter.format_response(
                processor_response=processor_response,
                classified_request=classified_request
            )
            format_time = time.time() - format_start
            self.logger.debug(f"Response formatted in {format_time:.3f}s (length: {len(response)}): {request_id}")
            
            # Update conversation context if provided
            if conversation_context:
                self.logger.debug(f"Updating conversation context: {request_id}")
                # Create a companion response object
                companion_response = CompanionResponse(
                    request_id=request.request_id,
                    response_text=response,
                    intent=intent,
                    processing_tier=tier
                )
                
                # Add the interaction to the conversation context
                conversation_context.add_interaction(request, companion_response)
                self.logger.debug(f"Conversation context updated, history size: {len(conversation_context.request_history)}: {request_id}")
            
            total_time = time.time() - start_time
            self.logger.info(f"Request handled successfully in {total_time:.3f}s: {request_id}")
            return response
            
        except Exception as e:
            # Log the error
            total_time = time.time() - start_time
            self.logger.error(f"Error handling request after {total_time:.3f}s: {str(e)}: {request_id}")
            self.logger.debug(traceback.format_exc())
            
            # Return a fallback response
            return f"I'm sorry, I encountered an error while processing your request. Please try again." 