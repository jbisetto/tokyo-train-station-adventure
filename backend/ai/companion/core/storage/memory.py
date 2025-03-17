"""
Tokyo Train Station Adventure - In-Memory Storage

This module provides an in-memory implementation of the conversation storage.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from backend.ai.companion.core.storage.base import ConversationStorage

logger = logging.getLogger(__name__)


class InMemoryConversationStorage(ConversationStorage):
    """
    In-memory implementation of the conversation storage.
    
    This class stores conversation contexts in memory, which means they are lost
    when the application restarts.
    """
    
    def __init__(self):
        """Initialize the in-memory storage."""
        self.contexts = {}
        logger.debug("Initialized InMemoryConversationStorage")
    
    async def get_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a conversation context by ID.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            The conversation context, or None if not found
        """
        return self.contexts.get(conversation_id)
    
    async def save_context(self, conversation_id: str, context: Dict[str, Any]) -> None:
        """
        Save a conversation context.
        
        Args:
            conversation_id: The ID of the conversation
            context: The conversation context to save
        """
        # Ensure the context has a timestamp
        if 'timestamp' not in context:
            context['timestamp'] = datetime.now().isoformat()
            
        self.contexts[conversation_id] = context
    
    async def delete_context(self, conversation_id: str) -> None:
        """
        Delete a conversation context.
        
        Args:
            conversation_id: The ID of the conversation
        """
        if conversation_id in self.contexts:
            del self.contexts[conversation_id]
    
    async def list_contexts(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List conversation contexts.
        
        Args:
            limit: The maximum number of contexts to return
            offset: The number of contexts to skip
            
        Returns:
            A list of conversation contexts
        """
        # Convert to list, sort by timestamp (newest first), and slice
        contexts = list(self.contexts.values())
        contexts.sort(key=lambda ctx: ctx.get('timestamp', ''), reverse=True)
        return contexts[offset:offset + limit]
    
    async def cleanup_old_contexts(self, max_age_days: int = 30) -> int:
        """
        Delete conversation contexts older than the specified age.
        
        Args:
            max_age_days: The maximum age of contexts to keep, in days
            
        Returns:
            The number of contexts deleted
        """
        now = datetime.now()
        max_age = timedelta(days=max_age_days)
        count = 0
        
        for conversation_id, context in list(self.contexts.items()):
            timestamp = context.get('timestamp')
            if timestamp:
                try:
                    context_date = datetime.fromisoformat(timestamp)
                    if now - context_date > max_age:
                        del self.contexts[conversation_id]
                        count += 1
                except (ValueError, TypeError):
                    # If timestamp is invalid, keep the context
                    pass
        
        return count 