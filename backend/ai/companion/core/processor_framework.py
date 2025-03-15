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
from backend.ai.companion.tier1.template_system import TemplateSystem
from backend.ai.companion.tier1.pattern_matching import PatternMatcher
from backend.ai.companion.tier1.decision_trees import DecisionTreeManager, DecisionTreeProcessor


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
        
        # Initialize the template system
        self.template_system = TemplateSystem()
        
        # Initialize the pattern matcher
        self.pattern_matcher = PatternMatcher()
        
        # Initialize the decision tree system
        self.tree_manager = DecisionTreeManager()
        self.tree_processor = DecisionTreeProcessor(self.tree_manager)
        
        # Load default trees
        self._load_default_trees()
    
    def process(self, request: ClassifiedRequest) -> str:
        """
        Process a request using rule-based processing.
        
        Args:
            request: The classified request to process
            
        Returns:
            A string response
        """
        self.logger.info(f"Processing request {request.request_id} with Tier 1 processor")
        
        # Create a companion request from the classified request
        companion_request = self._create_companion_request(request)
        
        # First, try to process the request using decision trees for multi-turn interactions
        conversation_state = request.additional_params.get("conversation_state")
        if conversation_state:
            try:
                response, new_state = self.tree_processor.process_request(companion_request, conversation_state)
                # Store the new state in the request for future use
                request.additional_params["conversation_state"] = new_state
                if response:
                    return response
            except Exception as e:
                self.logger.error(f"Error processing request with decision tree: {e}")
                # Continue with other processing methods if decision tree fails
        
        # If no decision tree handled the request, try pattern matching
        match_result = self.pattern_matcher.match(request.player_input)
        if match_result.get("matched", False):
            # Extract entities from the match result
            entities = self.pattern_matcher.extract_entities(match_result)
            # Update the request's extracted entities
            request.extracted_entities.update(entities)
            
            # Use the template system to generate a response
            try:
                return self.template_system.process_request(request)
            except Exception as e:
                self.logger.error(f"Error processing request with template system: {e}")
                # Continue with fallback response if template system fails
        
        # If no pattern matched, fall back to a simple response based on intent
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
    
    def _create_companion_request(self, request: ClassifiedRequest) -> Any:
        """
        Create a companion request from a classified request.
        
        Args:
            request: The classified request
            
        Returns:
            A companion request
        """
        from backend.ai.companion.core.models import CompanionRequest
        
        # Create a new CompanionRequest with the same basic fields
        companion_request = CompanionRequest(
            request_id=request.request_id,
            player_input=request.player_input,
            request_type=request.request_type,
            timestamp=request.timestamp,
            game_context=request.game_context,
            additional_params=request.additional_params.copy()  # Copy additional params
        )
        
        return companion_request
    
    def _load_default_trees(self):
        """Load default decision trees."""
        try:
            # Load trees from the trees directory
            import os
            import json
            
            trees_dir = os.path.join(os.path.dirname(__file__), "../tier1/trees")
            if os.path.exists(trees_dir):
                for filename in os.listdir(trees_dir):
                    if filename.endswith(".json"):
                        try:
                            file_path = os.path.join(trees_dir, filename)
                            self.tree_manager.load_tree_from_file(file_path)
                            self.logger.info(f"Loaded decision tree from {file_path}")
                        except Exception as e:
                            self.logger.error(f"Error loading decision tree {filename}: {e}")
        except Exception as e:
            self.logger.error(f"Error loading default trees: {e}")
    
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
    
    This class is responsible for creating and caching processors for different tiers.
    It ensures that only one instance of each processor type is created.
    """
    
    _instance = None
    _processors = {}
    
    def __new__(cls):
        """Create a new instance of the factory if one doesn't exist."""
        if cls._instance is None:
            cls._instance = super(ProcessorFactory, cls).__new__(cls)
            cls._instance.logger = logging.getLogger(__name__)
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
            self.logger.debug(f"Using cached {tier.name} processor")
            return self._processors[tier]
        
        # Create a new processor based on the tier
        self.logger.info(f"Creating new {tier.name} processor")
        
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
            self.logger.error(f"Unsupported processing tier: {tier.name}")
            raise ValueError(f"Unsupported processing tier: {tier.name}")
        
        # Cache the processor for future use
        self._processors[tier] = processor
        self.logger.debug(f"Cached {tier.name} processor for future use")
        
        return processor 