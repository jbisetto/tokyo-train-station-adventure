"""
Tests for the Ollama client.

This module contains tests for the Ollama client used by the Tier 2 processor
to interact with local language models.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
import time

from backend.ai.companion.core.models import (
    CompanionRequest,
    IntentCategory,
    ComplexityLevel
)


@pytest.fixture
def sample_request():
    """Create a sample request for testing."""
    return CompanionRequest(
        request_id="test-123",
        player_input="How do I say 'I want to go to Tokyo' in Japanese?",
        request_type="translation"
    )


@pytest.fixture
def sample_ollama_response():
    """Create a sample response from Ollama API."""
    return {
        "model": "llama3",
        "created_at": "2023-11-15T12:34:56Z",
        "response": "「東京に行きたいです」(Tōkyō ni ikitai desu) is how you say 'I want to go to Tokyo' in Japanese.",
        "done": True,
        "context": [1, 2, 3, 4],  # Simplified context representation
        "total_duration": 1234567890,
        "load_duration": 123456789,
        "prompt_eval_count": 10,
        "prompt_eval_duration": 12345678,
        "eval_count": 40,
        "eval_duration": 123456789
    }


@pytest.fixture
def sample_ollama_error_response():
    """Create a sample error response from Ollama API."""
    return {
        "error": "model 'nonexistent' not found, try pulling it first"
    }


@pytest.fixture
def sample_cache_entry():
    """Create a sample cache entry."""
    return {
        "request_hash": "abc123",
        "response": "「東京に行きたいです」(Tōkyō ni ikitai desu) is how you say 'I want to go to Tokyo' in Japanese.",
        "model": "llama3",
        "timestamp": "2023-11-15T12:34:56Z"
    }


class TestOllamaClient:
    """Tests for the OllamaClient class."""

    def test_initialization(self):
        """Test that the OllamaClient can be initialized."""
        from backend.ai.companion.tier2.ollama_client import OllamaClient

        client = OllamaClient()
        
        assert client is not None
        assert hasattr(client, 'generate')
        assert hasattr(client, 'get_available_models')
        assert client.base_url == "http://localhost:11434"
        assert client.default_model == "llama3"
        
        # Test with custom parameters
        client = OllamaClient(
            base_url="http://custom:11434",
            default_model="mistral",
            cache_enabled=False
        )
        
        assert client.base_url == "http://custom:11434"
        assert client.default_model == "mistral"
        assert client.cache_enabled is False

    @pytest.mark.asyncio
    async def test_generate(self, sample_request, sample_ollama_response):
        """Test generating a response from Ollama."""
        from backend.ai.companion.tier2.ollama_client import OllamaClient
        
        # Disable caching for this test
        client = OllamaClient(cache_enabled=False)
        
        # Mock the _call_ollama_api method directly
        with patch.object(client, '_call_ollama_api') as mock_api_call:
            mock_api_call.return_value = sample_ollama_response["response"]
            
            # Call the generate method
            response = await client.generate(sample_request)
            
            # Check that the response was returned
            assert response is not None
            assert "東京に行きたいです" in response
            assert "Tōkyō ni ikitai desu" in response
            
            # Check that the API was called
            assert mock_api_call.called
            # Use assert_called_once() instead of checking specific arguments
            mock_api_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_with_custom_model(self, sample_request, sample_ollama_response):
        """Test generating a response with a custom model."""
        from backend.ai.companion.tier2.ollama_client import OllamaClient
        
        # Disable caching for this test
        client = OllamaClient(cache_enabled=False)
        
        # Mock the _call_ollama_api method directly
        with patch.object(client, '_call_ollama_api') as mock_api_call:
            mock_api_call.return_value = sample_ollama_response["response"]
            
            # Call the generate method with a custom model
            response = await client.generate(sample_request, model="mistral")
            
            # Check that the API was called once
            mock_api_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_with_error(self, sample_request, sample_ollama_error_response):
        """Test handling errors from Ollama."""
        from backend.ai.companion.tier2.ollama_client import OllamaClient, OllamaError
        
        # Disable caching for this test
        client = OllamaClient(cache_enabled=False)
        
        # Mock the _call_ollama_api method to raise an exception
        with patch.object(client, '_call_ollama_api') as mock_api_call:
            error_message = f"Failed to generate response: {sample_ollama_error_response['error']}"
            mock_api_call.side_effect = OllamaError(error_message)
            
            # Check that an error is raised
            with pytest.raises(OllamaError) as excinfo:
                await client.generate(sample_request)
            
            # Check the error message
            assert "model 'nonexistent' not found" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_get_available_models(self):
        """Test getting available models from Ollama."""
        from backend.ai.companion.tier2.ollama_client import OllamaClient
        
        client = OllamaClient()
        
        # Mock the aiohttp ClientSession
        with patch('aiohttp.ClientSession') as mock_session:
            mock_cm = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_cm
            
            # Mock the get method
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama3"},
                    {"name": "mistral"},
                    {"name": "gemma"}
                ]
            }
            mock_cm.get.return_value.__aenter__.return_value = mock_response
            
            # Call the get_available_models method
            models = await client.get_available_models()
            
            # Check that the models were returned
            assert models is not None
            assert len(models) == 3
            assert "llama3" in models
            assert "mistral" in models
            assert "gemma" in models
            
            # Check that the correct URL was used
            mock_cm.get.assert_called_once_with("http://localhost:11434/api/tags")

    @pytest.mark.asyncio
    async def test_cache_hit(self, sample_request, sample_cache_entry):
        """Test that the cache is used when available."""
        from backend.ai.companion.tier2.ollama_client import OllamaClient
        
        client = OllamaClient(cache_enabled=True)
        
        # Mock the cache
        with patch.object(client, '_get_from_cache') as mock_get_cache:
            mock_get_cache.return_value = sample_cache_entry["response"]
            
            # Call the generate method
            response = await client.generate(sample_request)
            
            # Check that the response was returned from the cache
            assert response == sample_cache_entry["response"]
            mock_get_cache.assert_called_once()
            
            # The API should not be called
            assert not hasattr(client, '_last_api_call')

    @pytest.mark.asyncio
    async def test_cache_miss(self, sample_request, sample_ollama_response):
        """Test that the API is called when the cache is missed."""
        from backend.ai.companion.tier2.ollama_client import OllamaClient
        
        client = OllamaClient(cache_enabled=True)
        
        # Mock the cache miss and API call
        with patch.object(client, '_get_from_cache') as mock_get_cache, \
             patch.object(client, '_call_ollama_api') as mock_api_call:
            
            mock_get_cache.return_value = None
            mock_api_call.return_value = sample_ollama_response["response"]
            
            # Call the generate method
            response = await client.generate(sample_request)
            
            # Check that the API was called
            assert response == sample_ollama_response["response"]
            mock_get_cache.assert_called_once()
            mock_api_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_update(self, sample_request, sample_ollama_response):
        """Test that the cache is updated after an API call."""
        from backend.ai.companion.tier2.ollama_client import OllamaClient
        
        client = OllamaClient(cache_enabled=True)
        
        # Mock the cache miss, API call, and cache update
        with patch.object(client, '_get_from_cache') as mock_get_cache, \
             patch.object(client, '_call_ollama_api') as mock_api_call, \
             patch.object(client, '_save_to_cache') as mock_save_cache:
            
            mock_get_cache.return_value = None
            mock_api_call.return_value = sample_ollama_response["response"]
            
            # Call the generate method
            response = await client.generate(sample_request)
            
            # Check that the cache was updated
            assert response == sample_ollama_response["response"]
            mock_save_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_memory_cache(self, sample_request, sample_ollama_response):
        """Test that the memory cache is used before disk cache."""
        from backend.ai.companion.tier2.ollama_client import OllamaClient
        
        client = OllamaClient(cache_enabled=True)
        
        # Mock the API call and cache methods
        with patch.object(client, '_call_ollama_api') as mock_api_call, \
             patch.object(client, '_check_cache', return_value=None), \
             patch.object(client, '_save_to_cache'):
            
            mock_api_call.return_value = sample_ollama_response["response"]
            
            # First call should hit the API
            response1 = await client.generate(sample_request)
            assert response1 == sample_ollama_response["response"]
            mock_api_call.assert_called_once()
            
            # Reset the mock to verify it's not called again
            mock_api_call.reset_mock()
            
            # Add to memory cache directly
            cache_key = client._hash_request(sample_request, client.default_model)
            client._memory_cache[cache_key] = {
                "response": sample_ollama_response["response"],
                "timestamp": time.time()
            }
            
            # Patch _check_cache to return from memory cache
            with patch.object(client, '_check_cache', return_value=sample_ollama_response["response"]):
                # Second call with the same request should use memory cache
                response2 = await client.generate(sample_request)
                assert response2 == sample_ollama_response["response"]
                mock_api_call.assert_not_called()

    def test_cache_ttl(self, sample_request, sample_cache_entry):
        """Test that cache entries expire based on TTL."""
        from backend.ai.companion.tier2.ollama_client import OllamaClient
        import time
        
        # Create client with a very short TTL for testing
        client = OllamaClient(cache_enabled=True, cache_ttl=1)  # 1 second TTL
        
        # Mock the cache methods
        with patch.object(client, '_save_to_cache') as mock_save, \
             patch.object(client, '_get_from_cache', return_value=None):
            
            # Add an entry to the memory cache directly
            request_hash = client._hash_request(sample_request, client.default_model)
            client._memory_cache[request_hash] = {
                "response": sample_cache_entry["response"],
                "timestamp": time.time()
            }
            
            # Verify it's in the cache
            assert request_hash in client._memory_cache
            
            # Wait for TTL to expire
            time.sleep(1.1)
            
            # The entry should be considered expired
            assert client._is_cache_entry_expired(client._memory_cache[request_hash])

    def test_cache_stats(self, sample_request, sample_ollama_response):
        """Test that cache statistics are tracked correctly."""
        from backend.ai.companion.tier2.ollama_client import OllamaClient
        
        client = OllamaClient(cache_enabled=True)
        
        # Reset cache stats
        client.cache_stats = {
            "hits": 0,
            "misses": 0,
            "memory_hits": 0,
            "disk_hits": 0,
            "api_calls": 0,
            "cache_size": 0,
            "entries": 0
        }
        
        # Check initial stats
        assert client.cache_stats["hits"] == 0
        assert client.cache_stats["misses"] == 0
        
        # Mock a cache hit
        with patch.object(client, '_get_from_cache') as mock_get_cache:
            mock_get_cache.return_value = sample_ollama_response["response"]
            
            # This should be a hit
            result = client._check_cache(client._hash_request(sample_request, client.default_model))
            assert result == sample_ollama_response["response"]
            assert client.cache_stats["hits"] == 1
            
        # Reset stats
        client.cache_stats["hits"] = 0
        client.cache_stats["misses"] = 0
        
        # Mock a cache miss by patching both memory cache and disk cache
        client._memory_cache = {}  # Empty memory cache
        with patch.object(client, '_get_from_cache', return_value=None):  # No disk cache hit
            # This should be a miss
            result = client._check_cache(client._hash_request(sample_request, client.default_model))
            assert result is None
            assert client.cache_stats["misses"] == 1

    def test_clear_cache(self):
        """Test clearing the cache."""
        from backend.ai.companion.tier2.ollama_client import OllamaClient
        import os
        
        # Create a client with a test cache directory
        test_cache_dir = "test_cache_dir"
        client = OllamaClient(cache_enabled=True, cache_dir=test_cache_dir)
        
        # Mock the cache directory operations
        with patch('os.path.exists', return_value=True), \
             patch('os.listdir', return_value=["cache1.json", "cache2.json"]), \
             patch('os.remove') as mock_remove, \
             patch.dict(client._memory_cache, {"key1": "value1", "key2": "value2"}):
            
            # Clear the cache
            client.clear_cache()
            
            # Check that files were removed
            assert mock_remove.call_count == 2
            
            # Check that memory cache was cleared
            assert len(client._memory_cache) == 0
            
            # Check that stats were reset
            assert client.cache_stats["hits"] == 0
            assert client.cache_stats["misses"] == 0

    def test_prune_cache(self):
        """Test pruning old cache entries."""
        from backend.ai.companion.tier2.ollama_client import OllamaClient
        import time
        
        # Create client with cache enabled
        client = OllamaClient(cache_enabled=True)
        
        # Create some test cache entries with different timestamps
        now = time.time()
        old_time = now - 86400 * 2  # 2 days old
        
        # Add entries to memory cache
        client._memory_cache = {
            "recent1": {"response": "response1", "timestamp": now},
            "recent2": {"response": "response2", "timestamp": now - 3600},  # 1 hour old
            "old1": {"response": "response3", "timestamp": old_time},
            "old2": {"response": "response4", "timestamp": old_time - 3600}
        }
        
        # Mock the disk cache operations
        with patch('os.path.exists', return_value=True), \
             patch('os.listdir', return_value=["recent1.json", "recent2.json", "old1.json", "old2.json"]), \
             patch('os.path.getmtime', side_effect=lambda f: old_time if "old" in f else now), \
             patch('os.remove') as mock_remove:
            
            # Prune the cache
            client.prune_cache(max_age=86400)  # 1 day max age
            
            # Check that old files were removed
            assert mock_remove.call_count == 2
            
            # Check that old entries were removed from memory cache
            assert "recent1" in client._memory_cache
            assert "recent2" in client._memory_cache
            assert "old1" not in client._memory_cache
            assert "old2" not in client._memory_cache

    @pytest.mark.asyncio
    async def test_cache_size_limit(self, sample_request, sample_ollama_response):
        """Test that the cache respects size limits."""
        from backend.ai.companion.tier2.ollama_client import OllamaClient
        
        # Create client with a small cache size limit
        client = OllamaClient(cache_enabled=True, max_cache_entries=2)
        
        # Mock the API call
        with patch.object(client, '_call_ollama_api', return_value=sample_ollama_response["response"]):
            
            # Generate responses for different requests
            for i in range(3):
                modified_request = CompanionRequest(
                    request_id=f"test-{i}",
                    player_input=f"Request {i}",
                    request_type="translation"
                )
                # Add entries directly to the memory cache
                request_hash = client._hash_request(modified_request, client.default_model)
                client._memory_cache[request_hash] = {
                    "response": f"Response {i}",
                    "timestamp": time.time(),
                    "model": client.default_model
                }
            
            # Verify we have 3 entries in the cache
            assert len(client._memory_cache) == 3
            
            # Call prune directly
            client._prune_cache_if_needed()
            
            # Verify that entries were pruned
            assert len(client._memory_cache) <= 2

    def test_create_prompt(self, sample_request):
        """Test creating a prompt for Ollama."""
        from backend.ai.companion.tier2.ollama_client import OllamaClient
        
        client = OllamaClient()
        
        # Call the _create_prompt method
        prompt = client._create_prompt(sample_request)
        
        # Check that the prompt contains the necessary information
        assert "translation" in prompt
        assert "How do I say 'I want to go to Tokyo' in Japanese?" in prompt
        assert "Japanese" in prompt

    def test_hash_request(self, sample_request):
        """Test hashing a request for cache lookup."""
        from backend.ai.companion.tier2.ollama_client import OllamaClient
        
        client = OllamaClient()
        
        # Call the _hash_request method
        hash1 = client._hash_request(sample_request, "llama3")
        
        # The same request should produce the same hash
        hash2 = client._hash_request(sample_request, "llama3")
        assert hash1 == hash2
        
        # Different models should produce different hashes
        hash3 = client._hash_request(sample_request, "mistral")
        assert hash1 != hash3
        
        # Different requests should produce different hashes
        different_request = CompanionRequest(
            request_id="test-456",
            player_input="How do I say 'I want to eat sushi' in Japanese?",
            request_type="translation"
        )
        hash4 = client._hash_request(different_request, "llama3")
        assert hash1 != hash4 