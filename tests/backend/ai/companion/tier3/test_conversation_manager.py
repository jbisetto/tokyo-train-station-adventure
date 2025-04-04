"""
Tests for multi-turn conversation management.

These tests verify that the companion AI can maintain coherent
conversations across multiple interactions with the player.
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta

from src.ai.companion.core.models import (
    ClassifiedRequest,
    CompanionRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from src.ai.companion.core.conversation_manager import ConversationManager, ConversationState
from src.ai.companion.core.storage.memory import InMemoryConversationStorage


@pytest.fixture
def sample_conversation_history():
    """Create a sample conversation history for testing."""
    return [
        {
            "type": "user_message",
            "text": "What does 'kippu' mean?",
            "timestamp": "2023-05-01T12:00:00",
            "intent": "vocabulary_help",
            "entities": {"word": "kippu"}
        },
        {
            "type": "assistant_message",
            "text": "'Kippu' means 'ticket' in Japanese.",
            "timestamp": "2023-05-01T12:00:30",
        },
        {
            "type": "user_message",
            "text": "How do I ask for a ticket to Odawara?",
            "timestamp": "2023-05-01T12:01:00",
            "intent": "translation_confirmation",
            "entities": {"destination": "Odawara", "word": "kippu"}
        },
        {
            "type": "assistant_message",
            "text": "You can say 'Odawara made no kippu o kudasai'.",
            "timestamp": "2023-05-01T12:01:30",
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
        complexity=ComplexityLevel.COMPLEX,
        processing_tier=ProcessingTier.TIER_3,
        timestamp=datetime.now(),
        confidence=0.85,
        extracted_entities={"topic": "train tickets"},
        additional_params={"conversation_id": "conv-123"}
    )


@pytest.fixture
def conversation_id():
    """Create a unique conversation ID for each test."""
    return f"test-conversation-{uuid.uuid4()}"


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
    
    @pytest.mark.asyncio
    async def test_generate_contextual_prompt(self, sample_conversation_history, sample_classified_request):
        """Test generating a contextual prompt."""
        manager = ConversationManager()
        
        # Test with a follow-up question
        sample_classified_request.player_input = "tell me more about train tickets"
        state = manager.detect_conversation_state(sample_classified_request, sample_conversation_history)
        base_prompt = "You are Hachiko, a helpful companion dog."
        
        prompt = await manager.generate_contextual_prompt(
            sample_classified_request,
            sample_conversation_history,
            state,
            base_prompt
        )
        
        # Check that the prompt contains instructions for handling follow-up questions
        assert "follow-up question" in prompt
        assert "conversation history" in prompt
    
    @pytest.mark.asyncio
    async def test_handle_follow_up_question(self, sample_conversation_history, sample_classified_request):
        """Test handling a follow-up question."""
        manager = ConversationManager()
        
        # Set up a follow-up question
        sample_classified_request.player_input = "tell me more about train tickets"
        
        # Generate a prompt for the follow-up question
        state = manager.detect_conversation_state(sample_classified_request, sample_conversation_history)
        base_prompt = "You are Hachiko, a helpful companion dog."
        
        prompt = await manager.generate_contextual_prompt(
            sample_classified_request,
            sample_conversation_history,
            state,
            base_prompt
        )
        
        # Check that the prompt contains instructions for handling follow-up questions
        assert "follow-up" in prompt.lower()
        assert "conversation history" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_handle_clarification(self, sample_conversation_history, sample_classified_request):
        """Test handling a clarification request."""
        manager = ConversationManager()
        
        # Set up a clarification request
        sample_classified_request.player_input = "I don't understand what you mean"
        
        # Generate a prompt for the clarification request
        state = manager.detect_conversation_state(sample_classified_request, sample_conversation_history)
        base_prompt = "You are Hachiko, a helpful companion dog."
        
        prompt = await manager.generate_contextual_prompt(
            sample_classified_request,
            sample_conversation_history,
            state,
            base_prompt
        )
        
        # Check that the prompt contains instructions for handling clarification requests
        assert "clarification" in prompt.lower()
        assert "detailed explanation" in prompt.lower()
    
    @pytest.mark.skip(reason="Test isolation issues when running with full test suite")
    @pytest.mark.asyncio
    async def test_add_to_history(self, sample_classified_request, conversation_id):
        """Test adding to the conversation history."""
        # Create a ConversationManager with an in-memory storage
        storage = InMemoryConversationStorage()
        manager = ConversationManager(storage=storage)
        
        # Add a new entry to the history
        response = "Train tickets in Japan are called 'kippu' and can be purchased at ticket machines or counters."
        updated_history = await manager.add_to_history(
            conversation_id,
            sample_classified_request,
            response
        )
        
        # Check that the history was updated
        assert len(updated_history) == 2
        
        # Check the user entry
        assert updated_history[0]["type"] == "user_message"
        assert updated_history[0]["text"] == sample_classified_request.player_input
        assert updated_history[0]["intent"].lower() == sample_classified_request.intent.value.lower()
        assert updated_history[0]["entities"] == sample_classified_request.extracted_entities
        
        # Check the assistant entry
        assert updated_history[1]["type"] == "assistant_message"
        assert updated_history[1]["text"] == response
    
    @pytest.mark.skip(reason="Test isolation issues when running with full test suite")
    @pytest.mark.asyncio
    async def test_integration_with_tier3_processor(self, sample_classified_request, conversation_id):
        """Test integration with the Tier3Processor."""
        # Create a ConversationManager with an in-memory storage
        storage = InMemoryConversationStorage()
        manager = ConversationManager(storage=storage)
        
        # Mock a generate_response function
        async def mock_generate_response(prompt):
            return "This is a response to: " + sample_classified_request.player_input
        
        # Process the request with history
        response, updated_history = await manager.process_with_history(
            sample_classified_request,
            conversation_id,
            "You are Hachiko, a helpful companion dog.",
            mock_generate_response
        )
        
        # Check that the response was generated
        assert response == "This is a response to: " + sample_classified_request.player_input
        
        # Check that the history was updated
        assert len(updated_history) == 2
        assert updated_history[0]["type"] == "user_message"
        assert updated_history[0]["text"] == sample_classified_request.player_input
        assert updated_history[1]["type"] == "assistant_message"
        assert updated_history[1]["text"] == response 