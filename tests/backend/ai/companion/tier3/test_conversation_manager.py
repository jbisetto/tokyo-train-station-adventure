"""
Tests for multi-turn conversation management in Tier 3.

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
from backend.ai.companion.tier3.context_manager import (
    ConversationContext,
    ContextManager,
    ContextEntry
)


@pytest.fixture
def sample_context():
    """Create a sample conversation context for testing."""
    context = ConversationContext(
        conversation_id="conv-123",
        player_id="player-456",
        player_language_level="N5",
        current_location="ticket_counter",
        created_at=datetime.now() - timedelta(minutes=10),
        updated_at=datetime.now() - timedelta(minutes=5)
    )
    
    # Add some entries to the context
    context.entries = [
        ContextEntry(
            request="What does 'kippu' mean?",
            response="'Kippu' means 'ticket' in Japanese.",
            timestamp=datetime.now() - timedelta(minutes=5),
            intent=IntentCategory.VOCABULARY_HELP,
            entities={"word": "kippu"}
        ),
        ContextEntry(
            request="How do I ask for a ticket to Odawara?",
            response="You can say 'Odawara made no kippu o kudasai'.",
            timestamp=datetime.now() - timedelta(minutes=3),
            intent=IntentCategory.TRANSLATION_CONFIRMATION,
            entities={"destination": "Odawara"}
        )
    ]
    
    return context


@pytest.fixture
def sample_classified_request():
    """Create a sample classified request for testing."""
    return ClassifiedRequest(
        request_id=str(uuid.uuid4()),
        player_input="What does 'kudasai' mean?",
        request_type="vocabulary",
        timestamp=datetime.now(),
        intent=IntentCategory.VOCABULARY_HELP,
        complexity=ComplexityLevel.COMPLEX,
        processing_tier=ProcessingTier.TIER_3,
        confidence=0.9,
        extracted_entities={"word": "kudasai"},
        additional_params={"conversation_id": "conv-123"}
    )


class TestConversationManager:
    """Tests for the ConversationManager class."""
    
    def test_conversation_manager_creation(self):
        """Test that a ConversationManager can be created."""
        from backend.ai.companion.tier3.conversation_manager import ConversationManager
        
        manager = ConversationManager()
        
        assert manager is not None
        assert hasattr(manager, 'detect_conversation_state')
        assert hasattr(manager, 'generate_contextual_prompt')
        assert hasattr(manager, 'handle_follow_up_question')
    
    def test_detect_conversation_state(self, sample_context, sample_classified_request):
        """Test detecting the state of a conversation."""
        from backend.ai.companion.tier3.conversation_manager import (
            ConversationManager,
            ConversationState
        )
        
        manager = ConversationManager()
        
        # Test with a follow-up question
        sample_classified_request.player_input = "What does 'kudasai' mean in that sentence?"
        state = manager.detect_conversation_state(sample_classified_request, sample_context)
        
        assert state == ConversationState.FOLLOW_UP
        
        # Test with a new topic
        sample_classified_request.player_input = "How do I get to Shinjuku station?"
        state = manager.detect_conversation_state(sample_classified_request, sample_context)
        
        assert state == ConversationState.NEW_TOPIC
        
        # Test with a clarification request
        sample_classified_request.player_input = "Can you explain that again?"
        state = manager.detect_conversation_state(sample_classified_request, sample_context)
        
        assert state == ConversationState.CLARIFICATION
    
    def test_generate_contextual_prompt(self, sample_context, sample_classified_request):
        """Test generating a contextual prompt based on conversation history."""
        from backend.ai.companion.tier3.conversation_manager import (
            ConversationManager,
            ConversationState
        )
        
        manager = ConversationManager()
        
        # Test with a follow-up question
        sample_classified_request.player_input = "What does 'kudasai' mean in that sentence?"
        prompt = manager.generate_contextual_prompt(
            sample_classified_request,
            sample_context,
            ConversationState.FOLLOW_UP
        )
        
        assert "previous exchanges" in prompt
        assert "What does 'kippu' mean?" in prompt
        assert "'Kippu' means 'ticket' in Japanese." in prompt
        assert "How do I ask for a ticket to Odawara?" in prompt
        assert "You can say 'Odawara made no kippu o kudasai'." in prompt
        assert "follow-up question" in prompt
        assert "kudasai" in prompt
    
    def test_handle_follow_up_question(self, sample_context, sample_classified_request):
        """Test handling a follow-up question."""
        from backend.ai.companion.tier3.conversation_manager import ConversationManager
        
        manager = ConversationManager()
        context_manager = MagicMock()
        context_manager.get_context.return_value = sample_context
        
        # Mock the bedrock client
        bedrock_client = MagicMock()
        bedrock_client.generate_text.return_value = "'Kudasai' means 'please' in Japanese."
        
        # Test handling a follow-up question
        sample_classified_request.player_input = "What does 'kudasai' mean in that sentence?"
        response = manager.handle_follow_up_question(
            sample_classified_request,
            context_manager,
            bedrock_client
        )
        
        assert response is not None
        assert "please" in response
        
        # Verify that the bedrock client was called with a prompt containing context
        call_args = bedrock_client.generate_text.call_args[0]
        prompt = call_args[0]
        assert "previous exchanges" in prompt
        assert "What does 'kippu' mean?" in prompt
        assert "'Kippu' means 'ticket' in Japanese." in prompt
        assert "How do I ask for a ticket to Odawara?" in prompt
        assert "You can say 'Odawara made no kippu o kudasai'." in prompt
    
    def test_handle_clarification(self, sample_context, sample_classified_request):
        """Test handling a clarification request."""
        from backend.ai.companion.tier3.conversation_manager import ConversationManager
        
        manager = ConversationManager()
        context_manager = MagicMock()
        context_manager.get_context.return_value = sample_context
        
        # Mock the bedrock client
        bedrock_client = MagicMock()
        bedrock_client.generate_text.return_value = "To ask for a ticket to Odawara, you can say 'Odawara made no kippu o kudasai'. 'Made' means 'to', 'no' is a possessive particle, 'kippu' means 'ticket', and 'kudasai' means 'please'."
        
        # Test handling a clarification request
        sample_classified_request.player_input = "Can you explain that again?"
        response = manager.handle_clarification(
            sample_classified_request,
            context_manager,
            bedrock_client
        )
        
        assert response is not None
        assert "Odawara" in response
        assert "kudasai" in response
        
        # Verify that the bedrock client was called with a prompt containing context
        call_args = bedrock_client.generate_text.call_args[0]
        prompt = call_args[0]
        assert "previous exchanges" in prompt
        assert "clarification" in prompt
        assert "How do I ask for a ticket to Odawara?" in prompt
        assert "You can say 'Odawara made no kippu o kudasai'." in prompt
    
    def test_integration_with_tier3_processor(self, sample_classified_request):
        """Test integration with the Tier3Processor."""
        from backend.ai.companion.tier3.conversation_manager import (
            ConversationManager,
            ConversationState
        )
        
        # Mock the necessary components
        context_manager = MagicMock()
        bedrock_client = MagicMock()
        conversation_manager = ConversationManager()
        
        # Mock the context
        sample_context = MagicMock()
        context_manager.get_context.return_value = sample_context
        
        # Mock the conversation state detection
        with patch.object(
            conversation_manager,
            'detect_conversation_state',
            return_value=ConversationState.FOLLOW_UP
        ):
            # Mock the follow-up handling
            with patch.object(
                conversation_manager,
                'handle_follow_up_question',
                return_value="'Kudasai' means 'please' in Japanese."
            ):
                # Test the process method
                response = conversation_manager.process(
                    sample_classified_request,
                    context_manager,
                    bedrock_client
                )
                
                assert response is not None
                assert "please" in response 