"""
Tokyo Train Station Adventure - Tier 2 Processor

This module implements the Tier 2 processor for the companion AI system.
It uses the Ollama client to generate responses using local language models.
"""

import logging
from typing import Dict, Any, Optional

from backend.ai.companion.core.models import ClassifiedRequest, ComplexityLevel
from backend.ai.companion.core.processor_framework import Processor
from backend.ai.companion.tier2.ollama_client import OllamaClient, OllamaError

logger = logging.getLogger(__name__)


class Tier2Processor(Processor):
    """
    Tier 2 processor for the companion AI system.
    
    This processor uses the Ollama client to generate responses using local
    language models. It selects the appropriate model based on the complexity
    of the request and handles errors gracefully.
    """
    
    def __init__(self):
        """Initialize the Tier 2 processor."""
        self.ollama_client = OllamaClient()
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
        
        try:
            # Select the appropriate model based on complexity
            model = self._select_model(request.complexity)
            
            # Generate a response using the Ollama client
            response = await self.ollama_client.generate(
                request=request,
                model=model,
                temperature=0.7,
                max_tokens=500
            )
            
            logger.debug(f"Generated response for request {request.request_id}")
            return response
            
        except OllamaError as e:
            logger.error(f"Error generating response: {e}")
            return self._generate_fallback_response(request, str(e))
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return self._generate_fallback_response(request, str(e))
    
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
    
    def _generate_fallback_response(self, request: ClassifiedRequest, error_message: str) -> str:
        """
        Generate a fallback response when an error occurs.
        
        Args:
            request: The request that failed
            error_message: The error message
            
        Returns:
            A fallback response
        """
        logger.debug(f"Generating fallback response for request {request.request_id}")
        
        return (
            "I'm sorry, I'm having trouble processing your request at the moment. "
            "Could you try rephrasing your question or asking something else?"
        ) 