"""
Tokyo Train Station Adventure - Companion AI Data Models

This module defines the data models used by the companion AI system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import datetime


class IntentCategory(str, Enum):
    """Intent categories for player requests."""
    VOCABULARY_HELP = "vocabulary_help"
    GRAMMAR_EXPLANATION = "grammar_explanation"
    DIRECTION_GUIDANCE = "direction_guidance"
    TRANSLATION_CONFIRMATION = "translation_confirmation"
    GENERAL_HINT = "general_hint"


class ComplexityLevel(str, Enum):
    """Complexity levels for processing requests."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class ProcessingTier(str, Enum):
    """Processing tiers for handling requests."""
    TIER_1 = "tier_1"  # Rule-based
    TIER_2 = "tier_2"  # Local LLM
    TIER_3 = "tier_3"  # Cloud API


@dataclass
class GameContext:
    """Current game context information."""
    player_location: str
    current_objective: str
    nearby_npcs: List[str] = field(default_factory=list)
    nearby_objects: List[str] = field(default_factory=list)
    player_inventory: List[str] = field(default_factory=list)
    language_proficiency: Dict[str, float] = field(default_factory=dict)
    game_progress: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompanionRequest:
    """A request to the companion AI."""
    request_id: str
    player_input: str
    request_type: str
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    game_context: Optional[GameContext] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassifiedRequest:
    """A request that has been classified with intent and complexity."""
    # Include all fields from CompanionRequest
    request_id: str
    player_input: str
    request_type: str
    # Add classification fields
    intent: IntentCategory
    complexity: ComplexityLevel
    processing_tier: ProcessingTier
    # Optional fields
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    game_context: Optional[GameContext] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    extracted_entities: Dict[str, Any] = field(default_factory=dict)
    profile_id: Optional[str] = None
    
    @classmethod
    def from_companion_request(cls, request: CompanionRequest, intent: IntentCategory, 
                              complexity: ComplexityLevel, processing_tier: ProcessingTier,
                              confidence: float = 0.0, extracted_entities: Dict[str, Any] = None):
        """Create a ClassifiedRequest from a CompanionRequest."""
        # Check if profile_id is in additional_params
        profile_id = request.additional_params.get("profile_id")
        
        return cls(
            request_id=request.request_id,
            player_input=request.player_input,
            request_type=request.request_type,
            timestamp=request.timestamp,
            game_context=request.game_context,
            additional_params=request.additional_params,
            intent=intent,
            complexity=complexity,
            processing_tier=processing_tier,
            confidence=confidence,
            extracted_entities=extracted_entities or {},
            profile_id=profile_id
        )


@dataclass
class CompanionResponse:
    """A response from the companion AI."""
    request_id: str
    response_text: str
    intent: IntentCategory
    processing_tier: ProcessingTier
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    suggested_actions: List[str] = field(default_factory=list)
    learning_cues: Dict[str, Any] = field(default_factory=dict)
    emotion: str = "neutral"
    confidence: float = 1.0
    debug_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """Context for a conversation with the companion."""
    conversation_id: str
    request_history: List[CompanionRequest] = field(default_factory=list)
    response_history: List[CompanionResponse] = field(default_factory=list)
    session_start: datetime.datetime = field(default_factory=datetime.datetime.now)
    last_updated: datetime.datetime = field(default_factory=datetime.datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_interaction(self, request: CompanionRequest, response: CompanionResponse):
        """Add a request-response interaction to the history."""
        self.request_history.append(request)
        self.response_history.append(response)
        self.last_updated = datetime.datetime.now() 