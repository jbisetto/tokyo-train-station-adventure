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
from datetime import datetime

from backend.ai.companion.core.models import ClassifiedRequest
from backend.ai.companion.core.storage.factory import default_storage_factory
from backend.ai.companion.core.storage.base import ConversationStorage

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
    
    def __init__(self, tier_specific_config: Optional[Dict[str, Any]] = None, storage: Optional[ConversationStorage] = None):
        """
        Initialize the conversation manager.
        
        Args:
            tier_specific_config: Optional configuration specific to the tier
            storage: Optional storage implementation to use
        """
        self.tier_specific_config = tier_specific_config or {}
        
        # Get a storage instance
        self.storage = storage or default_storage_factory.get_storage()
        
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
    
    async def get_or_create_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get an existing conversation context or create a new one.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            The conversation context
        """
        # Try to get the context from storage
        context = await self.storage.get_context(conversation_id)
        
        if not context:
            # Create a new context
            context = {
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "entries": []
            }
            
            # Save the new context
            await self.storage.save_context(conversation_id, context)
        
        return context
    
    async def add_entry(self, conversation_id: str, entry: Dict[str, Any]) -> None:
        """
        Add an entry to a conversation context.
        
        Args:
            conversation_id: The ID of the conversation
            entry: The entry to add
        """
        context = await self.get_or_create_context(conversation_id)
        
        # Add timestamp if not present
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().isoformat()
        
        # Add the entry
        context["entries"].append(entry)
        
        # Trim history if it exceeds the maximum size
        max_history = self.tier_specific_config.get("max_history_size", 10)
        if len(context["entries"]) > max_history:
            context["entries"] = context["entries"][-max_history:]
        
        # Update the context in storage
        await self.storage.save_context(conversation_id, context)
    
    async def get_entries(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get all entries for a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            The entries for the conversation
        """
        context = await self.get_or_create_context(conversation_id)
        return context.get("entries", [])
    
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
        
        # Add conversation history if available (in OpenAI conversation format)
        if conversation_history and (state == ConversationState.FOLLOW_UP or state == ConversationState.CLARIFICATION):
            prompt += "\nPrevious conversation (in OpenAI conversation format):\n"
            
            # Get the most recent entries (up to 6 entries = 3 exchanges)
            recent_history = conversation_history[-6:]
            
            # Format in OpenAI conversation format
            prompt += "[\n"
            
            for entry in recent_history:
                if entry.get("type") == "user_message":
                    prompt += f'  {{"role": "user", "content": "{entry.get("text", "").replace("\"", "\\\"")}"}},'
                elif entry.get("type") == "assistant_message":
                    prompt += f'  {{"role": "assistant", "content": "{entry.get("text", "").replace("\"", "\\\"")}"}},'
                prompt += "\n"
            
            # Remove trailing comma and close the array
            if recent_history:
                prompt = prompt.rstrip(",\n") + "\n"
            prompt += "]\n"
        
        # Add specific instructions based on the conversation state
        if state == ConversationState.FOLLOW_UP:
            prompt += "\nThe player is asking a follow-up question related to the previous exchanges.\n"
            prompt += "Please provide a response that takes into account the conversation history.\n"
        elif state == ConversationState.CLARIFICATION:
            prompt += "\nThe player is asking for clarification about something in the previous exchanges.\n"
            prompt += "Please provide a more detailed explanation of the most recent topic.\n"
        
        return prompt
    
    async def add_to_history(
        self,
        conversation_id: str,
        request: ClassifiedRequest,
        response: str
    ) -> List[Dict[str, Any]]:
        """
        Add a request-response pair to the conversation history.
        
        Args:
            conversation_id: The conversation ID
            request: The current request
            response: The response to the request
            
        Returns:
            The updated conversation history
        """
        # Get the current conversation context
        context = await self.get_or_create_context(conversation_id)
        conversation_history = context.get("entries", [])
        
        # Create a new history entry
        entry = {
            "type": "user_message",
            "text": request.player_input,
            "timestamp": request.timestamp.isoformat() if hasattr(request, 'timestamp') else datetime.now().isoformat(),
            "intent": request.intent.value if hasattr(request, 'intent') else None,
            "entities": request.extracted_entities if hasattr(request, 'extracted_entities') else {}
        }
        
        # Add the user's request to the history
        conversation_history.append(entry)
        
        # Create the assistant's response entry
        response_entry = {
            "type": "assistant_message",
            "text": response,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Add the response to the history
        conversation_history.append(response_entry)
        
        # Limit the history size if specified in the config
        max_history = self.tier_specific_config.get('max_history_size', 10)
        if len(conversation_history) > max_history:
            conversation_history = conversation_history[-max_history:]
        
        # Update the context with the new history
        context["entries"] = conversation_history
        await self.storage.save_context(conversation_id, context)
        
        return conversation_history
    
    async def process_with_history(
        self,
        request: ClassifiedRequest,
        conversation_id: str,
        base_prompt: str,
        generate_response_func
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Process a request using conversation history.
        
        Args:
            request: The current request
            conversation_id: The conversation ID
            base_prompt: The base prompt to build upon
            generate_response_func: Function to generate a response
            
        Returns:
            A tuple of (response, updated_history)
        """
        # Get the conversation history
        context = await self.get_or_create_context(conversation_id)
        conversation_history = context.get("entries", [])
        
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
        response = await generate_response_func(prompt)
        
        # Add the request-response pair to the history
        updated_history = await self.add_to_history(
            conversation_id,
            request,
            response
        )
        
        return response, updated_history
    
    async def cleanup_old_conversations(self, max_age_days: int = 30) -> int:
        """
        Delete conversation contexts older than the specified age.
        
        Args:
            max_age_days: The maximum age of contexts to keep, in days
            
        Returns:
            The number of contexts deleted
        """
        return await self.storage.cleanup_old_contexts(max_age_days) 