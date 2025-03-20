"""
Tokyo Train Station Adventure - Tier 2 Processor

This module implements the Tier 2 processor for the companion AI system.
It uses the Ollama client to generate responses using local language models.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple

from backend.ai.companion.core.models import ClassifiedRequest, ComplexityLevel, ProcessingTier
from backend.ai.companion.core.processor_framework import Processor, ProcessorFactory
from backend.ai.companion.tier2.ollama_client import OllamaClient, OllamaError
from backend.ai.companion.core.prompt_manager import PromptManager
from backend.ai.companion.core.conversation_manager import ConversationManager
from backend.ai.companion.core.context_manager import ContextManager, default_context_manager
from backend.ai.companion.tier2.response_parser import ResponseParser
from backend.ai.companion.utils.monitoring import ProcessorMonitor
from backend.ai.companion.utils.retry import RetryConfig, retry_async
from backend.ai.companion.config import get_config

logger = logging.getLogger(__name__)


class Tier2Processor(Processor):
    """
    Tier 2 processor for the companion AI system.
    
    This processor uses the Ollama client to generate responses using local
    language models. It selects the appropriate model based on the complexity
    of the request and handles errors gracefully.
    """
    
    # Default retry configuration
    DEFAULT_RETRY_CONFIG = RetryConfig(
        max_retries=3,
        base_delay=1.0,
        max_delay=10.0,
        backoff_factor=3.0,
        jitter=True,
        jitter_factor=0.2
    )
    
    def __init__(
        self, 
        retry_config: Optional[RetryConfig] = None,
        context_manager: Optional[ContextManager] = None
    ):
        """
        Initialize the Tier 2 processor.
        
        Args:
            retry_config: Configuration for retry behavior (optional)
            context_manager: Context manager for tracking conversation context (optional)
        """
        # Load configuration
        config = get_config('tier2', {})
        self.enabled = True if config is None else config.get('enabled', True)
        
        # Initialize OllamaClient with configuration
        if config is not None:
            self.ollama_client = OllamaClient(
                base_url=config.get('base_url'),
                default_model=config.get('default_model'),
                cache_enabled=config.get('cache_enabled'),
                cache_dir=config.get('cache_dir'),
                cache_ttl=config.get('cache_ttl'),
                max_cache_entries=config.get('max_cache_entries'),
                max_cache_size_mb=config.get('max_cache_size_mb')
            )
        else:
            self.ollama_client = OllamaClient()
        
        # Use the common PromptManager instead of PromptEngineering
        tier2_prompt_config = {
            'format_for_model': 'ollama',
            'optimize_prompt': False  # Tier2 doesn't need prompt optimization
        }
        self.prompt_manager = PromptManager(tier_specific_config=tier2_prompt_config)
        
        # Use the common ConversationManager
        tier2_conversation_config = {
            'max_history_size': 5  # Limit history size for tier2
        }
        self.conversation_manager = ConversationManager(tier_specific_config=tier2_conversation_config)
        
        # Use the common ContextManager
        self.context_manager = context_manager or default_context_manager
        
        self.response_parser = ResponseParser()
        self.monitor = ProcessorMonitor()
        self.retry_config = retry_config or self.DEFAULT_RETRY_CONFIG
        
        # Initialize conversation history storage
        self.conversation_histories = {}
        
        logger.debug("Initialized Tier2Processor with common components")
    
    async def process(self, request: ClassifiedRequest) -> str:
        """
        Process a request using the Ollama client.
        
        Args:
            request: The classified request to process
            
        Returns:
            The generated response
        """
        logger.info(f"Processing request {request.request_id} with Tier 2 processor")
        
        # Check if processor is enabled
        if not self.enabled:
            logger.warning("Tier 2 processor is disabled in configuration")
            raise Exception("Tier 2 processor is disabled in configuration")
            
        self.monitor.track_request("tier2", request.request_id)
        
        start_time = time.time()
        success = False
        
        try:
            # Get or create conversation history
            conversation_id = request.additional_params.get("conversation_id", request.request_id)
            if conversation_id not in self.conversation_histories:
                self.conversation_histories[conversation_id] = []
            conversation_history = self.conversation_histories[conversation_id]
            
            # Select the appropriate model based on complexity
            model = self._select_model(request.complexity)
            logger.info(f"Selected model {model} for request {request.request_id} with complexity {request.complexity.value}")
            
            # Create a prompt using the common prompt manager
            base_prompt = self.prompt_manager.create_prompt(request)
            
            # Detect conversation state and generate contextual prompt if needed
            state = self.conversation_manager.detect_conversation_state(request, conversation_history)
            prompt = self.conversation_manager.generate_contextual_prompt(
                request, 
                conversation_history, 
                state, 
                base_prompt
            )
            
            # Try to generate a response with retries for transient errors
            logger.info(f"Attempting to generate response for request {request.request_id} with model {model}")
            response, error = await self._generate_with_retries(request, model, prompt)
            
            # If we got a response, update conversation history and return it
            if response:
                logger.info(f"Successfully generated response for request {request.request_id} with model {model}")
                
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
                
                success = True
                return response
            
            # If we got a model-related error, try with a simpler model
            config = get_config('tier2', {})
            fallback_model = config.get('ollama', {}).get('default_model', "llama3")
            if error and error.is_model_related() and model != fallback_model:
                logger.warning(f"Model-related error with {model} for request {request.request_id}, falling back to simpler model")
                self.monitor.track_fallback("tier2", "simpler_model")
                
                logger.info(f"Attempting to generate response with fallback model {fallback_model} for request {request.request_id}")
                response, error = await self._generate_with_retries(request, fallback_model, prompt)
                
                # If we got a response with the fallback model, update conversation history and return it
                if response:
                    logger.info(f"Successfully generated response with fallback model for request {request.request_id}")
                    
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
                    
                    success = True
                    return response
            
            # If we still don't have a response, check if we should fall back to tier1
            if error and self._should_fallback_to_tier1(error):
                logger.warning(f"Falling back to tier1 for request {request.request_id} due to error: {error}")
                self.monitor.track_fallback("tier2", "tier1")
                
                # Get a tier1 processor and process the request
                tier1_processor = self._get_tier1_processor()
                response = await tier1_processor.process(request)
                
                logger.info(f"Successfully generated fallback response with tier1 for request {request.request_id}")
                success = True
                return response
            
            # If all else fails, generate a fallback response
            logger.warning(f"All attempts failed for request {request.request_id}, generating fallback response")
            self.monitor.track_fallback("tier2", "fallback")
            
            response = self._generate_fallback_response(request, error)
            success = True
            return response
            
        except Exception as e:
            logger.error(f"Error processing request {request.request_id}: {str(e)}")
            return self._generate_fallback_response(request, e)
            
        finally:
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"Processed request {request.request_id} in {duration:.2f}s (success: {success})")
            self.monitor.track_response_time("tier2", duration * 1000)  # Convert to milliseconds
            self.monitor.track_success("tier2", success)
    
    async def _generate_with_retries(
        self, 
        request: ClassifiedRequest, 
        model: str, 
        prompt: str
    ) -> Tuple[Optional[str], Optional[OllamaError]]:
        """
        Generate a response with retries for transient errors.
        
        Args:
            request: The request to generate a response for
            model: The model to use
            prompt: The prompt to use
            
        Returns:
            A tuple of (response, error) where response is the generated response
            (or None if generation failed) and error is the error that occurred
            (or None if generation succeeded)
        """
        # Create a retry configuration
        retry_config = RetryConfig(
            max_retries=self.retry_config.max_retries,
            base_delay=self.retry_config.base_delay,
            max_delay=self.retry_config.max_delay,
            backoff_factor=self.retry_config.backoff_factor,
            jitter=self.retry_config.jitter,
            jitter_factor=self.retry_config.jitter_factor,
            retry_exceptions=[OllamaError],
            retry_on=lambda e: isinstance(e, OllamaError) and e.is_transient()
        )
        
        # Define the function to generate and parse the response
        async def generate_and_parse():
            try:
                # Log the prompt being sent to the LLM
                logger.debug(f"Prompt sent to LLM: {prompt}")
                
                # Generate a response using the Ollama client
                raw_response = await self.ollama_client.generate(
                    request=request,
                    model=model,
                    temperature=0.7,
                    max_tokens=500,
                    prompt=prompt
                )
                
                logger.debug(f"Full response from LLM: {raw_response}")
                
                # Ensure raw_response is a dictionary
                if isinstance(raw_response, str):
                    logger.error("Received response is a string, expected a dictionary.")
                    return None, OllamaError("Invalid response format from LLM.")
                
                # Parse the response
                parsed_response = self.response_parser.parse_response(
                    raw_response=raw_response,
                    request=request,
                    format="markdown",
                    highlight_key_terms=False,
                    simplify=False,
                    add_learning_cues=False
                )
                
                logger.debug(f"Parsed response: {parsed_response}")
                
                # Extract Japanese text and pronunciation
                japanese_text = parsed_response.get("japanese", "")
                pronunciation = parsed_response.get("pronunciation", "")
                
                if not japanese_text or not pronunciation:
                    logger.warning("Missing Japanese text or pronunciation in the response.")
                
                return parsed_response
            except Exception as e:
                logger.error(f"Error in generate_and_parse: {str(e)}")
                raise
        
        try:
            # Use retry_async to call the function with retries
            response = await retry_async(generate_and_parse, config=retry_config)
            return response, None
        except OllamaError as e:
            # If we get here, all retries failed
            logger.warning(f"Failed to generate response after {retry_config.max_retries} retries: {str(e)}")
            self.monitor.track_error("tier2", e.error_type, str(e))
            return None, e
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error generating response: {str(e)}")
            self.monitor.track_error("tier2", "unexpected", str(e))
            return None, OllamaError(str(e), OllamaError.UNKNOWN_ERROR)
    
    def _select_model(self, complexity: ComplexityLevel) -> str:
        """
        Select an appropriate model based on the complexity of the request.
        
        Args:
            complexity: The complexity of the request
            
        Returns:
            The name of the model to use
        """
        # Get configuration
        config = get_config('tier2', {})
        
        # Get models from configuration
        default_model = config.get('ollama', {}).get('default_model', "llama3")
        complex_model = config.get('ollama', {}).get('complex_model', "llama3:8b")
        
        if complexity == ComplexityLevel.SIMPLE:
            return default_model
        elif complexity == ComplexityLevel.MODERATE:
            return default_model
        else:  # COMPLEX
            return complex_model
    
    def _generate_fallback_response(self, request: ClassifiedRequest, error: Any) -> str:
        """
        Generate a fallback response when an error occurs.
        
        Args:
            request: The request that failed
            error: The error that occurred
            
        Returns:
            A fallback response
        """
        # Try to generate a response using the response parser
        try:
            return self.response_parser._create_fallback_response(request)
        except Exception as e:
            logger.error(f"Error creating fallback response: {str(e)}")
            
            # If that fails, return a generic response
            if request.intent == IntentCategory.VOCABULARY_HELP:
                return "I'm sorry, I couldn't find information about that word. Could you try asking about a different word?"
            elif request.intent == IntentCategory.GRAMMAR_EXPLANATION:
                return "I'm sorry, I couldn't explain that grammar point right now. Could you try asking about a simpler grammar point?"
            elif request.intent == IntentCategory.DIRECTION_GUIDANCE:
                return "I'm sorry, I couldn't provide directions right now. Could you try asking in a different way?"
            elif request.intent == IntentCategory.TRANSLATION_CONFIRMATION:
                return "I'm sorry, I couldn't confirm that translation right now. Could you try a simpler phrase?"
            else:
                return "I'm sorry, I couldn't understand that request. Could you try asking in a different way?"
    
    def _should_fallback_to_tier1(self, error: Any) -> bool:
        """
        Determine if we should fall back to tier1 based on the error.
        
        Args:
            error: The error that occurred
            
        Returns:
            True if we should fall back to tier1, False otherwise
        """
        # If it's an OllamaError, check the error type
        if isinstance(error, OllamaError):
            # Fall back to tier1 for connection errors, memory errors, and model errors
            if error.error_type in [
                OllamaError.CONNECTION_ERROR,
                OllamaError.MEMORY_ERROR,
                OllamaError.MODEL_ERROR
            ]:
                return True
        
        # For other errors, don't fall back to tier1
        return False
    
    def _get_tier1_processor(self):
        """
        Get a tier1 processor for fallback.
        
        Returns:
            A tier1 processor
        """
        # Get a tier1 processor from the factory
        factory = ProcessorFactory()
        return factory.get_processor(ProcessingTier.TIER_1) 