"""
Tokyo Train Station Adventure - Tier 3 Processor

This module implements the Tier 3 processor for the companion AI system,
which uses Amazon Bedrock for generating responses to complex requests.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List

from backend.ai.companion.core.models import (
    ClassifiedRequest,
    CompanionRequest,
    ProcessingTier,
    ComplexityLevel
)
from backend.ai.companion.core.processor_framework import Processor
from backend.ai.companion.tier3.bedrock_client import BedrockClient, BedrockError
from backend.ai.companion.tier3.usage_tracker import UsageTracker, default_tracker
from backend.ai.companion.core.context_manager import ContextManager, default_context_manager
from backend.ai.companion.core.conversation_manager import ConversationManager
from backend.ai.companion.core.prompt_manager import PromptManager
from backend.ai.companion.tier3.scenario_detection import ScenarioDetector, ScenarioType
from backend.ai.companion.config import CLOUD_API_CONFIG


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
            usage_tracker: Optional usage tracker for monitoring API usage
            context_manager: Optional context manager for tracking conversation context
        """
        self.logger = logging.getLogger(__name__)
        self.client = self._create_bedrock_client(usage_tracker)
        
        # Use the common ContextManager
        self.context_manager = context_manager or default_context_manager
        
        # Use the common ConversationManager with tier3-specific config
        tier3_conversation_config = {
            'max_history_size': 10  # Tier3 can handle more history
        }
        self.conversation_manager = ConversationManager(tier_specific_config=tier3_conversation_config)
        
        # Use the common PromptManager with tier3-specific config
        tier3_prompt_config = {
            'format_for_model': 'bedrock',
            'optimize_prompt': True,
            'max_prompt_tokens': 1000,
            'additional_instructions': "\nPlease provide a detailed and helpful response."
        }
        self.prompt_manager = PromptManager(tier_specific_config=tier3_prompt_config)
        
        # Keep the scenario detector for tier3-specific functionality
        self.scenario_detector = ScenarioDetector()
        
        # Initialize conversation history storage
        self.conversation_histories = {}
        
        self.logger.info("Tier 3 processor initialized with Bedrock client and common components")
    
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
    
    def process(self, request: ClassifiedRequest) -> str:
        """
        Process a request using Amazon Bedrock.
        
        Args:
            request: The classified request to process
            
        Returns:
            A string response
            
        Raises:
            Exception: If there is an error processing the request
        """
        self.logger.info(f"Processing request {request.request_id} with Tier 3 processor")
        
        # Create a companion request from the classified request
        companion_request = CompanionRequest(
            request_id=request.request_id,
            player_input=request.player_input,
            request_type=request.request_type,
            timestamp=request.timestamp
        )
        
        try:
            # Get or create conversation history
            conversation_id = request.additional_params.get("conversation_id", request.request_id)
            if conversation_id not in self.conversation_histories:
                self.conversation_histories[conversation_id] = []
            conversation_history = self.conversation_histories[conversation_id]
            
            # First, try to detect and handle specific scenarios for complex requests
            if request.complexity == ComplexityLevel.COMPLEX:
                # Only attempt scenario detection if we have a conversation_id
                if "conversation_id" in request.additional_params:
                    # Get the context
                    context = self.context_manager.get_context(request.additional_params["conversation_id"])
                    
                    # Only proceed with scenario detection if we have a valid context
                    if context:
                        # Detect the scenario
                        scenario_type = self.scenario_detector.detect_scenario(request)
                        
                        if scenario_type != ScenarioType.UNKNOWN:
                            self.logger.info(f"Detected scenario {scenario_type.value} for request {request.request_id}")
                            
                            # Handle the scenario
                            response = self.scenario_detector.handle_scenario(
                                request,
                                self.context_manager,
                                self.client
                            )
                            
                            # Update conversation history
                            self.conversation_histories[conversation_id] = self.conversation_manager.add_to_history(
                                conversation_history,
                                request,
                                response
                            )
                            
                            # Update context
                            self.context_manager.update_context(
                                request.additional_params["conversation_id"],
                                request,
                                response
                            )
                            
                            self.logger.info(f"Generated response for scenario {scenario_type.value}")
                            return response
            
            # For requests that don't match a specific scenario, use the common components
            
            # Create a base prompt using the common prompt manager
            base_prompt = self.prompt_manager.create_prompt(request)
            
            # Detect conversation state and generate contextual prompt
            state = self.conversation_manager.detect_conversation_state(request, conversation_history)
            prompt = self.conversation_manager.generate_contextual_prompt(
                request, 
                conversation_history, 
                state, 
                base_prompt
            )
            
            # Generate a response using the Bedrock client
            try:
                # Try to get the running event loop
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # If no loop is running, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                should_close_loop = True
            else:
                should_close_loop = False
            
            # Define a function to generate a response
            async def generate_response():
                return await self.client.generate(
                    request=companion_request,
                    model_id=CLOUD_API_CONFIG.get("model", "amazon.nova-micro-v1:0"),
                    temperature=CLOUD_API_CONFIG.get("temperature", 0.7),
                    max_tokens=CLOUD_API_CONFIG.get("max_tokens", 512),
                    prompt=prompt
                )
            
            try:
                # Generate the response
                response = loop.run_until_complete(generate_response())
            finally:
                # Only close the loop if we created it
                if should_close_loop:
                    loop.close()
            
            # Parse and clean the response
            response = self._parse_response(response)
            
            # Update conversation history
            self.conversation_histories[conversation_id] = self.conversation_manager.add_to_history(
                conversation_history,
                request,
                response
            )
            
            # Update context if we have a conversation_id in additional_params
            if "conversation_id" in request.additional_params:
                self.context_manager.update_context(
                    request.additional_params["conversation_id"],
                    request,
                    response
                )
            
            self.logger.info(f"Generated response for request {request.request_id}")
            return response
            
        except BedrockError as e:
            self.logger.error(f"Error generating response with Bedrock: {str(e)}")
            return self._generate_fallback_response(request, e)
            
        except Exception as e:
            self.logger.error(f"Unexpected error in Tier 3 processor: {str(e)}")
            return f"I'm sorry, I encountered an unexpected error: {str(e)}"
    
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