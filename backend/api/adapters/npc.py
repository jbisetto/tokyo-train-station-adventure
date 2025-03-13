"""
Adapters for NPC Information API.
"""

from typing import Dict, Any, List
from datetime import datetime, UTC

from backend.api.adapters.base import ResponseAdapter
from backend.api.models.npc import (
    NPCInformationResponse,
    NPCConfigurationResponse,
    NPCInteractionStateResponse,
    VisualAppearance,
    NPCStatus,
    NPCProfile,
    LanguageProfile,
    PromptTemplates,
    ConversationParameters,
    RelationshipMetrics,
    ConversationState,
    GameProgressUnlocks
)


class NPCInformationResponseAdapter(ResponseAdapter):
    """Adapter for NPC information responses."""

    def adapt(self, internal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapt internal data to API format.
        
        Args:
            internal_data: The internal data.
            
        Returns:
            The API response data.
        """
        return self.to_api(internal_data)
    
    def to_api(self, internal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert internal data to API format.
        
        Args:
            internal_data: The internal data.
            
        Returns:
            The API response data.
        """
        # Convert internal data to API format
        visual_appearance = VisualAppearance(
            spriteKey=internal_data.get("visual_appearance", {}).get("sprite_key", ""),
            animations=internal_data.get("visual_appearance", {}).get("animations", [])
        )
        
        status = NPCStatus(
            active=internal_data.get("status", {}).get("active", False),
            currentEmotion=internal_data.get("status", {}).get("current_emotion", ""),
            currentActivity=internal_data.get("status", {}).get("current_activity", "")
        )
        
        api_data = NPCInformationResponse(
            npcId=internal_data.get("npc_id", ""),
            name=internal_data.get("name", ""),
            role=internal_data.get("role", ""),
            location=internal_data.get("location", ""),
            availableDialogueTopics=internal_data.get("available_dialogue_topics", []),
            visualAppearance=visual_appearance,
            status=status
        )
        
        return api_data.model_dump()


class NPCConfigurationResponseAdapter(ResponseAdapter):
    """Adapter for NPC configuration responses."""

    def adapt(self, internal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapt internal data to API format.
        
        Args:
            internal_data: The internal data.
            
        Returns:
            The API response data.
        """
        return self.to_api(internal_data)
    
    def to_api(self, internal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert internal data to API format.
        
        Args:
            internal_data: The internal data.
            
        Returns:
            The API response data.
        """
        # Convert internal data to API format
        profile = NPCProfile(
            name=internal_data.get("profile", {}).get("name", ""),
            role=internal_data.get("profile", {}).get("role", ""),
            location=internal_data.get("profile", {}).get("location", ""),
            personality=internal_data.get("profile", {}).get("personality", []),
            expertise=internal_data.get("profile", {}).get("expertise", []),
            limitations=internal_data.get("profile", {}).get("limitations", [])
        )
        
        language_profile = LanguageProfile(
            defaultLanguage=internal_data.get("language_profile", {}).get("default_language", ""),
            japaneseLevel=internal_data.get("language_profile", {}).get("japanese_level", ""),
            speechPatterns=internal_data.get("language_profile", {}).get("speech_patterns", []),
            commonPhrases=internal_data.get("language_profile", {}).get("common_phrases", []),
            vocabularyFocus=internal_data.get("language_profile", {}).get("vocabulary_focus", [])
        )
        
        prompt_templates = PromptTemplates(
            initialGreeting=internal_data.get("prompt_templates", {}).get("initial_greeting", ""),
            responseFormat=internal_data.get("prompt_templates", {}).get("response_format", ""),
            errorHandling=internal_data.get("prompt_templates", {}).get("error_handling", ""),
            conversationClose=internal_data.get("prompt_templates", {}).get("conversation_close", "")
        )
        
        conversation_parameters = ConversationParameters(
            maxTurns=internal_data.get("conversation_parameters", {}).get("max_turns", 0),
            temperatureDefault=internal_data.get("conversation_parameters", {}).get("temperature_default", 0.0),
            contextWindowSize=internal_data.get("conversation_parameters", {}).get("context_window_size", 0)
        )
        
        api_data = NPCConfigurationResponse(
            npcId=internal_data.get("npc_id", ""),
            profile=profile,
            languageProfile=language_profile,
            promptTemplates=prompt_templates,
            conversationParameters=conversation_parameters
        )
        
        return api_data.model_dump()


class NPCInteractionStateResponseAdapter(ResponseAdapter):
    """Adapter for NPC interaction state responses."""

    def adapt(self, internal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapt internal data to API format.
        
        Args:
            internal_data: The internal data.
            
        Returns:
            The API response data.
        """
        return self.to_api(internal_data)
    
    def to_api(self, internal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert internal data to API format.
        
        Args:
            internal_data: The internal data.
            
        Returns:
            The API response data.
        """
        # Convert internal data to API format
        relationship_metrics = RelationshipMetrics(
            familiarityLevel=internal_data.get("relationship_metrics", {}).get("familiarity_level", 0.0),
            interactionCount=internal_data.get("relationship_metrics", {}).get("interaction_count", 0),
            lastInteractionTime=internal_data.get("relationship_metrics", {}).get("last_interaction_time", datetime.now(UTC))
        )
        
        conversation_state = ConversationState(
            activeConversation=internal_data.get("conversation_state", {}).get("active_conversation", False),
            conversationId=internal_data.get("conversation_state", {}).get("conversation_id"),
            turnCount=internal_data.get("conversation_state", {}).get("turn_count", 0),
            pendingResponse=internal_data.get("conversation_state", {}).get("pending_response", False)
        )
        
        game_progress_unlocks = GameProgressUnlocks(
            unlockedTopics=internal_data.get("game_progress_unlocks", {}).get("unlocked_topics", []),
            completedInteractions=internal_data.get("game_progress_unlocks", {}).get("completed_interactions", []),
            availableQuests=internal_data.get("game_progress_unlocks", {}).get("available_quests", [])
        )
        
        api_data = NPCInteractionStateResponse(
            playerId=internal_data.get("player_id", ""),
            npcId=internal_data.get("npc_id", ""),
            relationshipMetrics=relationship_metrics,
            conversationState=conversation_state,
            gameProgressUnlocks=game_progress_unlocks
        )
        
        return api_data.model_dump() 