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
    
    This processor handles simple requests using templates and pattern matching.
    It is the most efficient processor but has limited flexibility.
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
        
        # For now, return a simple response based on the intent and entities
        # This will be replaced with a more sophisticated template system in the future
        
        if request.intent.value == "vocabulary_help" and "word" in request.extracted_entities:
            word = request.extracted_entities["word"]
            return f"'{word}' is a Japanese word that means 'ticket'. It's written as '切符' in kanji."
        
        elif request.intent.value == "grammar_explanation" and "grammar_point" in request.extracted_entities:
            grammar_point = request.extracted_entities["grammar_point"]
            return f"The grammar point '{grammar_point}' is used to mark the subject of a sentence in Japanese."
        
        elif request.intent.value == "direction_guidance" and "location" in request.extracted_entities:
            location = request.extracted_entities["location"]
            return f"To get to {location}, please follow the signs ahead and turn right at the main concourse."
        
        elif request.intent.value == "translation_confirmation":
            return "This sign says 'Exit' in Japanese. It's pronounced 'deguchi'."
        
        else:  # general_hint or fallback
            return "I'm here to help you navigate the station. What would you like to know?"


class Tier2Processor(Processor):
    """
    Tier 2 processor that uses a local LLM (Ollama with DeepSeek 7B).
    
    This processor handles moderately complex requests by generating responses
    with a local language model. It balances efficiency and flexibility.
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
                return f"This is a response from the local LLM for: {prompt}"
        
        return MockOllamaClient()
    
    def process(self, request: ClassifiedRequest) -> str:
        """
        Process a request using a local LLM.
        
        Args:
            request: The classified request to process
            
        Returns:
            A string response
        """
        self.logger.info(f"Processing request {request.request_id} with Tier 2 processor")
        
        # Create a prompt for the LLM
        prompt = self._create_prompt(request)
        
        # Generate a response using the local LLM
        response = self.client.generate(prompt, 
                                       model=LOCAL_MODEL_CONFIG["model_name"],
                                       max_tokens=LOCAL_MODEL_CONFIG["max_tokens"],
                                       temperature=LOCAL_MODEL_CONFIG["temperature"],
                                       top_p=LOCAL_MODEL_CONFIG["top_p"])
        
        return response
    
    def _create_prompt(self, request: ClassifiedRequest) -> str:
        """
        Create a prompt for the LLM based on the request.
        
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
The player has asked: "{player_input}"
Their intent is: {intent}

"""
        
        # Add entity-specific information to the prompt
        if entities:
            prompt += "Relevant information:\n"
            for key, value in entities.items():
                prompt += f"- {key}: {value}\n"
        
        prompt += "\nProvide a helpful, concise response in English:"
        
        return prompt


class Tier3Processor(Processor):
    """
    Tier 3 processor that uses a cloud API (Amazon Bedrock).
    
    This processor handles complex requests by generating responses with a
    powerful cloud-based language model. It is the most flexible but also
    the most expensive processor.
    """
    
    def __init__(self):
        """Initialize the Tier 3 processor."""
        self.logger = logging.getLogger(__name__)
        self.client = self._create_bedrock_client()
    
    def _create_bedrock_client(self):
        """
        Create a Bedrock client.
        
        This is a separate method to make it easier to mock in tests.
        
        Returns:
            A Bedrock client
        """
        # This is a placeholder for the actual Bedrock client
        # In a real implementation, we would import and configure the Bedrock client
        class MockBedrockClient:
            def invoke_model(self, **kwargs):
                class MockResponse:
                    @property
                    def body(self):
                        class MockBody:
                            def read(self):
                                return json.dumps({"completion": "This is a response from the cloud API."}).encode('utf-8')
                        return MockBody()
                return MockResponse()
        
        return MockBedrockClient()
    
    def process(self, request: ClassifiedRequest) -> str:
        """
        Process a request using a cloud API.
        
        Args:
            request: The classified request to process
            
        Returns:
            A string response
        """
        self.logger.info(f"Processing request {request.request_id} with Tier 3 processor")
        
        # Create a prompt for the API
        prompt = self._create_prompt(request)
        
        # Generate a response using the cloud API
        response = self.client.invoke_model(
            modelId=CLOUD_API_CONFIG["model"],
            body=json.dumps({
                "prompt": prompt,
                "max_tokens": CLOUD_API_CONFIG["max_tokens"],
                "temperature": CLOUD_API_CONFIG["temperature"],
                "top_p": CLOUD_API_CONFIG["top_p"]
            }).encode('utf-8')
        )
        
        # Parse the response
        response_json = json.loads(response.body.read().decode('utf-8'))
        
        return response_json.get("completion", "I'm sorry, I couldn't generate a response.")
    
    def _create_prompt(self, request: ClassifiedRequest) -> str:
        """
        Create a prompt for the API based on the request.
        
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
        prompt = f"""<system>
You are a helpful bilingual dog companion in a Japanese train station.
You are assisting an English-speaking player who is learning Japanese.
Provide accurate, helpful responses about Japanese language and culture.
</system>

<user>
{player_input}
</user>

<context>
Intent: {intent}
"""
        
        # Add entity-specific information to the prompt
        if entities:
            prompt += "Entities:\n"
            for key, value in entities.items():
                prompt += f"- {key}: {value}\n"
        
        prompt += "</context>\n\n<assistant>"
        
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
            processor = Tier2Processor()
        elif tier == ProcessingTier.TIER_3:
            processor = Tier3Processor()
        else:
            raise ValueError(f"Unsupported processing tier: {tier.name}")
        
        # Cache the processor for future use
        self._processors[tier] = processor
        
        return processor 