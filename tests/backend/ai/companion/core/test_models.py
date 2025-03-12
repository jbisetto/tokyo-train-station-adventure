"""
Tests for the companion AI data models.
"""

import pytest
from datetime import datetime, timedelta
import uuid

from backend.ai.companion.core.models import (
    IntentCategory,
    ComplexityLevel,
    ProcessingTier,
    GameContext,
    CompanionRequest,
    ClassifiedRequest,
    CompanionResponse,
    ConversationContext
)


class TestEnums:
    """Tests for the enum classes."""
    
    def test_intent_category_values(self):
        """Test that IntentCategory has the expected values."""
        assert IntentCategory.VOCABULARY_HELP.value == "vocabulary_help"
        assert IntentCategory.GRAMMAR_EXPLANATION.value == "grammar_explanation"
        assert IntentCategory.DIRECTION_GUIDANCE.value == "direction_guidance"
        assert IntentCategory.TRANSLATION_CONFIRMATION.value == "translation_confirmation"
        assert IntentCategory.GENERAL_HINT.value == "general_hint"
    
    def test_complexity_level_values(self):
        """Test that ComplexityLevel has the expected values."""
        assert ComplexityLevel.SIMPLE.value == "simple"
        assert ComplexityLevel.MODERATE.value == "moderate"
        assert ComplexityLevel.COMPLEX.value == "complex"
    
    def test_processing_tier_values(self):
        """Test that ProcessingTier has the expected values."""
        assert ProcessingTier.TIER_1.value == "tier_1"
        assert ProcessingTier.TIER_2.value == "tier_2"
        assert ProcessingTier.TIER_3.value == "tier_3"


class TestGameContext:
    """Tests for the GameContext class."""
    
    def test_game_context_creation(self):
        """Test that a GameContext can be created with the required fields."""
        context = GameContext(
            player_location="station_entrance",
            current_objective="find_information_desk"
        )
        
        assert context.player_location == "station_entrance"
        assert context.current_objective == "find_information_desk"
        assert context.nearby_npcs == []
        assert context.nearby_objects == []
        assert context.player_inventory == []
        assert isinstance(context.language_proficiency, dict)
        assert isinstance(context.game_progress, dict)
    
    def test_game_context_with_optional_fields(self):
        """Test that a GameContext can be created with optional fields."""
        context = GameContext(
            player_location="platform_1",
            current_objective="board_train",
            nearby_npcs=["conductor", "passenger"],
            nearby_objects=["bench", "vending_machine"],
            player_inventory=["ticket", "map"],
            language_proficiency={"reading": 0.7},
            game_progress={"tickets_purchased": 1}
        )
        
        assert context.player_location == "platform_1"
        assert context.current_objective == "board_train"
        assert "conductor" in context.nearby_npcs
        assert "vending_machine" in context.nearby_objects
        assert "ticket" in context.player_inventory
        assert context.language_proficiency["reading"] == 0.7
        assert context.game_progress["tickets_purchased"] == 1


class TestCompanionRequest:
    """Tests for the CompanionRequest class."""
    
    def test_companion_request_creation(self):
        """Test that a CompanionRequest can be created with the required fields."""
        request_id = str(uuid.uuid4())
        request = CompanionRequest(
            request_id=request_id,
            player_input="How do I buy a ticket?",
            request_type="question"
        )
        
        assert request.request_id == request_id
        assert request.player_input == "How do I buy a ticket?"
        assert request.request_type == "question"
        assert isinstance(request.timestamp, datetime)
        assert request.game_context is None
        assert isinstance(request.additional_params, dict)
    
    def test_companion_request_with_game_context(self, sample_game_context):
        """Test that a CompanionRequest can be created with a game context."""
        request = CompanionRequest(
            request_id="test-123",
            player_input="What does this sign say?",
            request_type="translation",
            game_context=sample_game_context
        )
        
        assert request.game_context is not None
        assert request.game_context.player_location == "main_concourse"
        assert "ticket_machine" in request.game_context.nearby_objects


