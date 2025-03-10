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
        
        try:
            # Select the appropriate model based on complexity
            model = self._select_model(request.complexity)
            
            # Create a prompt using the prompt engineering module
            prompt = self.prompt_engineering.create_prompt(request)
            
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
            return parsed_response
            
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