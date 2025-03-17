"""
Tests for the ConversationManager with persistent storage.
"""

import os
import pytest
import tempfile
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from dataclasses import replace

from backend.ai.companion.core.models import (
    ClassifiedRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from backend.ai.companion.core.conversation_manager import ConversationManager, ConversationState
from backend.ai.companion.core.storage.sqlite import SQLiteConversationStorage


@pytest.fixture
def sample_classified_request():
    """Create a sample classified request for testing."""
    return ClassifiedRequest(
        request_id="test-request-1",
        player_input="What does 'kippu' mean?",
        request_type="vocabulary",
        intent=IntentCategory.VOCABULARY_HELP,
        complexity=ComplexityLevel.SIMPLE,
        processing_tier=ProcessingTier.TIER_1,
        confidence=0.9,
        extracted_entities={"word": "kippu"},
        timestamp=datetime.now()
    )


@pytest_asyncio.fixture
async def sqlite_storage():
    """Create a temporary SQLite storage for testing."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Use a temporary database file
        db_path = os.path.join(temp_dir, "test_conversations.db")
        
        # Create a storage instance
        storage = SQLiteConversationStorage(database_path=db_path)
        
        # Initialize the database
        await storage._init_db()
        
        yield storage
        # No cleanup needed as tempfile will clean up


@pytest_asyncio.fixture
async def conversation_manager(sqlite_storage):
    """Create a ConversationManager with SQLite storage for testing."""
    manager = ConversationManager(
        tier_specific_config={"max_history_size": 5},
        storage=sqlite_storage
    )
    
    yield manager


@pytest.mark.asyncio
async def test_get_or_create_context(conversation_manager):
    """Test getting or creating a conversation context."""
    conversation_id = "test-conversation-1"
    
    # Get a context that doesn't exist yet
    context = await conversation_manager.get_or_create_context(conversation_id)
    
    # Check that a new context was created
    assert context["conversation_id"] == conversation_id
    assert "timestamp" in context
    assert context["entries"] == []
    
    # Get the same context again
    context2 = await conversation_manager.get_or_create_context(conversation_id)
    
    # Check that we got the same context
    assert context2["conversation_id"] == context["conversation_id"]
    assert context2["timestamp"] == context["timestamp"]


@pytest.mark.asyncio
async def test_add_entry(conversation_manager):
    """Test adding an entry to a conversation context."""
    conversation_id = "test-conversation-1"
    
    # Add an entry
    entry = {
        "type": "user_message",
        "text": "Hello!",
        "timestamp": datetime.now().isoformat()
    }
    
    await conversation_manager.add_entry(conversation_id, entry)
    
    # Get the context
    context = await conversation_manager.get_or_create_context(conversation_id)
    
    # Check that the entry was added
    assert len(context["entries"]) == 1
    assert context["entries"][0]["type"] == "user_message"
    assert context["entries"][0]["text"] == "Hello!"


@pytest.mark.asyncio
async def test_add_to_history(conversation_manager, sample_classified_request):
    """Test adding a request-response pair to the conversation history."""
    conversation_id = "test-conversation-1"
    response = "'Kippu' (切符) means 'ticket' in Japanese."
    
    # Add the request-response pair to the history
    updated_history = await conversation_manager.add_to_history(
        conversation_id,
        sample_classified_request,
        response
    )
    
    # Check that the history has two entries (request and response)
    assert len(updated_history) == 2
    
    # Check the request entry
    assert updated_history[0]["type"] == "user_message"
    assert updated_history[0]["text"] == "What does 'kippu' mean?"
    assert updated_history[0]["intent"].lower() == "vocabulary_help"
    assert updated_history[0]["entities"]["word"] == "kippu"
    
    # Check the response entry
    assert updated_history[1]["type"] == "assistant_message"
    assert updated_history[1]["text"] == "'Kippu' (切符) means 'ticket' in Japanese."


@pytest.mark.asyncio
async def test_process_with_history(conversation_manager, sample_classified_request):
    """Test processing a request with conversation history."""
    conversation_id = "test-conversation-1"
    base_prompt = "You are a helpful assistant."
    
    # Mock the generate_response_func
    async def mock_generate_response(prompt):
        return "'Kippu' (切符) means 'ticket' in Japanese."
    
    # Process the request
    response, updated_history = await conversation_manager.process_with_history(
        sample_classified_request,
        conversation_id,
        base_prompt,
        mock_generate_response
    )
    
    # Check the response
    assert response == "'Kippu' (切符) means 'ticket' in Japanese."
    
    # Check that the history has two entries (request and response)
    assert len(updated_history) == 2
    
    # Add another request-response pair
    # Use replace instead of copy for dataclasses
    sample_classified_request2 = replace(
        sample_classified_request,
        request_id="test-request-2",
        player_input="How do I use it?"
    )
    
    # Process the second request
    response2, updated_history2 = await conversation_manager.process_with_history(
        sample_classified_request2,
        conversation_id,
        base_prompt,
        mock_generate_response
    )
    
    # Check that the history now has four entries
    assert len(updated_history2) == 4


@pytest.mark.asyncio
async def test_history_persistence(sqlite_storage, sample_classified_request):
    """Test that conversation history persists across manager instances."""
    conversation_id = "test-conversation-1"
    base_prompt = "You are a helpful assistant."
    
    # Mock the generate_response_func
    async def mock_generate_response(prompt):
        return "'Kippu' (切符) means 'ticket' in Japanese."
    
    # Create a first manager and add some history
    manager1 = ConversationManager(
        tier_specific_config={"max_history_size": 5},
        storage=sqlite_storage
    )
    
    # Process a request with the first manager
    await manager1.process_with_history(
        sample_classified_request,
        conversation_id,
        base_prompt,
        mock_generate_response
    )
    
    # Create a second manager with the same storage
    manager2 = ConversationManager(
        tier_specific_config={"max_history_size": 5},
        storage=sqlite_storage
    )
    
    # Get the entries from the second manager
    entries = await manager2.get_entries(conversation_id)
    
    # Check that the history is accessible from the second manager
    assert len(entries) == 2
    assert entries[0]["type"] == "user_message"
    assert entries[0]["text"] == "What does 'kippu' mean?"
    assert entries[1]["type"] == "assistant_message"
    assert entries[1]["text"] == "'Kippu' (切符) means 'ticket' in Japanese." 