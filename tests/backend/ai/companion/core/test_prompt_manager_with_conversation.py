"""
Tests for the PromptManager with conversation history integration.
"""

import pytest
import pytest_asyncio
import unittest.mock
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from backend.ai.companion.core.models import (
    ClassifiedRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from backend.ai.companion.core.prompt_manager import PromptManager
from backend.ai.companion.core.conversation_manager import ConversationManager, ConversationState
from backend.ai.companion.core.storage.memory import InMemoryConversationStorage


@pytest.fixture
def sample_classified_request():
    """Create a sample classified request for testing."""
    return ClassifiedRequest(
        request_id="test-request-1",
        player_input="Can you explain more about train tickets?",
        request_type="vocabulary",
        intent=IntentCategory.VOCABULARY_HELP,
        complexity=ComplexityLevel.SIMPLE,
        processing_tier=ProcessingTier.TIER_1,
        confidence=0.9,
        extracted_entities={"topic": "train tickets"},
        timestamp=datetime.now()
    )


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
            "text": "'Kippu' (切符) means 'ticket' in Japanese. It's an important word to know when traveling by train.",
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
            "text": "You can say 'Odawara made no kippu o kudasai'. This literally means 'Please give me a ticket to Odawara'.",
            "timestamp": "2023-05-01T12:01:30",
        }
    ]


@pytest.fixture
def conversation_id():
    """Create a conversation ID for testing."""
    return "test-conversation-1"


@pytest_asyncio.fixture
async def conversation_manager():
    """Create a ConversationManager with in-memory storage for testing."""
    storage = InMemoryConversationStorage()
    manager = ConversationManager(storage=storage)
    return manager


@pytest.mark.asyncio
async def test_create_contextual_prompt_no_history(sample_classified_request):
    """Test creating a contextual prompt when no conversation manager is provided."""
    # Create a PromptManager without a ConversationManager
    prompt_manager = PromptManager()
    
    # Mock the create_prompt method
    original_create_prompt = prompt_manager.create_prompt
    prompt_manager.create_prompt = MagicMock(return_value="Base prompt")
    
    # Call create_contextual_prompt
    prompt = await prompt_manager.create_contextual_prompt(sample_classified_request, "conversation-id")
    
    # Check that create_prompt was called with the request
    prompt_manager.create_prompt.assert_called_once_with(sample_classified_request)
    
    # Check that the prompt is the base prompt
    assert prompt == "Base prompt"
    
    # Restore the original method
    prompt_manager.create_prompt = original_create_prompt


@pytest.mark.asyncio
async def test_create_contextual_prompt_with_new_topic(sample_classified_request, conversation_manager, conversation_id):
    """Test creating a contextual prompt for a new topic."""
    # Create a PromptManager with a ConversationManager
    prompt_manager = PromptManager(conversation_manager=conversation_manager)
    
    # Mock the create_prompt method
    original_create_prompt = prompt_manager.create_prompt
    prompt_manager.create_prompt = MagicMock(return_value="Base prompt")
    
    # Mock the detect_conversation_state method to return NEW_TOPIC
    original_detect_state = conversation_manager.detect_conversation_state
    conversation_manager.detect_conversation_state = MagicMock(return_value=ConversationState.NEW_TOPIC)
    
    # Call create_contextual_prompt
    prompt = await prompt_manager.create_contextual_prompt(sample_classified_request, conversation_id)
    
    # Check that create_prompt was called with the request
    prompt_manager.create_prompt.assert_called_once_with(sample_classified_request)
    
    # Check that the prompt does not contain conversation history
    assert prompt == "Base prompt"
    assert "[{" not in prompt
    
    # Restore the original methods
    prompt_manager.create_prompt = original_create_prompt
    conversation_manager.detect_conversation_state = original_detect_state


