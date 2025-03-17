"""
Tokyo Train Station Adventure - Common Conversation Manager

This module provides a unified conversation management system that can be used by
both tier2 and tier3 processors, allowing for consistent conversation handling
with tier-specific optimizations.
"""

import re
import logging
import enum
from typing import Optional, List, Dict, Any, Tuple

from backend.ai.companion.core.models import ClassifiedRequest

logger = logging.getLogger(__name__)


class ConversationState(enum.Enum):
    """
    Enum representing the state of a conversation.
    """
    NEW_TOPIC = "new_topic"
    FOLLOW_UP = "follow_up"
    CLARIFICATION = "clarification"


class ConversationManager:
    """
    Manager for multi-turn conversations.
    
    This class provides methods for detecting the state of a conversation,
    generating contextual prompts, and handling different types of
    conversation flows.
    """
    
    def __init__(self, tier_specific_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the conversation manager.
        
        Args:
            tier_specific_config: Optional configuration specific to the tier
        """
        self.tier_specific_config = tier_specific_config or {}
        
        # Patterns for detecting follow-up questions
        self.follow_up_patterns = [
            r"what does .+ mean in that",
            r"can you explain .+ in that",
            r"what is .+ in that",
            r"how do you say .+ in that",
            r"what about .+",
            r"how about .+",
            r"tell me more about .+",
            r"what is the difference between .+",
            r"could you elaborate on .+"
        ]
        
        # Patterns for detecting clarification requests
        self.clarification_patterns = [
            r"can you explain that again",
            r"i don't understand",
            r"what do you mean",
            r"could you clarify",
            r"please explain again",
            r"i'm confused",
            r"that doesn't make sense",
            r"can you repeat that",
            r"what was that again"
        ]
        
        logger.debug("Initialized ConversationManager with config: %s", self.tier_specific_config)
    
    def detect_conversation_state(
        self,
        request: ClassifiedRequest,
        conversation_history: List[Dict[str, Any]]
    ) -> ConversationState:
        """
        Detect the state of a conversation based on the current request and history.
        
        Args:
            request: The current request
            conversation_history: The conversation history
            
        Returns:
            The detected conversation state
        """
        # If there's no history, it's a new topic
        if not conversation_history:
            return ConversationState.NEW_TOPIC
        
        # Get the player's input in lowercase for pattern matching
        player_input = request.player_input.lower()
        
        # Check for clarification patterns
        for pattern in self.clarification_patterns:
            if re.search(pattern, player_input):
                logger.debug(f"Detected clarification request: {player_input}")
                return ConversationState.CLARIFICATION
        
        # Check for follow-up patterns
        for pattern in self.follow_up_patterns:
            if re.search(pattern, player_input):
                logger.debug(f"Detected follow-up question: {player_input}")
                return ConversationState.FOLLOW_UP
        
        # Check for references to previous entities
        for entry in conversation_history:
            if "entities" in entry and entry["entities"]:
                for entity_name, entity_value in entry["entities"].items():
                    if isinstance(entity_value, str) and entity_value.lower() in player_input:
                        logger.debug(f"Detected reference to previous entity: {entity_value}")
                        return ConversationState.FOLLOW_UP
        
        # Default to new topic
        return ConversationState.NEW_TOPIC
    
    def generate_contextual_prompt(
        self,
        request: ClassifiedRequest,
        conversation_history: List[Dict[str, Any]],
        state: ConversationState,
        base_prompt: str
    ) -> str:
        """
        Generate a contextual prompt based on the conversation history and state.
        
        Args:
            request: The current request
            conversation_history: The conversation history
            state: The detected conversation state
            base_prompt: The base prompt to build upon
            
        Returns:
            A prompt that includes relevant context
        """
        # Start with the base prompt
        prompt = base_prompt
        
        # Add conversation history if available
        if conversation_history and (state == ConversationState.FOLLOW_UP or state == ConversationState.CLARIFICATION):
            history_str = "\nPrevious conversation:\n"
            
            # Get the most recent entries (up to 3)
            recent_history = conversation_history[-3:]
            
            for entry in recent_history:
                history_str += f"Player: {entry.get('request', '')}\n"
                history_str += f"Companion: {entry.get('response', '')}\n\n"
            
            prompt += history_str
        
        # Add specific instructions based on the conversation state
        if state == ConversationState.FOLLOW_UP:
            prompt += "\nThe player is asking a follow-up question related to the previous exchanges.\n"
            prompt += "Please provide a response that takes into account the conversation history.\n"
        elif state == ConversationState.CLARIFICATION:
            prompt += "\nThe player is asking for clarification about something in the previous exchanges.\n"
            prompt += "Please provide a more detailed explanation of the most recent topic.\n"
        
        return prompt
    
    def add_to_history(
        self,
        conversation_history: List[Dict[str, Any]],
        request: ClassifiedRequest,
        response: str
    ) -> List[Dict[str, Any]]:
        """
        Add a request-response pair to the conversation history.
        
        Args:
            conversation_history: The existing conversation history
            request: The current request
            response: The response to the request
            
        Returns:
            The updated conversation history
        """
        # Create a new history entry
        entry = {
            "request": request.player_input,
            "response": response,
            "timestamp": request.timestamp.isoformat() if hasattr(request, 'timestamp') else None,
            "intent": request.intent.value if hasattr(request, 'intent') else None,
            "entities": request.extracted_entities if hasattr(request, 'extracted_entities') else {}
        }
        
        # Add the entry to the history
        conversation_history.append(entry)
        
        # Limit the history size if specified in the config
        max_history = self.tier_specific_config.get('max_history_size', 10)
        if len(conversation_history) > max_history:
            conversation_history = conversation_history[-max_history:]
        
        return conversation_history
    
    def process_with_history(
        self,
        request: ClassifiedRequest,
        conversation_history: List[Dict[str, Any]],
        base_prompt: str,
        generate_response_func
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Process a request using conversation history.
        
        Args:
            request: The current request
            conversation_history: The conversation history
            base_prompt: The base prompt to build upon
            generate_response_func: Function to generate a response
            
        Returns:
            A tuple of (response, updated_history)
        """
        # Detect the conversation state
        state = self.detect_conversation_state(request, conversation_history)
        
        # Generate a contextual prompt
        prompt = self.generate_contextual_prompt(
            request,
            conversation_history,
            state,
            base_prompt
        )
        
        # Generate a response using the provided function
        response = generate_response_func(prompt)
        
        # Add the request-response pair to the history
        updated_history = self.add_to_history(
            conversation_history,
            request,
            response
        )
        
        return response, updated_history 