class TestClassifiedRequest:
    """Tests for the ClassifiedRequest class."""
    
    def test_classified_request_creation(self):
        """Test that a ClassifiedRequest can be created with the required fields."""
        request = ClassifiedRequest(
            request_id="test-456",
            player_input="What is 'kippu'?",
            request_type="vocabulary",
            intent=IntentCategory.VOCABULARY_HELP,
            complexity=ComplexityLevel.SIMPLE,
            processing_tier=ProcessingTier.TIER_1
        )
        
        assert request.request_id == "test-456"
        assert request.player_input == "What is 'kippu'?"
        assert request.intent == IntentCategory.VOCABULARY_HELP
        assert request.complexity == ComplexityLevel.SIMPLE
        assert request.processing_tier == ProcessingTier.TIER_1
        assert request.confidence == 0.0
        assert isinstance(request.extracted_entities, dict)
    
    def test_from_companion_request(self):
        """Test that a ClassifiedRequest can be created from a CompanionRequest."""
        # Create a companion request
        companion_request = CompanionRequest(
            request_id="test-789",
            player_input="How do I say 'ticket' in Japanese?",
            request_type="translation"
        )
        
        # Create a classified request from the companion request
        classified_request = ClassifiedRequest.from_companion_request(
            request=companion_request,
            intent=IntentCategory.VOCABULARY_HELP,
            complexity=ComplexityLevel.SIMPLE,
            processing_tier=ProcessingTier.TIER_1,
            confidence=0.95,
            extracted_entities={"word": "ticket", "language": "Japanese"}
        )
        
        # Check that the fields were copied correctly
        assert classified_request.request_id == companion_request.request_id
        assert classified_request.player_input == companion_request.player_input
        assert classified_request.request_type == companion_request.request_type
        assert classified_request.timestamp == companion_request.timestamp
        
        # Check that the new fields were set correctly
        assert classified_request.intent == IntentCategory.VOCABULARY_HELP
        assert classified_request.complexity == ComplexityLevel.SIMPLE
        assert classified_request.processing_tier == ProcessingTier.TIER_1
        assert classified_request.confidence == 0.95
        assert classified_request.extracted_entities["word"] == "ticket"


class TestCompanionResponse:
    """Tests for the CompanionResponse class."""
    
    def test_companion_response_creation(self):
        """Test that a CompanionResponse can be created with the required fields."""
        response = CompanionResponse(
            request_id="test-789",
            response_text="'Kippu' means 'ticket' in Japanese.",
            intent=IntentCategory.VOCABULARY_HELP,
            processing_tier=ProcessingTier.TIER_1
        )
        
        assert response.request_id == "test-789"
        assert response.response_text == "'Kippu' means 'ticket' in Japanese."
        assert response.intent == IntentCategory.VOCABULARY_HELP
        assert response.processing_tier == ProcessingTier.TIER_1
        assert isinstance(response.timestamp, datetime)
        assert response.emotion == "neutral"
        assert response.confidence == 1.0
        assert isinstance(response.suggested_actions, list)
        assert isinstance(response.learning_cues, dict)
        assert isinstance(response.debug_info, dict)


class TestConversationContext:
    """Tests for the ConversationContext class."""
    
    def test_conversation_context_creation(self):
        """Test that a ConversationContext can be created with the required fields."""
        context = ConversationContext(
            conversation_id="conv-123"
        )
        
        assert context.conversation_id == "conv-123"
        assert isinstance(context.request_history, list)
        assert isinstance(context.response_history, list)
        assert isinstance(context.session_start, datetime)
        assert isinstance(context.last_updated, datetime)
        assert isinstance(context.metadata, dict)
    
    def test_add_interaction(self):
        """Test that interactions can be added to the conversation context."""
        context = ConversationContext(conversation_id="conv-456")
        
        # Create a request and response
        request = CompanionRequest(
            request_id="req-123",
            player_input="How do I get to platform 3?",
            request_type="direction"
        )
        
        response = CompanionResponse(
            request_id="req-123",
            response_text="Follow the signs to your right.",
            intent=IntentCategory.DIRECTION_GUIDANCE,
            processing_tier=ProcessingTier.TIER_1
        )
        
        # Record the last updated time
        last_updated_before = context.last_updated
        
        # Add the interaction
        context.add_interaction(request, response)
        
        # Check that the interaction was added
        assert len(context.request_history) == 1
        assert len(context.response_history) == 1
        assert context.request_history[0].request_id == "req-123"
        assert context.response_history[0].request_id == "req-123"
        
        # Check that last_updated was updated
        assert context.last_updated > last_updated_before 