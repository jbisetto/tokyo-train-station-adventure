"""
Base adapter interfaces for transforming between API and internal data formats.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, TypeVar

# Define type variables for request and response types
RequestT = TypeVar('RequestT')
ResponseT = TypeVar('ResponseT')
InternalRequestT = TypeVar('InternalRequestT')
InternalResponseT = TypeVar('InternalResponseT')


class RequestAdapter(Generic[RequestT, InternalRequestT], ABC):
    """
    Base interface for request adapters.
    
    Request adapters transform external API requests into internal format.
    """
    
    @abstractmethod
    def adapt(self, request: RequestT) -> InternalRequestT:
        """
        Transform an external request to the internal format.
        
        Args:
            request: The external request to transform
            
        Returns:
            The transformed internal request
        """
        pass


class ResponseAdapter(Generic[InternalResponseT, ResponseT], ABC):
    """
    Base interface for response adapters.
    
    Response adapters transform internal responses into external API format.
    """
    
    @abstractmethod
    def adapt(self, response: InternalResponseT) -> ResponseT:
        """
        Transform an internal response to the external format.
        
        Args:
            response: The internal response to transform
            
        Returns:
            The transformed external response
        """
        pass


class AdapterFactory:
    """
    Factory for creating adapters.
    """
    
    @staticmethod
    def get_request_adapter(adapter_type: str) -> RequestAdapter:
        """
        Get a request adapter for the specified type.
        
        Args:
            adapter_type: The type of adapter to get
            
        Returns:
            A request adapter instance
        """
        from backend.api.adapters.companion_assist import CompanionAssistRequestAdapter
        from backend.api.adapters.dialogue_process import DialogueProcessRequestAdapter
        from backend.api.adapters.player_progress import PlayerProgressRequestAdapter
        from backend.api.adapters.game_state import SaveGameStateRequestAdapter
        
        adapters = {
            "companion_assist": CompanionAssistRequestAdapter(),
            "dialogue_process": DialogueProcessRequestAdapter(),
            "player_progress": PlayerProgressRequestAdapter(),
            "save_game_state": SaveGameStateRequestAdapter(),
        }
        
        return adapters.get(adapter_type)
    
    @staticmethod
    def get_response_adapter(adapter_type: str) -> ResponseAdapter:
        """
        Get a response adapter for the specified type.
        
        Args:
            adapter_type: The type of adapter to get
            
        Returns:
            A response adapter instance
        """
        from backend.api.adapters.companion_assist import CompanionAssistResponseAdapter
        from backend.api.adapters.dialogue_process import DialogueProcessResponseAdapter
        from backend.api.adapters.player_progress import PlayerProgressResponseAdapter
        from backend.api.adapters.game_state import (
            SaveGameStateResponseAdapter,
            LoadGameStateResponseAdapter,
            ListSavedGamesResponseAdapter
        )
        
        adapters = {
            "companion_assist": CompanionAssistResponseAdapter(),
            "dialogue_process": DialogueProcessResponseAdapter(),
            "player_progress": PlayerProgressResponseAdapter(),
            "save_game_state": SaveGameStateResponseAdapter(),
            "load_game_state": LoadGameStateResponseAdapter(),
            "list_saved_games": ListSavedGamesResponseAdapter(),
        }
        
        return adapters.get(adapter_type) 