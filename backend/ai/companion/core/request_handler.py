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
            
            # Log the initial tier selection at INFO level
            self.logger.info(f"Request {request_id} initially classified for {tier.name} processing with intent={intent.name}, complexity={complexity.name}, confidence={confidence:.2f}")
            
            # Try to get a processor using the cascade pattern
            processor_start = time.time()
            processor_response = await self._process_with_cascade(classified_request, tier)
            processor_time = time.time() - processor_start
            self.logger.debug(f"Request processed in {processor_time:.3f}s: {request_id}")
            
            # Check if the response is a special error message that should be returned directly
            if isinstance(processor_response, str) and "All AI services are currently disabled" in processor_response:
                self.logger.warning(f"Returning error message directly: {processor_response}")
                return processor_response
            
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
    
    async def _process_with_cascade(self, classified_request: ClassifiedRequest, 
                             preferred_tier: ProcessingTier) -> str:
        """
        Process a request using the cascade pattern.
        
        This method attempts to process the request with the preferred tier.
        If that fails (e.g., because the tier is disabled), it will try the next
        tier in the cascade order.
        
        Args:
            classified_request: The classified request to process
            preferred_tier: The preferred processing tier
            
        Returns:
            The processor response
            
        Raises:
            Exception: If no processors are available or all processing attempts fail
        """
        # Define the cascade order based on the preferred tier
        cascade_order = self._get_cascade_order(preferred_tier)
        
        # Try each tier in the cascade order
        errors = []
        for tier in cascade_order:
            try:
                self.logger.debug(f"Attempting to process request {classified_request.request_id} with {tier.name}")
                
                # Get a processor for this tier
                processor = self.processor_factory.get_processor(tier)
                self.logger.debug(f"Got processor of type {type(processor).__name__} for {tier.name}")
                
                # Check if this tier is enabled before processing
                if not self._is_tier_enabled(tier, processor):
                    self.logger.warning(f"Tier {tier.name} is disabled, skipping to next tier")
                    errors.append(f"{tier.name}: disabled in configuration")
                    continue
                
                # Update the processing tier in the classified request
                classified_request.processing_tier = tier
                
                # Log that we're using this tier
                self.logger.info(f"Processing request {classified_request.request_id} with {tier.name} processor")
                
                # Check if the processor's process method is async
                is_async = inspect.iscoroutinefunction(processor.process)
                
                if is_async:
                    # If it's async, await it
                    response = await processor.process(classified_request)
                else:
                    # If it's not async, call it normally
                    response = processor.process(classified_request)
                
                # If response is a string, convert to dict with tier info
                if isinstance(response, str):
                    response = {
                        'response_text': response,
                        'processing_tier': tier  # Include the tier that processed it
                    }
                elif isinstance(response, dict) and 'processing_tier' not in response:
                    response['processing_tier'] = tier  # Add tier if missing
                
                return response
                
            except Exception as e:
                # Log the error and continue with the next tier
                self.logger.warning(f"Failed to process request {classified_request.request_id} with {tier.name} processor: {str(e)}")
                errors.append(f"{tier.name}: {str(e)}")
        
        # If we get here, all tiers failed
        self.logger.error(f"All processing tiers failed for request {classified_request.request_id}: {errors}")
        
        # Check if all errors are due to tiers being disabled
        if all("disabled in configuration" in error for error in errors):
            # If all tiers are disabled, return a direct error message without formatting
            error_message = "All AI services are currently disabled. Please check your configuration."
            return error_message
        else:
            raise Exception(f"Failed to process request with any tier: {errors}")
    
    def _get_cascade_order(self, preferred_tier: ProcessingTier) -> list:
        """
        Get the cascade order for a preferred tier.
        
        Args:
            preferred_tier: The preferred tier level
            
        Returns:
            List of tier levels in cascade order
        """
        # Start with the preferred tier
        order = [preferred_tier]
        
        # Add the remaining tiers in a sensible order
        if preferred_tier == ProcessingTier.TIER_1:
            order.extend([ProcessingTier.TIER_2, ProcessingTier.TIER_3])
        elif preferred_tier == ProcessingTier.TIER_2:
            order.extend([ProcessingTier.TIER_3, ProcessingTier.TIER_1])
        else:  # TIER_3
            order.extend([ProcessingTier.TIER_2, ProcessingTier.TIER_1])
        
        return order

    def _is_tier_enabled(self, tier: ProcessingTier, processor) -> bool:
        """Check if a tier is enabled in the configuration"""
        # Try to access the config attribute if it exists
        if hasattr(processor, 'config'):
            return processor.config.get('enabled', False)
        
        # Fallback to checking via the processor factory
        try:
            # This assumes processor_factory has a method to check if a tier is enabled
            return self.processor_factory.is_tier_enabled(tier)
        except AttributeError:
            # If no method exists, we can't determine if it's enabled
            # Default to trying it anyway
            return True 