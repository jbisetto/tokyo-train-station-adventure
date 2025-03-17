"""
Tests for multi-turn conversation management.

These tests verify that the companion AI can maintain coherent
conversations across multiple interactions with the player.
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from backend.ai.companion.core.models import (
    ClassifiedRequest,
    CompanionRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from backend.ai.companion.core.conversation_manager import ConversationManager, ConversationState


@pytest.fixture
def sample_conversation_history():
    """Create a sample conversation history for testing."""
    return [
        {
            "request": "What does 'kippu' mean?",
            "response": "'Kippu' means 'ticket' in Japanese.",
            "timestamp": "2023-05-01T12:00:00",
            "intent": "vocabulary_help",
            "entities": {"word": "kippu"}
        },
        {
            "request": "How do I ask for a ticket to Odawara?",
            "response": "You can say 'Odawara made no kippu o kudasai'.",
            "timestamp": "2023-05-01T12:01:00",
            "intent": "translation_confirmation",
            "entities": {"destination": "Odawara", "word": "kippu"}
        }
    ]


@pytest.fixture
def sample_classified_request():
    """Create a sample classified request for testing."""
    return ClassifiedRequest(
        request_id="test-123",
        player_input="Can you explain more about train tickets?",
        request_type="general",
        intent=IntentCategory.GENERAL_HINT,
        complexity="complex",
        processing_tier="tier_3",
        timestamp=datetime.now(),
        confidence=0.85,
        extracted_entities={"topic": "train tickets"},
        additional_params={"conversation_id": "conv-123"}
    )


class TestConversationManager:
    """Tests for the ConversationManager class."""
    
    def test_conversation_manager_creation(self):
        """Test creating a ConversationManager."""
        manager = ConversationManager()
        
        assert manager is not None
        assert hasattr(manager, 'detect_conversation_state')
        assert hasattr(manager, 'generate_contextual_prompt')
        assert hasattr(manager, 'add_to_history')
    
    def test_detect_conversation_state(self, sample_conversation_history, sample_classified_request):
        """Test detecting the conversation state."""
        manager = ConversationManager()
        
        # Test with a follow-up question that matches one of the patterns
        sample_classified_request.player_input = "tell me more about train tickets"
        state = manager.detect_conversation_state(sample_classified_request, sample_conversation_history)
        
        assert state == ConversationState.FOLLOW_UP
        
        # Test with a clarification request
        sample_classified_request.player_input = "I don't understand what you mean"
        state = manager.detect_conversation_state(sample_classified_request, sample_conversation_history)
        
        assert state == ConversationState.CLARIFICATION
        
        # Test with a new topic
        sample_classified_request.player_input = "What time does the train to Tokyo leave?"
        state = manager.detect_conversation_state(sample_classified_request, sample_conversation_history)
        
        assert state == ConversationState.NEW_TOPIC
        
        # Test with a reference to a previous entity
        sample_classified_request.player_input = "How much does a kippu cost?"
        state = manager.detect_conversation_state(sample_classified_request, sample_conversation_history)
        
        assert state == ConversationState.FOLLOW_UP
    
    def test_generate_contextual_prompt(self, sample_conversation_history, sample_classified_request):
        """Test generating a contextual prompt."""
        manager = ConversationManager()
        
        # Test with a follow-up question
        sample_classified_request.player_input = "tell me more about train tickets"
        state = manager.detect_conversation_state(sample_classified_request, sample_conversation_history)
        base_prompt = "You are Hachiko, a helpful companion dog."
        
        prompt = manager.generate_contextual_prompt(
            sample_classified_request,
            sample_conversation_history,
            state,
            base_prompt
        )
        
        # Check that the prompt contains the conversation history
        assert "What does 'kippu' mean?" in prompt
        assert "'Kippu' means 'ticket' in Japanese." in prompt
        assert "How do I ask for a ticket to Odawara?" in prompt
        assert "You can say 'Odawara made no kippu o kudasai'." in prompt
        
        # Check that the prompt contains instructions for handling follow-up questions
        assert "follow-up question" in prompt
        assert "conversation history" in prompt
    
    def test_handle_follow_up_question(self, sample_conversation_history, sample_classified_request):
        """Test handling a follow-up question."""
        manager = ConversationManager()
        
        # Set up a follow-up question
        sample_classified_request.player_input = "tell me more about train tickets"
        
        # Generate a prompt for the follow-up question
        state = manager.detect_conversation_state(sample_classified_request, sample_conversation_history)
        base_prompt = "You are Hachiko, a helpful companion dog."
        
        prompt = manager.generate_contextual_prompt(
            sample_classified_request,
            sample_conversation_history,
            state,
            base_prompt
        )
        
        # Check that the prompt contains instructions for handling follow-up questions
        assert "follow-up" in prompt.lower()
        assert "conversation history" in prompt.lower()
    
    def test_handle_clarification(self, sample_conversation_history, sample_classified_request):
        """Test handling a clarification request."""
        manager = ConversationManager()
        
        # Set up a clarification request
        sample_classified_request.player_input = "I don't understand what you mean"
        
        # Generate a prompt for the clarification request
        state = manager.detect_conversation_state(sample_classified_request, sample_conversation_history)
        base_prompt = "You are Hachiko, a helpful companion dog."
        
        prompt = manager.generate_contextual_prompt(
            sample_classified_request,
            sample_conversation_history,
            state,
            base_prompt
        )
        
        # Check that the prompt contains instructions for handling clarification requests
        assert "clarification" in prompt.lower()
        assert "detailed explanation" in prompt.lower()
    
    def test_add_to_history(self, sample_conversation_history, sample_classified_request):
        """Test adding to the conversation history."""
        manager = ConversationManager()
        
        # Add a new entry to the history
        response = "Train tickets in Japan are called 'kippu' and can be purchased at ticket machines or counters."
        updated_history = manager.add_to_history(
            sample_conversation_history,
            sample_classified_request,
            response
        )
        
        # Check that the history was updated
        assert len(updated_history) == 3
        assert updated_history[2]["request"] == sample_classified_request.player_input
        assert updated_history[2]["response"] == response
        assert updated_history[2]["intent"] == sample_classified_request.intent.value
        assert updated_history[2]["entities"] == sample_classified_request.extracted_entities
    
    def test_integration_with_tier3_processor(self, sample_conversation_history, sample_classified_request):
        """Test integration with the Tier3Processor."""
        manager = ConversationManager()
        
        # Mock a generate_response function
        def generate_response(prompt):
            return "This is a response to: " + sample_classified_request.player_input
        
        # Process the request with history
        response, updated_history = manager.process_with_history(
            sample_classified_request,
            sample_conversation_history,
            "You are Hachiko, a helpful companion dog.",
            generate_response
        )
        
        # Check that the response was generated
        assert response == "This is a response to: " + sample_classified_request.player_input
        
        # Check that the history was updated
        assert len(updated_history) == 3
        assert updated_history[2]["request"] == sample_classified_request.player_input
        assert updated_history[2]["response"] == response 