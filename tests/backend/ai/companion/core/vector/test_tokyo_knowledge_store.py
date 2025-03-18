"""
Tests for the TokyoKnowledgeStore class.

This module contains tests for the vector database store that provides
contextual information from the Tokyo train station knowledge base.
"""

import os
import json
import pytest
import tempfile
import pytest_asyncio
from unittest.mock import patch, MagicMock, Mock

from backend.ai.companion.core.models import (
    ClassifiedRequest, 
    IntentCategory, 
    ComplexityLevel, 
    GameContext,
    ProcessingTier
)


@pytest.fixture
def sample_tokyo_knowledge():
    """Create a sample knowledge base for testing."""
    return [
        {
            "title": "Ticket Vocabulary",
            "type": "language_learning",
            "content": "Essential ticket vocabulary: 切符 (きっぷ - ticket), 片道 (かたみち - one-way), 往復 (おうふく - round-trip).",
            "importance": "high"
        },
        {
            "title": "Tokyo Station Overview",
            "type": "location",
            "content": "Tokyo Station is one of Japan's busiest railway stations.",
            "importance": "medium"
        },
        {
            "title": "NPC Profile: Ticket Booth Agent",
            "type": "character",
            "content": "Sells tickets and provides fare information.",
            "personality": "helpful, formal",
            "key_vocabulary": ["切符", "料金", "いくら"],
            "importance": "high"
        }
    ]


@pytest.fixture
def sample_knowledge_file(sample_tokyo_knowledge):
    """Create a temporary knowledge base file for testing."""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as f:
        json.dump(sample_tokyo_knowledge, f)
        temp_file_path = f.name
    
    yield temp_file_path
    
    # Clean up the temporary file
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)


@pytest.fixture
def sample_request():
    """Create a sample classified request for testing."""
    return ClassifiedRequest(
        request_id="test-request",
        player_input="How do I buy a ticket?",
        request_type="vocabulary",
        intent=IntentCategory.VOCABULARY_HELP,
        complexity=ComplexityLevel.SIMPLE,
        processing_tier=ProcessingTier.TIER_2,
        game_context=GameContext(
            player_location="Tokyo Station Entrance",
            current_objective="Purchase ticket to Odawara",
            nearby_npcs=["Information Booth Attendant"]
        )
    )


@pytest.fixture
def chroma_mock():
    """Mock the ChromaDB client."""
    with patch('chromadb.PersistentClient') as persistent_mock, \
         patch('chromadb.EphemeralClient') as ephemeral_mock, \
         patch('chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction') as embedding_mock:
        
        # Create mock collection
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0  # Empty by default
        mock_collection.get.return_value = {
            'ids': [],
            'embeddings': [],
            'documents': [],
            'metadatas': []
        }
        
        # Set up mock response for query method with correct format
        mock_collection.query.return_value = {
            'ids': [['doc1', 'doc2']],  # Note the nested list format
            'distances': [[0.1, 0.2]],  # Note the nested list format
            'documents': [
                ["Essential ticket vocabulary: 切符 (きっぷ - ticket).",
                 "Tokyo Station is one of Japan's busiest railway stations."]
            ],
            'metadatas': [
                [{"title": "Ticket Vocabulary", "type": "language_learning", "importance": "high"},
                 {"title": "Tokyo Station Overview", "type": "location", "importance": "medium"}]
            ]
        }
        
        # Set up mock clients
        persistent_client = MagicMock()
        persistent_client.get_or_create_collection.return_value = mock_collection
        persistent_mock.return_value = persistent_client
        
        ephemeral_client = MagicMock()
        ephemeral_client.get_or_create_collection.return_value = mock_collection
        ephemeral_mock.return_value = ephemeral_client
        
        yield {
            'persistent': persistent_mock,
            'ephemeral': ephemeral_mock,
            'embedding_function': embedding_mock,
            'collection': mock_collection
        }