@pytest.mark.asyncio
async def test_create_contextual_prompt_with_follow_up(sample_classified_request, sample_conversation_history, conversation_manager, conversation_id):
    """Test creating a contextual prompt for a follow-up question."""
    # Create a PromptManager with a ConversationManager
    prompt_manager = PromptManager(conversation_manager=conversation_manager)
    
    # Mock the create_prompt method
    original_create_prompt = prompt_manager.create_prompt
    prompt_manager.create_prompt = MagicMock(return_value="Base prompt")
    
    # Mock the detect_conversation_state method to return FOLLOW_UP
    original_detect_state = conversation_manager.detect_conversation_state
    conversation_manager.detect_conversation_state = MagicMock(return_value=ConversationState.FOLLOW_UP)
    
    # Mock the get_or_create_context method to return a context with history
    original_get_context = conversation_manager.get_or_create_context
    conversation_manager.get_or_create_context = AsyncMock(return_value={
        "conversation_id": conversation_id,
        "timestamp": datetime.now().isoformat(),
        "entries": sample_conversation_history
    })
    
    # Call create_contextual_prompt
    prompt = await prompt_manager.create_contextual_prompt(sample_classified_request, conversation_id)
    
    # Check that create_prompt was called with the request
    prompt_manager.create_prompt.assert_called_once_with(sample_classified_request)
    
    # Check that the prompt contains conversation history in OpenAI format
    assert "Base prompt" in prompt
    assert "Previous conversation (in OpenAI conversation format)" in prompt
    assert '"role": "user"' in prompt
    assert '"content"' in prompt
    assert '"role": "assistant"' in prompt
    
    # Restore the original methods
    prompt_manager.create_prompt = original_create_prompt
    conversation_manager.detect_conversation_state = original_detect_state
    conversation_manager.get_or_create_context = original_get_context


@pytest.mark.asyncio
async def test_end_to_end_conversation_flow():
    """
    Test the end-to-end flow of conversation history integration.
    This test simulates the flow shown in the example script, but with mock prompt generation.
    """
    # Create storage and managers using in-memory storage for test isolation
    storage = InMemoryConversationStorage()
    conversation_manager = ConversationManager(storage=storage)
    prompt_manager = PromptManager(conversation_manager=conversation_manager)
    
    # Mock the create_prompt method to return a simple string
    original_create_prompt = prompt_manager.create_prompt
    prompt_manager.create_prompt = MagicMock(return_value="Base prompt for test")
    
    # Create a conversation ID for this test
    conversation_id = "test-conversation-flow"
    
    # Create a first request
    first_request = ClassifiedRequest(
        request_id="first-request",
        player_input="What does 'kippu' mean?",
        request_type="vocabulary",
        intent=IntentCategory.VOCABULARY_HELP,
        complexity=ComplexityLevel.SIMPLE,
        processing_tier=ProcessingTier.TIER_1,
        confidence=0.9,
        extracted_entities={"word": "kippu"},
        timestamp=datetime.now()
    )
    
    # Generate a contextual prompt for the first request
    first_prompt = await prompt_manager.create_contextual_prompt(first_request, conversation_id)
    
    # Verify that the first prompt does not include conversation history
    # (as this is the first message in the conversation)
    assert first_prompt == "Base prompt for test"
    assert "Previous conversation" not in first_prompt
    
    # Add an entry to the conversation history
    await conversation_manager.add_to_history(
        conversation_id=conversation_id,
        request=first_request,
        response="'Kippu' (切符) means 'ticket' in Japanese. It's an important word to know when traveling by train."
    )
    
    # Create a second request with phrasing to trigger follow-up detection
    second_request = ClassifiedRequest(
        request_id="second-request",
        player_input="What about asking for a ticket to Odawara?",  # Using "what about" to trigger follow-up detection
        request_type="translation",
        intent=IntentCategory.TRANSLATION_CONFIRMATION,
        complexity=ComplexityLevel.SIMPLE,
        processing_tier=ProcessingTier.TIER_1,
        confidence=0.9,
        extracted_entities={"destination": "Odawara", "word": "kippu"},
        timestamp=datetime.now()
    )
    
    # Generate a contextual prompt for the second request
    second_prompt = await prompt_manager.create_contextual_prompt(second_request, conversation_id)
    
    # Verify that the second prompt includes conversation history
    assert "Base prompt for test" in second_prompt
    assert "Previous conversation (in OpenAI conversation format)" in second_prompt
    assert '"role": "user"' in second_prompt
    assert '"role": "assistant"' in second_prompt
    assert "What does 'kippu' mean?" in second_prompt
    assert "'Kippu'" in second_prompt
    
    # Verify that follow-up instructions are included
    assert "follow-up question" in second_prompt
    
    # Restore the original method
    prompt_manager.create_prompt = original_create_prompt 