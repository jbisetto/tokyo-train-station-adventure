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

logger = logging.getLogger(__name__)


class Tier2Processor(Processor):
    """
    Tier 2 processor for the companion AI system.
    
    This processor uses the Ollama client to generate responses using local
    language models. It selects the appropriate model based on the complexity
    of the request and handles errors gracefully.
    """
    
    # Maximum number of retries for transient errors
    MAX_RETRIES = 3
    
    # Delay between retries in seconds (exponential backoff)
    RETRY_DELAYS = [1, 3, 9]
    
    def __init__(self):
        """Initialize the Tier 2 processor."""
        self.ollama_client = OllamaClient()
        self.prompt_engineering = PromptEngineering()
        self.response_parser = ResponseParser()
        self.monitor = ProcessorMonitor()
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
            
            # Create a prompt using the prompt engineering module
            prompt = self.prompt_engineering.create_prompt(request)
            
            # Try to generate a response with retries for transient errors
            response, error = await self._generate_with_retries(request, model, prompt)
            
            # If we got a response, return it
            if response:
                success = True
                return response
            
            # If we got a model-related error, try with a simpler model
            if error and error.is_model_related() and model != "llama3":
                logger.warning(f"Model-related error with {model}, falling back to simpler model")
                self.monitor.track_fallback("tier2", "simpler_model")
                
                fallback_model = "llama3"
                response, error = await self._generate_with_retries(request, fallback_model, prompt)
                
                # If we got a response with the fallback model, return it
                if response:
                    success = True
                    return response
            
            # If we still don't have a response, return a fallback response
            if error:
                return self._generate_fallback_response(request, error)
            else:
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
        retries = 0
        last_error = None
        
        while retries <= self.MAX_RETRIES:
            try:
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
                
                logger.debug(f"Generated response for request {request.request_id}")
                return parsed_response, None
                
            except OllamaError as e:
                logger.error(f"Error generating response: {e}")
                last_error = e
                
                # Track the error
                error_type = e.error_type if hasattr(e, 'error_type') else "unknown_error"
                self.monitor.track_error("tier2", error_type, str(e))
                
                # If the error is transient and we haven't exceeded the maximum retries,
                # wait and try again
                if e.is_transient() and retries < self.MAX_RETRIES:
                    retry_delay = self.RETRY_DELAYS[retries]
                    logger.info(f"Transient error, retrying in {retry_delay} seconds")
                    
                    # Track the retry
                    self.monitor.track_retry("tier2", retries + 1)
                    
                    time.sleep(retry_delay)
                    retries += 1
                else:
                    # Non-transient error or maximum retries exceeded
                    break
                    
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                last_error = OllamaError(str(e))
                
                # Track the error
                self.monitor.track_error("tier2", "unexpected_error", str(e))
                
                break
        
        return None, last_error
    
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
            logger.info(f"Falling back to Tier 1 processor for request {request.request_id}")
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
                
                start_time = time.time()
                response = tier1_processor.process(tier1_request)
                
                # Track response time and success for Tier 1
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000
                self.monitor.track_response_time("tier1", response_time_ms)
                self.monitor.track_success("tier1", True)
                
                return response
            except Exception as e:
                logger.error(f"Error in Tier 1 fallback: {str(e)}")
                
                # Track the error and failure for Tier 1
                self.monitor.track_error("tier1", "fallback_error", str(e))
                self.monitor.track_success("tier1", False)
                
                # If Tier 1 also fails, continue to the default fallback responses
        
        # If we shouldn't fall back to Tier 1 or Tier 1 failed, use the default fallback responses
        # Track the fallback to default response
        self.monitor.track_fallback("tier2", "default_response")
        
        # If the error is an OllamaError, use its error type to generate a more specific response
        if isinstance(error, OllamaError):
            if error.error_type == OllamaError.CONNECTION_ERROR:
                return (
                    "I'm sorry, I'm having a connection issue with my language model service. "
                    "Please try again in a moment."
                )
            elif error.error_type == OllamaError.MODEL_ERROR:
                return (
                    "I'm sorry, there seems to be an issue with the language model I'm trying to use. "
                    "Please try a simpler question or try again later."
                )
            elif error.error_type == OllamaError.TIMEOUT_ERROR:
                return (
                    "I'm sorry, generating a response is taking too long. "
                    "Please try asking a simpler question or try again later."
                )
            elif error.error_type == OllamaError.CONTENT_ERROR:
                return (
                    "I'm sorry, I'm unable to provide a response to that question due to content restrictions. "
                    "Please try asking something else."
                )
            elif error.error_type == OllamaError.MEMORY_ERROR:
                return (
                    "I'm sorry, the language model is currently using too much memory. "
                    "Please try asking a simpler question or try again later."
                )
        
        # Default fallback response
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
                return True
                
            # For model errors, we might want to fall back to Tier 1 if we've already
            # tried a simpler model and it still failed
            if error.error_type == OllamaError.MODEL_ERROR:
                return True
                
            # For content errors, we probably don't want to fall back to Tier 1
            # since the request itself might be problematic
            if error.error_type == OllamaError.CONTENT_ERROR:
                return False
        
        # For unknown errors, fall back to Tier 1 as a safe option
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