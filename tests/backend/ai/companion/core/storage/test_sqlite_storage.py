"""
Tests for the SQLite conversation storage.
"""

import os
import pytest
import tempfile
import pytest_asyncio
from datetime import datetime, timedelta

from src.ai.companion.core.storage.sqlite import SQLiteConversationStorage


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


@pytest.fixture
def sample_context():
    """Create a sample conversation context for testing."""
    return {
        "conversation_id": "test-conversation-1",
        "timestamp": datetime.now().isoformat(),
        "entries": [
            {
                "type": "user_message",
                "text": "What does 'kippu' mean?",
                "timestamp": datetime.now().isoformat(),
                "intent": "VOCABULARY_HELP",
                "entities": {"word": "kippu"}
            },
            {
                "type": "assistant_message",
                "text": "'Kippu' (切符) means 'ticket' in Japanese. It's an important word to know when traveling by train.",
                "timestamp": datetime.now().isoformat()
            }
        ]
    }


@pytest.mark.asyncio
async def test_save_and_get_context(sqlite_storage):
    """Test saving and retrieving a conversation context."""
    # Create a sample context
    conversation_id = "test-conversation-1"
    sample_context = {
        "conversation_id": conversation_id,
        "timestamp": datetime.now().isoformat(),
        "entries": [
            {
                "type": "user_message",
                "text": "What does 'kippu' mean?",
                "timestamp": datetime.now().isoformat(),
                "intent": "VOCABULARY_HELP",
                "entities": {"word": "kippu"}
            },
            {
                "type": "assistant_message",
                "text": "'Kippu' (切符) means 'ticket' in Japanese. It's an important word to know when traveling by train.",
                "timestamp": datetime.now().isoformat()
            }
        ]
    }
    
    # Save the context
    await sqlite_storage.save_context(conversation_id, sample_context)
    
    # Get the context
    retrieved_context = await sqlite_storage.get_context(conversation_id)
    
    # Check that the retrieved context is the same as the original
    assert retrieved_context["conversation_id"] == sample_context["conversation_id"]
    assert retrieved_context["timestamp"] == sample_context["timestamp"]
    assert len(retrieved_context["entries"]) == len(sample_context["entries"])
    
    # Check the first entry
    assert retrieved_context["entries"][0]["type"] == "user_message"
    assert retrieved_context["entries"][0]["text"] == "What does 'kippu' mean?"
    assert retrieved_context["entries"][0]["intent"] == "VOCABULARY_HELP"
    assert retrieved_context["entries"][0]["entities"]["word"] == "kippu"
    
    # Check the second entry
    assert retrieved_context["entries"][1]["type"] == "assistant_message"
    assert retrieved_context["entries"][1]["text"] == "'Kippu' (切符) means 'ticket' in Japanese. It's an important word to know when traveling by train."


@pytest.mark.asyncio
async def test_list_contexts(sqlite_storage):
    """Test listing conversation contexts."""
    # Sample base context
    base_context = {
        "timestamp": datetime.now().isoformat(),
        "entries": [
            {
                "type": "user_message",
                "text": "Hello",
                "timestamp": datetime.now().isoformat()
            }
        ]
    }
    
    # Save multiple contexts
    for i in range(3):
        context = base_context.copy()
        context["conversation_id"] = f"test-conversation-{i}"
        context["timestamp"] = (datetime.now() - timedelta(days=i)).isoformat()
        await sqlite_storage.save_context(context["conversation_id"], context)
    
    # List all contexts
    contexts = await sqlite_storage.list_contexts()
    
    # Check that we have all three contexts
    assert len(contexts) == 3
    
    # Check that they're ordered by timestamp (newest first)
    assert contexts[0]["conversation_id"] == "test-conversation-0"
    assert contexts[1]["conversation_id"] == "test-conversation-1"
    assert contexts[2]["conversation_id"] == "test-conversation-2"


@pytest.mark.asyncio
async def test_delete_context(sqlite_storage):
    """Test deleting a conversation context."""
    # Create a sample context
    conversation_id = "test-conversation-to-delete"
    sample_context = {
        "conversation_id": conversation_id,
        "timestamp": datetime.now().isoformat(),
        "entries": [
            {
                "type": "user_message",
                "text": "Delete me",
                "timestamp": datetime.now().isoformat()
            }
        ]
    }
    
    # Save the context
    await sqlite_storage.save_context(conversation_id, sample_context)
    
    # Verify it was saved
    assert await sqlite_storage.get_context(conversation_id) is not None
    
    # Delete the context
    await sqlite_storage.delete_context(conversation_id)
    
    # Verify it was deleted
    assert await sqlite_storage.get_context(conversation_id) is None


@pytest.mark.asyncio
async def test_cleanup_old_contexts(sqlite_storage):
    """Test cleaning up old conversation contexts."""
    # Sample base context
    base_context = {
        "entries": [
            {
                "type": "user_message",
                "text": "Test message",
                "timestamp": datetime.now().isoformat()
            }
        ]
    }
    
    # Save contexts with different ages
    for i in range(5):
        context = base_context.copy()
        context["conversation_id"] = f"test-conversation-{i}"
        # Make contexts 0, 1, 2 older than 10 days
        days_offset = 20 if i < 3 else 5
        context["timestamp"] = (datetime.now() - timedelta(days=days_offset)).isoformat()
        await sqlite_storage.save_context(context["conversation_id"], context)
    
    # Clean up contexts older than 10 days
    deleted_count = await sqlite_storage.cleanup_old_contexts(max_age_days=10)
    
    # Check that 3 contexts were deleted
    assert deleted_count == 3
    
    # Check that only the newer contexts remain
    contexts = await sqlite_storage.list_contexts()
    assert len(contexts) == 2
    assert sorted([c["conversation_id"] for c in contexts]) == ["test-conversation-3", "test-conversation-4"] 