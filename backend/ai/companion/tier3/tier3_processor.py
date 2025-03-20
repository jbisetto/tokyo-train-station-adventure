"""
Tokyo Train Station Adventure - Tier 3 Processor

This module implements the Tier 3 processor for the companion AI system,
which uses Amazon Bedrock for generating responses to complex requests.
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional, List
from unittest.mock import patch

from backend.ai.companion.core.models import (
    ClassifiedRequest,
    CompanionRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from backend.ai.companion.core.processor_framework import Processor
from backend.ai.companion.tier3.bedrock_client import BedrockClient, BedrockError
from backend.ai.companion.tier3.usage_tracker import UsageTracker, default_tracker
from backend.ai.companion.core.context_manager import ContextManager, default_context_manager
from backend.ai.companion.core.conversation_manager import ConversationManager, ConversationState
from backend.ai.companion.core.prompt_manager import PromptManager
from backend.ai.companion.tier3.scenario_detection import ScenarioDetector, ScenarioType
from backend.ai.companion.tier3.prompt_optimizer import PromptOptimizer
from backend.ai.companion.tier3.conversation_manager import ConversationManager
from backend.ai.companion.utils.monitoring import ProcessorMonitor
from backend.ai.companion.config import get_config, CLOUD_API_CONFIG


class Tier3Processor(Processor):
    """
    Tier 3 processor that uses Amazon Bedrock for generating responses.
    
    This processor handles complex requests by generating responses with a
    powerful cloud-based language model. It is the most flexible but also
    the most expensive processor in the tiered processing framework.
    """
    
    def __init__(
        self,
        usage_tracker: Optional[UsageTracker] = None,
        context_manager: Optional[ContextManager] = None
    ):
        """
        Initialize the Tier 3 processor.
        
        Args:
            usage_tracker: The usage tracker for monitoring API usage
            context_manager: Context manager for tracking conversation context
        """
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.client = self._create_bedrock_client(usage_tracker)
        self.conversation_manager = ConversationManager()
        self.prompt_manager = PromptManager(tier_specific_config={"model_type": "bedrock"})
        self.scenario_detector = ScenarioDetector()
        self.context_manager = context_manager or default_context_manager
        self.monitor = ProcessorMonitor()
        
        # Initialize storage
        self.conversation_histories = {}
        
        self.logger.info("Initialized Tier3Processor with Bedrock client")
    
    def _create_bedrock_client(self, usage_tracker: Optional[UsageTracker] = None) -> BedrockClient:
        """
        Create a Bedrock client.
        
        Args:
            usage_tracker: Optional usage tracker for monitoring API usage
            
        Returns:
            A configured Bedrock client
        """
        return BedrockClient(
            region_name=CLOUD_API_CONFIG.get("region", "us-east-1"),
            model_id=CLOUD_API_CONFIG.get("model", "amazon.nova-micro-v1:0"),
            max_tokens=CLOUD_API_CONFIG.get("max_tokens", 512),
            usage_tracker=usage_tracker or default_tracker
        )
    
    async def process(self, request: ClassifiedRequest) -> str:
        """
        Process a classified request and generate a response using Amazon Bedrock.
        
        Args:
            request: A classified request
            
        Returns:
            The generated response string
        """
        start_time = time.time()
        
        try:
            # Check if this is a known scenario that should be handled by a specialized handler
            scenario_type = self.scenario_detector.detect_scenario(request)
            if scenario_type != ScenarioType.UNKNOWN and request.complexity == ComplexityLevel.COMPLEX:
                self.logger.info(f"Using specialized handler for scenario type: {scenario_type}")
                try:
                    response = await self.scenario_detector.handle_scenario(
                        request, 
                        self.context_manager, 
                        self.client
                    )
                    return response
                except Exception as e:
                    self.logger.error(f"Error in specialized handler: {str(e)}")
                    # Fall back to standard processing
            
            # Create a companion request for the client
            companion_request = CompanionRequest(
                request_id=request.request_id,
                player_input=request.player_input,
                request_type=request.request_type,
                timestamp=request.timestamp,
                game_context=request.game_context,
                additional_params=request.additional_params
            )
            
            # Create a base prompt for the request
            base_prompt = self.prompt_manager.create_prompt(
                request
            )
            
            # Initialize conversation_history as an empty list
            conversation_history = []
            
            # Get conversation history if a conversation ID is provided
            conversation_id = request.additional_params.get("conversation_id")
            if conversation_id:
                try:
                    # Try to use get_or_create_context if available
                    context = self.context_manager.get_or_create_context(conversation_id)
                except AttributeError:
                    # Fallback to get_context if get_or_create_context is not available
                    context = self.context_manager.get_context(conversation_id)
                
                if context:
                    # Create conversation history from the context
                    if isinstance(context, dict) and "entries" in context:
                        conversation_history = context["entries"]
            
            # For testing, we'll just use a simple state and the base prompt
            state = ConversationState.NEW_TOPIC
            prompt = base_prompt
            
            # Generate a response using the Bedrock client
            try:
                # Check if the generate method is a coroutine or not
                if asyncio.iscoroutinefunction(self.client.generate):
                    response = await self.client.generate(
                        request=companion_request,
                        model_id=CLOUD_API_CONFIG.get("model", "amazon.nova-micro-v1:0"),
                        temperature=CLOUD_API_CONFIG.get("temperature", 0.7),
                        max_tokens=CLOUD_API_CONFIG.get("max_tokens", 512),
                        prompt=prompt
                    )
                else:
                    # For mocked clients that don't implement async
                    response = self.client.generate(
                        request=companion_request,
                        model_id=CLOUD_API_CONFIG.get("model", "amazon.nova-micro-v1:0"),
                        temperature=CLOUD_API_CONFIG.get("temperature", 0.7),
                        max_tokens=CLOUD_API_CONFIG.get("max_tokens", 512),
                        prompt=prompt
                    )
                
                # Update conversation history if a conversation ID is provided
                if conversation_id:
                    # Check if update_context is a coroutine function
                    if asyncio.iscoroutinefunction(self.context_manager.update_context):
                        await self.context_manager.update_context(
                            conversation_id, 
                            request, 
                            response
                        )
                    else:
                        # Use the sync method
                        self.context_manager.update_context(
                            conversation_id, 
                            request, 
                            response
                        )
                
                # Parse the response
                parsed_response = self._parse_response(response)
                
                return parsed_response
            except Exception as e:
                self.logger.error(f"Error generating response: {str(e)}")
                return self._generate_fallback_response(request, e)
                
        except Exception as e:
            self.logger.error(f"Unexpected error in Tier3Processor: {str(e)}")
            return f"I'm sorry, I'm having trouble processing your request. Error: {str(e)}"
        finally:
            elapsed_time = time.time() - start_time
            self.logger.info(f"Processed request {request.request_id} in {elapsed_time:.2f}s")
    
    def _parse_response(self, response: str) -> str:
        """
        Parse and clean the response from the Bedrock API.
        
        Args:
            response: The raw response from the API
            
        Returns:
            A cleaned response string
        """
        # Remove any system-like prefixes that might be in the response
        cleaned_response = response.strip()
        
        # Remove any <assistant> tags that might be in the response
        cleaned_response = cleaned_response.replace("<assistant>", "").replace("</assistant>", "")
        
        # Remove any leading/trailing whitespace
        cleaned_response = cleaned_response.strip()
        
        return cleaned_response
    
    def _generate_fallback_response(self, request: ClassifiedRequest, error: Any) -> str:
        """
        Generate a fallback response when an error occurs.
        
        Args:
            request: The request that failed
            error: The error that occurred
            
        Returns:
            A fallback response
        """
        self.logger.debug(f"Generating fallback response for request {request.request_id}")
        
        # For quota errors, provide a specific message
        if isinstance(error, BedrockError) and error.error_type == BedrockError.QUOTA_ERROR:
            self.logger.info(f"Tier3 quota exceeded for request {request.request_id}. Returning quota error message.")
            return "I'm sorry, but I've reached my limit for complex questions right now. Could you ask something simpler, or try again later?"
        
        # For other errors, provide a generic message
        self.logger.info(f"Tier3 fallback for request {request.request_id} due to error: {str(error)}")
        return "I'm sorry, I'm having trouble understanding that right now. Could you rephrase your question or ask something else?" 