from datetime import datetime, UTC
import uuid
from typing import Dict, Any, List

from backend.api.adapters.base import RequestAdapter, ResponseAdapter
from backend.api.models.game_state import (
    SaveGameStateRequest,
    SaveGameStateResponse,
    LoadGameStateResponse,
    ListSavedGamesResponse,
    SaveMetadata,
    Location,
    QuestState,
    Objective,
    Position,
    CompanionState
)


class SaveGameStateRequestAdapter(RequestAdapter):
    """Adapter for save game state requests."""

    def adapt(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform an external request to the internal format.
        
        Args:
            request_data: The external request to transform
            
        Returns:
            The transformed internal request
        """
        return self.to_internal(request_data)

    def to_internal(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert API request data to internal format.
        
        Args:
            request_data: The API request data.
            
        Returns:
            The internal format data.
        """
        # Validate request data using Pydantic model
        validated_data = SaveGameStateRequest(**request_data)
        
        # Convert to internal format
        internal_data = {
            "player_id": validated_data.playerId,
            "session_id": validated_data.sessionId,
            "timestamp": validated_data.timestamp,
            "location": {
                "area": validated_data.location.area,
                "position": {
                    "x": validated_data.location.position.x,
                    "y": validated_data.location.position.y
                }
            },
            "quest_state": {
                "active_quest": validated_data.questState.activeQuest,
                "quest_step": validated_data.questState.questStep,
                "objectives": [
                    {
                        "id": obj.id,
                        "completed": obj.completed,
                        "description": obj.description
                    }
                    for obj in validated_data.questState.objectives
                ]
            },
            "inventory": validated_data.inventory,
            "game_flags": validated_data.gameFlags,
            "companions": {
                companion_id: {
                    "relationship": state.relationship,
                    "assistance_used": state.assistanceUsed
                }
                for companion_id, state in validated_data.companions.items()
            }
        }
        
        return internal_data


class SaveGameStateResponseAdapter(ResponseAdapter):
    """Adapter for save game state responses."""

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
        api_data = SaveGameStateResponse(
            success=internal_data.get("success", True),
            saveId=internal_data.get("save_id", str(uuid.uuid4())),
            timestamp=internal_data.get("timestamp", datetime.now(UTC))
        )
        
        return api_data.model_dump()


class LoadGameStateResponseAdapter(ResponseAdapter):
    """Adapter for load game state responses."""

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
        api_data = LoadGameStateResponse(
            playerId=internal_data.get("player_id", ""),
            saveId=internal_data.get("save_id", ""),
            sessionId=internal_data.get("session_id", ""),
            timestamp=internal_data.get("timestamp", datetime.now(UTC)),
            lastPlayed=internal_data.get("last_played", datetime.now(UTC)),
            location=self._convert_location(internal_data.get("location", {})),
            questState=self._convert_quest_state(internal_data.get("quest_state", {})),
            inventory=internal_data.get("inventory", []),
            gameFlags=internal_data.get("game_flags", {}),
            companions=self._convert_companions(internal_data.get("companions", {}))
        )
        
        return api_data.model_dump()

    def _convert_location(self, location_data: Dict[str, Any]) -> Location:
        """Convert location data to API format."""
        position_data = location_data.get("position", {})
        return Location(
            area=location_data.get("area", ""),
            position=Position(
                x=position_data.get("x", 0),
                y=position_data.get("y", 0)
            )
        )

    def _convert_quest_state(self, quest_data: Dict[str, Any]) -> QuestState:
        """Convert quest state data to API format."""
        return QuestState(
            activeQuest=quest_data.get("active_quest", ""),
            questStep=quest_data.get("quest_step", ""),
            objectives=self._convert_objectives(quest_data.get("objectives", []))
        )

    def _convert_objectives(self, objectives_data: List[Dict[str, Any]]) -> List[Objective]:
        """Convert objectives data to API format."""
        return [
            Objective(
                id=obj.get("id", ""),
                completed=obj.get("completed", False),
                description=obj.get("description", "")
            )
            for obj in objectives_data
        ]

    def _convert_companions(self, companions_data: Dict[str, Any]) -> Dict[str, CompanionState]:
        """Convert companions data to API format."""
        return {
            companion_id: CompanionState(
                relationship=state.get("relationship", 0.0),
                assistanceUsed=state.get("assistance_used", 0)
            )
            for companion_id, state in companions_data.items()
        }


class ListSavedGamesResponseAdapter(ResponseAdapter):
    """Adapter for list saved games responses."""

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
        api_data = ListSavedGamesResponse(
            playerId=internal_data.get("player_id", ""),
            saves=self._convert_saves(internal_data.get("saves", []))
        )
        
        return api_data.model_dump()

    def _convert_saves(self, saves_data: List[Dict[str, Any]]) -> List[SaveMetadata]:
        """Convert saves data to API format."""
        return [
            SaveMetadata(
                saveId=save.get("save_id", ""),
                timestamp=save.get("timestamp", datetime.now(UTC)),
                location=save.get("location_name", ""),
                questName=save.get("quest_name", ""),
                level=save.get("level")
            )
            for save in saves_data
        ] 