"""
Tokyo Train Station Adventure - Tier 2 Processor

This module implements the Tier 2 processor for the companion AI system.
It uses the Ollama client to generate responses using local language models.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple

from backend.ai.companion.core.models import ClassifiedRequest, ComplexityLevel
from backend.ai.companion.core.processor_framework import Processor
from backend.ai.companion.tier2.ollama_client import OllamaClient, OllamaError
from backend.ai.companion.tier2.prompt_engineering import PromptEngineering
from backend.ai.companion.tier2.response_parser import ResponseParser

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
        
        # Select the appropriate model based on complexity
        model = self._select_model(request.complexity)
        
        # Create a prompt using the prompt engineering module
        prompt = self.prompt_engineering.create_prompt(request)
        
        # Try to generate a response with retries for transient errors
        response, error = await self._generate_with_retries(request, model, prompt)
        
        # If we got a response, return it
        if response:
            return response
        
        # If we got a model-related error, try with a simpler model
        if error and error.is_model_related() and model != "llama3":
            logger.warning(f"Model-related error with {model}, falling back to simpler model")
            fallback_model = "llama3"
            response, error = await self._generate_with_retries(request, fallback_model, prompt)
            
            # If we got a response with the fallback model, return it
            if response:
                return response
        
        # If we still don't have a response, return a fallback response
        if error:
            return self._generate_fallback_response(request, error)
        else:
            return self._generate_fallback_response(request, "Unknown error")
    
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
                
                # If the error is transient and we haven't exceeded the maximum retries,
                # wait and try again
                if e.is_transient() and retries < self.MAX_RETRIES:
                    retry_delay = self.RETRY_DELAYS[retries]
                    logger.info(f"Transient error, retrying in {retry_delay} seconds")
                    time.sleep(retry_delay)
                    retries += 1
                else:
                    # Non-transient error or maximum retries exceeded
                    break
                    
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                last_error = OllamaError(str(e))
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