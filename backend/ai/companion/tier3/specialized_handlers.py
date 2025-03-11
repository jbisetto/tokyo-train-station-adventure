"""
Specialized handlers for complex scenarios in Tier 3.

These handlers are designed to process specific types of complex requests
that require specialized prompt engineering and response processing.
"""

import abc
import logging
from typing import Dict, Optional, Any, List, Type

from backend.ai.companion.core.models import (
    ClassifiedRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from backend.ai.companion.tier3.bedrock_client import BedrockClient

logger = logging.getLogger(__name__)


class SpecializedHandler(abc.ABC):
    """
    Abstract base class for specialized handlers.
    
    Specialized handlers are responsible for handling specific types of complex
    requests that require specialized prompt engineering and response processing.
    """
    
    def __init__(self, bedrock_client: Optional[BedrockClient] = None):
        """
        Initialize the specialized handler.
        
        Args:
            bedrock_client: The Bedrock client to use for generating responses.
                If not provided, a new client will be created when needed.
        """
        self.bedrock_client = bedrock_client or BedrockClient()
    
    @abc.abstractmethod
    def can_handle(self, intent: IntentCategory) -> bool:
        """
        Check if this handler can handle the given intent.
        
        Args:
            intent: The intent to check.
            
        Returns:
            True if this handler can handle the intent, False otherwise.
        """
        pass
    
    @abc.abstractmethod
    def create_prompt(self, request: ClassifiedRequest) -> str:
        """
        Create a prompt for the given request.
        
        Args:
            request: The request to create a prompt for.
            
        Returns:
            The prompt to send to the LLM.
        """
        pass
    
    def process_response(self, response: str, request: ClassifiedRequest) -> str:
        """
        Process the response from the LLM.
        
        Args:
            response: The raw response from the LLM.
            request: The original request.
            
        Returns:
            The processed response to send to the player.
        """
        # By default, just return the response as-is
        return response.strip()
    
    async def handle_request(self, request: ClassifiedRequest) -> str:
        """
        Handle the given request.
        
        Args:
            request: The request to handle.
            
        Returns:
            The response to send to the player.
        """
        prompt = self.create_prompt(request)
        
        logger.debug(f"Sending prompt to Bedrock: {prompt[:100]}...")
        
        response = await self.bedrock_client.generate(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7,
            model_id="anthropic.claude-3-sonnet-20240229-v1:0"
        )
        
        logger.debug(f"Received response from Bedrock: {response[:100]}...")
        
        processed_response = self.process_response(response, request)
        
        return processed_response


class DefaultHandler(SpecializedHandler):
    """
    Default handler for requests that don't have a specialized handler.
    
    This handler uses a generic prompt template and minimal response processing.
    """
    
    def can_handle(self, intent: IntentCategory) -> bool:
        """
        Check if this handler can handle the given intent.
        
        The default handler can handle any intent.
        
        Args:
            intent: The intent to check.
            
        Returns:
            True, always.
        """
        return True
    
    def create_prompt(self, request: ClassifiedRequest) -> str:
        """
        Create a prompt for the given request.
        
        Args:
            request: The request to create a prompt for.
            
        Returns:
            The prompt to send to the LLM.
        """
        prompt = f"""
        You are a helpful AI companion in the Tokyo Train Station Adventure game.
        You are assisting a player who is learning Japanese while navigating Tokyo's train system.
        
        The player has asked: "{request.player_input}"
        
        Please provide a helpful, concise response that:
        1. Directly addresses their question
        2. Uses simple language appropriate for a language learner
        3. Includes relevant Japanese phrases with romaji pronunciation
        4. Keeps cultural context in mind
        5. Is friendly and encouraging
        
        Your response:
        """
        
        return prompt.strip()


class GrammarExplanationHandler(SpecializedHandler):
    """
    Specialized handler for grammar explanation requests.
    
    This handler uses specialized prompts for explaining Japanese grammar
    points in a way that's accessible to language learners.
    """
    
    def can_handle(self, intent: IntentCategory) -> bool:
        """
        Check if this handler can handle the given intent.
        
        Args:
            intent: The intent to check.
            
        Returns:
            True if this handler can handle the intent, False otherwise.
        """
        return intent == IntentCategory.GRAMMAR_EXPLANATION
    
    def create_prompt(self, request: ClassifiedRequest) -> str:
        """
        Create a prompt for the given request.
        
        Args:
            request: The request to create a prompt for.
            
        Returns:
            The prompt to send to the LLM.
        """
        # Extract the grammar point if available
        grammar_point = request.extracted_entities.get("grammar_point", "")
        
        prompt = f"""
        You are a Japanese language teacher in the Tokyo Train Station Adventure game.
        You specialize in explaining Japanese grammar in a clear, concise way for beginners.
        
        The player has asked about the following grammar point: "{request.player_input}"
        
        Please provide an explanation that:
        1. Clearly explains the grammar point "{grammar_point}" at JLPT N5 level
        2. Includes 2-3 simple, practical examples with romaji and English translations
        3. Relates the explanation to situations the player might encounter in a train station
        4. Uses visual formatting (bullet points, spacing) to make the explanation easy to follow
        5. Is concise (150-200 words maximum)
        
        Your explanation:
        """
        
        return prompt.strip()
    
    def process_response(self, response: str, request: ClassifiedRequest) -> str:
        """
        Process the response from the LLM.
        
        Args:
            response: The raw response from the LLM.
            request: The original request.
            
        Returns:
            The processed response to send to the player.
        """
        # For grammar explanations, we want to ensure the response includes
        # both Japanese script and romaji for all examples
        
        processed = response.strip()
        
        # Add a friendly closing if not present
        if "good luck" not in processed.lower() and "がんばって" not in processed:
            processed += "\n\nがんばって (Ganbatte)! Good luck with your Japanese studies!"
        
        return processed


class TranslationHandler(SpecializedHandler):
    """
    Specialized handler for translation requests.
    
    This handler uses specialized prompts for translating between
    English and Japanese with detailed explanations.
    """
    
    def can_handle(self, intent: IntentCategory) -> bool:
        """
        Check if this handler can handle the given intent.
        
        Args:
            intent: The intent to check.
            
        Returns:
            True if this handler can handle the intent, False otherwise.
        """
        return intent == IntentCategory.TRANSLATION_CONFIRMATION
    
    def create_prompt(self, request: ClassifiedRequest) -> str:
        """
        Create a prompt for the given request.
        
        Args:
            request: The request to create a prompt for.
            
        Returns:
            The prompt to send to the LLM.
        """
        # Extract relevant entities if available
        destination = request.extracted_entities.get("destination", "")
        ticket_type = request.extracted_entities.get("ticket_type", "")
        
        prompt = f"""
        You are a Japanese language assistant in the Tokyo Train Station Adventure game.
        You specialize in providing accurate translations with helpful explanations.
        
        The player has asked for a translation: "{request.player_input}"
        
        Relevant details:
        - Destination: {destination}
        - Ticket type: {ticket_type}
        
        Please provide a response that:
        1. Gives the Japanese translation at JLPT N5 level
        2. Includes both Japanese script and romaji pronunciation
        3. Breaks down the translation with word-by-word explanations
        4. Provides cultural context if relevant
        5. Is formatted clearly with the translation highlighted
        
        Your translation and explanation:
        """
        
        return prompt.strip()
    
    def process_response(self, response: str, request: ClassifiedRequest) -> str:
        """
        Process the response from the LLM.
        
        Args:
            response: The raw response from the LLM.
            request: The original request.
            
        Returns:
            The processed response to send to the player.
        """
        # For translations, we want to ensure the response includes
        # both Japanese script and romaji for all phrases
        
        processed = response.strip()
        
        # Add a practice suggestion if not present
        if "practice" not in processed.lower() and "try saying" not in processed.lower():
            processed += "\n\nTry saying this phrase a few times to practice your pronunciation!"
        
        return processed


class ConversationContextHandler(SpecializedHandler):
    """
    Specialized handler for requests with conversation context.
    
    This handler incorporates previous conversation history to maintain
    context across multiple turns of conversation.
    """
    
    def can_handle(self, intent: IntentCategory) -> bool:
        """
        Check if this handler can handle the given intent.
        
        This handler can handle any intent if conversation context is available.
        
        Args:
            intent: The intent to check.
            
        Returns:
            True if this handler can handle the intent, False otherwise.
        """
        # This handler can handle any intent, as it's focused on maintaining
        # conversation context rather than specific intents
        return True
    
    def create_prompt(self, request: ClassifiedRequest) -> str:
        """
        Create a prompt for the given request.
        
        Args:
            request: The request to create a prompt for.
            
        Returns:
            The prompt to send to the LLM.
        """
        # Extract conversation context if available
        conversation_context = request.additional_params.get("conversation_context", {})
        previous_exchanges = conversation_context.get("previous_exchanges", [])
        player_language_level = conversation_context.get("player_language_level", "N5")
        current_location = conversation_context.get("current_location", "unknown")
        
        # Build the conversation history part of the prompt
        conversation_history = ""
        if previous_exchanges:
            conversation_history = "Previous conversation:\n"
            for i, exchange in enumerate(previous_exchanges):
                conversation_history += f"Player: {exchange.get('request', '')}\n"
                conversation_history += f"You: {exchange.get('response', '')}\n\n"
        
        prompt = f"""
        You are a helpful AI companion in the Tokyo Train Station Adventure game.
        You are assisting a player who is learning Japanese while navigating Tokyo's train system.
        
        Player's current location: {current_location}
        Player's Japanese language level: {player_language_level}
        
        {conversation_history}
        
        The player's current question is: "{request.player_input}"
        
        Please provide a helpful response that:
        1. Maintains continuity with the previous conversation
        2. Directly addresses their current question
        3. Uses simple language appropriate for their level ({player_language_level})
        4. Includes relevant Japanese phrases with romaji pronunciation
        5. Is friendly and encouraging
        
        Your response:
        """
        
        return prompt.strip()
    
    def process_response(self, response: str, request: ClassifiedRequest) -> str:
        """
        Process the response from the LLM.
        
        Args:
            response: The raw response from the LLM.
            request: The original request.
            
        Returns:
            The processed response to send to the player.
        """
        # For conversation context, we want to ensure the response
        # maintains a consistent tone and style
        
        processed = response.strip()
        
        return processed


class SpecializedHandlerRegistry:
    """
    Registry for specialized handlers.
    
    This class maintains a mapping of intent categories to specialized handlers
    and provides methods for registering and retrieving handlers.
    """
    
    def __init__(self):
        """Initialize the registry with an empty handler map."""
        self._handlers: Dict[IntentCategory, SpecializedHandler] = {}
        self._default_handler = DefaultHandler()
    
    def register_handler(self, intent: IntentCategory, handler: SpecializedHandler) -> None:
        """
        Register a handler for the given intent.
        
        Args:
            intent: The intent to register the handler for.
            handler: The handler to register.
        """
        self._handlers[intent] = handler
    
    def get_handler(self, intent: IntentCategory) -> SpecializedHandler:
        """
        Get the handler for the given intent.
        
        If no handler is registered for the intent, returns the default handler.
        
        Args:
            intent: The intent to get a handler for.
            
        Returns:
            The handler for the intent, or the default handler if none is registered.
        """
        return self._handlers.get(intent, self._default_handler)
    
    def initialize_default_handlers(self) -> None:
        """
        Initialize the registry with default handlers for common intents.
        """
        self.register_handler(IntentCategory.GRAMMAR_EXPLANATION, GrammarExplanationHandler())
        self.register_handler(IntentCategory.TRANSLATION_CONFIRMATION, TranslationHandler())
        
        # Add more default handlers as needed 