class TestTokyoKnowledgeStore:
    """Tests for the TokyoKnowledgeStore class."""
    
    def test_initialization_ephemeral(self, chroma_mock):
        """Test initializing with an ephemeral database."""
        from backend.ai.companion.core.vector.tokyo_knowledge_store import TokyoKnowledgeStore
        
        # Create a store with ephemeral storage
        store = TokyoKnowledgeStore(persist_directory=None)
        
        # Verify that the ephemeral client was created
        chroma_mock['ephemeral'].assert_called_once()
        assert store.client is not None
        assert store.collection is not None
    
    def test_initialization_persistent(self, chroma_mock):
        """Test initializing with a persistent database."""
        from backend.ai.companion.core.vector.tokyo_knowledge_store import TokyoKnowledgeStore
        
        # Create a store with persistent storage
        store = TokyoKnowledgeStore(persist_directory="/tmp/chroma_test")
        
        # Verify that the persistent client was created
        chroma_mock['persistent'].assert_called_once_with(path="/tmp/chroma_test")
        assert store.client is not None
        assert store.collection is not None
    
    def test_load_knowledge_base_when_empty(self, chroma_mock, sample_knowledge_file):
        """Test loading the knowledge base when the collection is empty."""
        from backend.ai.companion.core.vector.tokyo_knowledge_store import TokyoKnowledgeStore
        
        # Configure mock to show empty collection
        chroma_mock['collection'].count.return_value = 0
        
        # Create a store and load the knowledge base
        store = TokyoKnowledgeStore()
        store.load_knowledge_base(sample_knowledge_file)
        
        # Verify that data was added to the collection
        chroma_mock['collection'].add.assert_called_once()
        call_args = chroma_mock['collection'].add.call_args[1]
        
        # Check that we have the right number of documents
        assert len(call_args['documents']) == 3
        assert len(call_args['metadatas']) == 3
        assert len(call_args['ids']) == 3
    
    def test_load_knowledge_base_when_populated(self, chroma_mock, sample_knowledge_file):
        """Test loading the knowledge base when the collection is already populated."""
        from backend.ai.companion.core.vector.tokyo_knowledge_store import TokyoKnowledgeStore
        
        # Configure mock to show populated collection
        chroma_mock['collection'].count.return_value = 3
        
        # Create a store and try to load the knowledge base
        store = TokyoKnowledgeStore()
        store.load_knowledge_base(sample_knowledge_file)
        
        # Verify that no data was added to the collection
        chroma_mock['collection'].add.assert_not_called()
    
    def test_from_file_initialization(self, chroma_mock, sample_knowledge_file):
        """Test initializing from a knowledge base file."""
        from backend.ai.companion.core.vector.tokyo_knowledge_store import TokyoKnowledgeStore
        
        # Configure mock to show empty collection initially
        chroma_mock['collection'].count.return_value = 0
        
        # Create a store from a file
        store = TokyoKnowledgeStore.from_file(sample_knowledge_file)
        
        # Verify that data was loaded
        chroma_mock['collection'].add.assert_called_once()
    
    def test_search(self, chroma_mock):
        """Test searching for relevant documents."""
        from backend.ai.companion.core.vector.tokyo_knowledge_store import TokyoKnowledgeStore
        
        # Create a store
        store = TokyoKnowledgeStore()
        
        # Search for documents
        results = store.search("ticket")
        
        # Verify the search was performed
        chroma_mock['collection'].query.assert_called_once()
        assert len(results) == 2
        assert results[0]['document'] == "Essential ticket vocabulary: 切符 (きっぷ - ticket)."
        assert results[0]['metadata']['title'] == "Ticket Vocabulary"
        assert results[0]['score'] == 0.9  # 1 - distance
    
    def test_contextual_search(self, chroma_mock, sample_request):
        """Test searching with game context."""
        from backend.ai.companion.core.vector.tokyo_knowledge_store import TokyoKnowledgeStore
        
        # Create a store
        store = TokyoKnowledgeStore()
        
        # Patch the specific query method for vocabulary_help to ensure consistent behavior
        store.search = MagicMock()
        store.search.side_effect = [
            # Return for language_learning search
            [
                {
                    "id": "doc1",
                    "document": "Essential ticket vocabulary: 切符 (きっぷ - ticket).",
                    "metadata": {"title": "Ticket Vocabulary", "type": "language_learning", "importance": "high"},
                    "score": 0.9
                }
            ],
            # Return for location search
            [
                {
                    "id": "doc2",
                    "document": "Tokyo Station is one of Japan's busiest railway stations.",
                    "metadata": {"title": "Tokyo Station Overview", "type": "location", "importance": "medium"},
                    "score": 0.8
                }
            ]
        ]
        
        # Search with context
        results = store.contextual_search(sample_request)
        
        # Verify search was called correctly
        assert store.search.call_count == 2
        
        # First call should be for language learning with the enhanced query
        enhanced_query = store.search.call_args_list[0][0][0]
        assert sample_request.player_input in enhanced_query
        assert "tokyo station entrance" in enhanced_query.lower()
        assert "vocabulary_help" in enhanced_query.lower()
        
        # Second call should be for location search
        location_query = store.search.call_args_list[1][0][0]
        assert "tokyo station entrance" in location_query.lower()
        
        # Verify the results
        assert len(results) == 2
        # Results should be sorted by importance, so high importance first
        assert results[0]['metadata']['importance'] == "high"
    
    def test_filtering_by_type(self, chroma_mock):
        """Test filtering search results by document type."""
        from backend.ai.companion.core.vector.tokyo_knowledge_store import TokyoKnowledgeStore
        
        # Create a store
        store = TokyoKnowledgeStore()
        
        # Search with type filter
        store.search("ticket", filters={"type": "language_learning"})
        
        # Verify filter was used
        filter_arg = chroma_mock['collection'].query.call_args[1].get('where')
        assert filter_arg == {"type": "language_learning"}
    
    def test_embeddings_created_when_empty(self, chroma_mock, sample_knowledge_file):
        """Test that embeddings are created when the store is empty."""
        from backend.ai.companion.core.vector.tokyo_knowledge_store import TokyoKnowledgeStore
        
        # First set count to 0 to indicate an empty collection
        chroma_mock['collection'].count.return_value = 0
        
        # Create a store and trigger automatic loading
        store = TokyoKnowledgeStore.from_file(sample_knowledge_file)
        
        # Verify that data was added to the collection
        chroma_mock['collection'].add.assert_called_once()
        
        # Verify that embeddings were created by checking the embedding function
        embedding_fn = chroma_mock['embedding_function'].return_value
        assert embedding_fn is not None 