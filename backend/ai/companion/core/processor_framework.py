"""
Tokyo Train Station Adventure - Processor Framework

This module implements the tiered processing framework for the companion AI system.
It defines the processor interface and concrete implementations for each tier.
"""

import abc
import json
import logging
from typing import Dict, Any, Optional

from backend.ai.companion.core.models import (
    ClassifiedRequest,
    ProcessingTier
)
from backend.ai.companion.config import (
    LOCAL_MODEL_CONFIG,
    CLOUD_API_CONFIG
)


class Processor(abc.ABC):
    """
    Abstract base class for request processors.
    
    This class defines the interface that all processors must implement.
    """
    
    @abc.abstractmethod
    def process(self, request: ClassifiedRequest) -> str:
        """
        Process a classified request.
        
        Args:
            request: The classified request to process
            
        Returns:
            A string response
        """
        pass


class Tier1Processor(Processor):
    """
    Tier 1 processor that uses rule-based processing.
    
    This processor handles simple requests by matching them against
    predefined patterns and templates. It is the fastest and most
    efficient processor, but also the least flexible.
    """
    
    def __init__(self):
        """Initialize the Tier 1 processor."""
        self.logger = logging.getLogger(__name__)
    
    def process(self, request: ClassifiedRequest) -> str:
        """
        Process a request using rule-based processing.
        
        Args:
            request: The classified request to process
            
        Returns:
            A string response
        """
        self.logger.info(f"Processing request {request.request_id} with Tier 1 processor")
        
        # Create a prompt for the rule-based processor
        prompt = self._create_prompt(request)
        
        # In a real implementation, we would match the prompt against
        # predefined patterns and templates to generate a response
        
        # For now, return a simple response based on the intent
        intent = request.intent.value
        if "vocabulary" in intent:
            return "That word means 'ticket' in Japanese."
        elif "grammar" in intent:
            return "In Japanese, the particle 'wa' marks the topic of the sentence."
        elif "direction" in intent:
            return "The ticket machines are over there, to your right."
        elif "translation" in intent:
            return "Yes, that's correct! Good job!"
        else:
            return "I'm here to help you navigate the train station and learn Japanese."
    
    def _create_prompt(self, request: ClassifiedRequest) -> str:
        """
        Create a prompt for the rule-based processor.
        
        Args:
            request: The classified request
            
        Returns:
            A prompt string
        """
        # Extract relevant information from the request
        intent = request.intent.value
        player_input = request.player_input
        entities = request.extracted_entities
        
        # Create a prompt based on the intent and entities
        prompt = f"Intent: {intent}\nInput: {player_input}\n"
        
        # Add entity-specific information to the prompt
        if entities:
            prompt += "Entities:\n"
            for key, value in entities.items():
                prompt += f"- {key}: {value}\n"
        
        return prompt


class Tier2Processor(Processor):
    """
    Tier 2 processor that uses a local language model.
    
    This processor handles moderate requests by generating responses with a
    lightweight language model running locally. It is more flexible than
    the Tier 1 processor but less powerful than the Tier 3 processor.
    """
    
    def __init__(self):
        """Initialize the Tier 2 processor."""
        self.logger = logging.getLogger(__name__)
        self.client = self._create_ollama_client()
    
    def _create_ollama_client(self):
        """
        Create an Ollama client.
        
        This is a separate method to make it easier to mock in tests.
        
        Returns:
            An Ollama client
        """
        # This is a placeholder for the actual Ollama client
        # In a real implementation, we would import and configure the Ollama client
        class MockOllamaClient:
            def generate(self, prompt, **kwargs):
                return {"response": "This is a response from the local language model."}
        
        return MockOllamaClient()
    
    def process(self, request: ClassifiedRequest) -> str:
        """
        Process a request using a local language model.
        
        Args:
            request: The classified request to process
            
        Returns:
            A string response
        """
        self.logger.info(f"Processing request {request.request_id} with Tier 2 processor")
        
        # Create a prompt for the language model
        prompt = self._create_prompt(request)
        
        # Generate a response using the language model
        response = self.client.generate(
            prompt,
            model=LOCAL_MODEL_CONFIG["model_name"],
            max_tokens=LOCAL_MODEL_CONFIG["max_tokens"],
            temperature=LOCAL_MODEL_CONFIG["temperature"],
            top_p=LOCAL_MODEL_CONFIG["top_p"]
        )
        
        # Handle both dictionary and string responses (for testing)
        if isinstance(response, dict):
            return response.get("response", "")
        else:
            return response
    
    def _create_prompt(self, request: ClassifiedRequest) -> str:
        """
        Create a prompt for the language model based on the request.
        
        Args:
            request: The classified request
            
        Returns:
            A prompt string
        """
        # Extract relevant information from the request
        intent = request.intent.value
        player_input = request.player_input
        entities = request.extracted_entities
        
        # Create a prompt based on the intent and entities
        prompt = f"""You are a helpful bilingual dog companion in a Japanese train station.
You are assisting an English-speaking player who is learning Japanese.
Provide accurate, helpful responses about Japanese language and culture.

Player input: {player_input}
Intent: {intent}
"""
        
        # Add entity-specific information to the prompt
        if entities:
            prompt += "Entities:\n"
            for key, value in entities.items():
                prompt += f"- {key}: {value}\n"
        
        return prompt


class ProcessorFactory:
    """
    Factory for creating processors based on the processing tier.
    
    This class implements the Singleton pattern to ensure that only one
    instance of each processor is created.
    """
    
    _instance = None
    _processors = {}
    
    def __new__(cls):
        """Create a new instance of the factory if one doesn't exist."""
        if cls._instance is None:
            cls._instance = super(ProcessorFactory, cls).__new__(cls)
        return cls._instance
    
    def get_processor(self, tier: ProcessingTier) -> Processor:
        """
        Get a processor for the specified tier.
        
        Args:
            tier: The processing tier
            
        Returns:
            A processor for the specified tier
            
        Raises:
            ValueError: If the tier is not supported
        """
        # Check if we already have a processor for this tier
        if tier in self._processors:
            return self._processors[tier]
        
        # Create a new processor based on the tier
        if tier == ProcessingTier.TIER_1:
            processor = Tier1Processor()
        elif tier == ProcessingTier.TIER_2:
            # Import here to avoid circular imports
            from backend.ai.companion.tier2.tier2_processor import Tier2Processor as RealTier2Processor
            processor = RealTier2Processor()
        elif tier == ProcessingTier.TIER_3:
            # Import here to avoid circular imports
            from backend.ai.companion.tier3.tier3_processor import Tier3Processor as RealTier3Processor
            processor = RealTier3Processor()
        else:
            raise ValueError(f"Unsupported processing tier: {tier.name}")
        
        # Cache the processor for future use
        self._processors[tier] = processor
        
        return processor 