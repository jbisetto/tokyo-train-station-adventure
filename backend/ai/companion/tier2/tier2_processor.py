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
from backend.ai.companion.tier2.prompt_engineering import PromptEngineering
from backend.ai.companion.tier2.response_parser import ResponseParser
from backend.ai.companion.utils.monitoring import ProcessorMonitor
from backend.ai.companion.utils.retry import RetryConfig, retry_async

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
    
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        """
        Initialize the Tier 2 processor.
        
        Args:
            retry_config: Configuration for retry behavior (optional)
        """
        self.ollama_client = OllamaClient()
        self.prompt_engineering = PromptEngineering()
        self.response_parser = ResponseParser()
        self.monitor = ProcessorMonitor()
        self.retry_config = retry_config or self.DEFAULT_RETRY_CONFIG
        logger.debug("Initialized Tier2Processor")
    
    async def process(self, request: ClassifiedRequest) -> str:
        """
        Process a request using the Ollama client.
        
        Args:
            request: The classified request to process
            
        Returns:
            The generated response
        """
        logger.info(f"Processing request {request.request_id} with Tier 2 processor")
        self.monitor.track_request("tier2", request.request_id)
        
        start_time = time.time()
        success = False
        
        try:
            # Select the appropriate model based on complexity
            model = self._select_model(request.complexity)
            logger.info(f"Selected model {model} for request {request.request_id} with complexity {request.complexity.value}")
            
            # Create a prompt using the prompt engineering module
            prompt = self.prompt_engineering.create_prompt(request)
            
            # Try to generate a response with retries for transient errors
            logger.info(f"Attempting to generate response for request {request.request_id} with model {model}")
            response, error = await self._generate_with_retries(request, model, prompt)
            
            # If we got a response, return it
            if response:
                logger.info(f"Successfully generated response for request {request.request_id} with model {model}")
                success = True
                return response
            
            # If we got a model-related error, try with a simpler model
            if error and error.is_model_related() and model != "llama3":
                logger.warning(f"Model-related error with {model} for request {request.request_id}, falling back to simpler model")
                self.monitor.track_fallback("tier2", "simpler_model")
                
                fallback_model = "llama3"
                logger.info(f"Attempting to generate response with fallback model {fallback_model} for request {request.request_id}")
                response, error = await self._generate_with_retries(request, fallback_model, prompt)
                
                # If we got a response with the fallback model, return it
                if response:
                    logger.info(f"Successfully generated response with fallback model {fallback_model} for request {request.request_id}")
                    success = True
                    return response
            
            # If we still don't have a response, return a fallback response
            if error:
                logger.warning(f"Failed to generate response for request {request.request_id} after all attempts. Error: {error}")
                return self._generate_fallback_response(request, error)
            else:
                logger.warning(f"Failed to generate response for request {request.request_id} with unknown error")
                return self._generate_fallback_response(request, "Unknown error")
        finally:
            # Track response time and success
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            self.monitor.track_response_time("tier2", response_time_ms)
            self.monitor.track_success("tier2", success)
            
            # Log metrics summary periodically (every 100 requests)
            if self.monitor.get_metrics()['requests'].get('tier2', 0) % 100 == 0:
                self.monitor.log_metrics_summary()
                self.monitor.save_metrics()
    
    async def _generate_with_retries(
        self, 
        request: ClassifiedRequest, 
        model: str, 
        prompt: str
    ) -> Tuple[Optional[str], Optional[OllamaError]]:
        """
        Generate a response with retries for transient errors.
        
        Args:
            request: The request to process
            model: The model to use
            prompt: The prompt to send to the model
            
        Returns:
            A tuple of (response, error) where response is the generated response
            (or None if generation failed) and error is the last error encountered
            (or None if generation succeeded)
        """
        # Create a retry configuration that only retries on transient errors
        retry_config = RetryConfig(
            max_retries=self.retry_config.max_retries,
            base_delay=self.retry_config.base_delay,
            max_delay=self.retry_config.max_delay,
            backoff_factor=self.retry_config.backoff_factor,
            jitter=self.retry_config.jitter,
            jitter_factor=self.retry_config.jitter_factor,
            retry_on=lambda e: isinstance(e, OllamaError) and e.is_transient()
        )
        
        try:
            # Use the retry_async utility to handle retries
            async def generate_and_parse():
                # Generate a response using the Ollama client
                raw_response = await self.ollama_client.generate(
                    request=request,
                    model=model,
                    temperature=0.7,
                    max_tokens=500,
                    prompt=prompt
                )
                
                # Parse and enhance the response
                parsed_response = self.response_parser.parse_response(
                    raw_response=raw_response,
                    request=request,
                    format="markdown",
                    highlight_key_terms=True,
                    simplify=request.complexity == ComplexityLevel.SIMPLE,
                    add_learning_cues=True
                )
                
                return parsed_response
            
            # Attempt to generate a response with retries
            response = await retry_async(
                generate_and_parse,
                config=retry_config
            )
            
            # Track successful retries
            logger.debug(f"Generated response for request {request.request_id}")
            return response, None
            
        except OllamaError as e:
            # Track the error
            error_type = e.error_type if hasattr(e, 'error_type') else "unknown_error"
            self.monitor.track_error("tier2", error_type, str(e))
            
            # Log the error
            logger.error(f"Error generating response after retries: {e}")
            
            # Return the error
            return None, e
            
        except Exception as e:
            # Track unexpected errors
            self.monitor.track_error("tier2", "unexpected_error", str(e))
            
            # Log the error
            logger.error(f"Unexpected error: {e}")
            
            # Convert to OllamaError and return
            error = OllamaError(str(e))
            return None, error
    
    def _select_model(self, complexity: ComplexityLevel) -> str:
        """
        Select the appropriate model based on complexity.
        
        Args:
            complexity: The complexity level of the request
            
        Returns:
            The name of the model to use
        """
        if complexity == ComplexityLevel.COMPLEX:
            return "llama3:16b"  # Use a larger model for complex requests
        else:
            return "llama3"  # Use the default model for simple/moderate requests
    
    def _generate_fallback_response(self, request: ClassifiedRequest, error: Any) -> str:
        """
        Generate a fallback response when an error occurs.
        
        Args:
            request: The request that failed
            error: The error that occurred
            
        Returns:
            A fallback response
        """
        logger.debug(f"Generating fallback response for request {request.request_id}")
        
        # Determine if we should fall back to Tier 1
        should_fallback_to_tier1 = self._should_fallback_to_tier1(error)
        
        # If we should fall back to Tier 1, use the Tier 1 processor
        if should_fallback_to_tier1:
            logger.info(f"Falling back to Tier 1 processor for request {request.request_id} due to error: {error}")
            self.monitor.track_fallback("tier2", "tier1")
            
            # Create a modified request with Tier 1 as the processing tier
            tier1_request = ClassifiedRequest(
                request_id=request.request_id,
                player_input=request.player_input,
                request_type=request.request_type,
                timestamp=request.timestamp,
                intent=request.intent,
                complexity=ComplexityLevel.SIMPLE,  # Force simple complexity for Tier 1
                processing_tier=ProcessingTier.TIER_1,
                confidence=request.confidence,
                extracted_entities=request.extracted_entities
            )
            
            # Get the Tier 1 processor and process the request
            tier1_processor = self._get_tier1_processor()
            try:
                # Track the request to Tier 1
                self.monitor.track_request("tier1", request.request_id)
                
                logger.info(f"Processing request {request.request_id} with Tier 1 processor as fallback")
                start_time = time.time()
                response = tier1_processor.process(tier1_request)
                
                # Track response time and success for Tier 1
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000
                self.monitor.track_response_time("tier1", response_time_ms)
                self.monitor.track_success("tier1", True)
                
                logger.info(f"Successfully processed request {request.request_id} with Tier 1 processor as fallback")
                return response
            except Exception as e:
                logger.error(f"Error in Tier 1 fallback for request {request.request_id}: {str(e)}")
                
                # Track the error and failure for Tier 1
                self.monitor.track_error("tier1", "fallback_error", str(e))
                self.monitor.track_success("tier1", False)
                
                # If Tier 1 also fails, continue to the default fallback responses
        else:
            logger.info(f"Not falling back to Tier 1 for request {request.request_id}, using default fallback response")
        
        # If we shouldn't fall back to Tier 1 or Tier 1 failed, use the default fallback responses
        # Track the fallback to default response
        self.monitor.track_fallback("tier2", "default_response")
        
        # If the error is an OllamaError, use its error type to generate a more specific response
        if isinstance(error, OllamaError):
            if error.error_type == OllamaError.CONNECTION_ERROR:
                logger.info(f"Returning connection error fallback response for request {request.request_id}")
                return (
                    "I'm sorry, I'm having a connection issue with my language model service. "
                    "Please try again in a moment."
                )
            elif error.error_type == OllamaError.MODEL_ERROR:
                logger.info(f"Returning model error fallback response for request {request.request_id}")
                return (
                    "I'm sorry, there seems to be an issue with the language model I'm trying to use. "
                    "Please try a simpler question or try again later."
                )
            elif error.error_type == OllamaError.TIMEOUT_ERROR:
                logger.info(f"Returning timeout error fallback response for request {request.request_id}")
                return (
                    "I'm sorry, generating a response is taking too long. "
                    "Please try asking a simpler question or try again later."
                )
            elif error.error_type == OllamaError.CONTENT_ERROR:
                logger.info(f"Returning content error fallback response for request {request.request_id}")
                return (
                    "I'm sorry, I'm unable to provide a response to that question due to content restrictions. "
                    "Please try asking something else."
                )
            elif error.error_type == OllamaError.MEMORY_ERROR:
                logger.info(f"Returning memory error fallback response for request {request.request_id}")
                return (
                    "I'm sorry, the language model is currently using too much memory. "
                    "Please try asking a simpler question or try again later."
                )
        
        # Default fallback response
        logger.info(f"Returning default fallback response for request {request.request_id}")
        return (
            "I'm sorry, I'm having trouble processing your request at the moment. "
            "Could you try rephrasing your question or asking something else?"
        )
    
    def _should_fallback_to_tier1(self, error: Any) -> bool:
        """
        Determine if we should fall back to Tier 1 based on the error.
        
        Args:
            error: The error that occurred
            
        Returns:
            True if we should fall back to Tier 1, False otherwise
        """
        # Fall back to Tier 1 for certain error types
        if isinstance(error, OllamaError):
            # For connection, timeout, or memory errors, Tier 1 is a good fallback
            # since these are issues with the LLM service, not the request itself
            if error.error_type in [
                OllamaError.CONNECTION_ERROR,
                OllamaError.TIMEOUT_ERROR,
                OllamaError.MEMORY_ERROR
            ]:
                logger.debug(f"Deciding to fall back to Tier 1 due to LLM service issue: {error.error_type}")
                return True
                
            # For model errors, we might want to fall back to Tier 1 if we've already
            # tried a simpler model and it still failed
            if error.error_type == OllamaError.MODEL_ERROR:
                logger.debug(f"Deciding to fall back to Tier 1 due to model error")
                return True
                
            # For content errors, we probably don't want to fall back to Tier 1
            # since the request itself might be problematic
            if error.error_type == OllamaError.CONTENT_ERROR:
                logger.debug(f"Deciding NOT to fall back to Tier 1 due to content error")
                return False
        
        # For unknown errors, fall back to Tier 1 as a safe option
        logger.debug(f"Deciding to fall back to Tier 1 due to unknown error: {error}")
        return True
    
    def _get_tier1_processor(self):
        """
        Get the Tier 1 processor.
        
        Returns:
            The Tier 1 processor
        """
        # Use the processor factory to get the Tier 1 processor
        processor_factory = ProcessorFactory()
        return processor_factory.get_processor(ProcessingTier.TIER_1) 