"""
Tests for the Tier 2 processor.

This module contains tests for the Tier 2 processor, which uses the Ollama client
to generate responses using local language models.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from backend.ai.companion.core.models import (
    CompanionRequest,
    ClassifiedRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)


@pytest.fixture
def sample_request():
    """Create a sample request for testing."""
    request = CompanionRequest(
        request_id="test-123",
        player_input="How do I say 'I want to go to Tokyo' in Japanese?",
        request_type="translation"
    )
    
    return ClassifiedRequest.from_companion_request(
        request=request,
        intent=IntentCategory.TRANSLATION_CONFIRMATION,
        complexity=ComplexityLevel.MODERATE,
        processing_tier=ProcessingTier.TIER_2,
        confidence=0.85,
        extracted_entities={"destination": "Tokyo"}
    )


@pytest.fixture
def sample_ollama_response():
    """Create a sample response from Ollama."""
    return "「東京に行きたいです」(Tōkyō ni ikitai desu) is how you say 'I want to go to Tokyo' in Japanese."


class TestTier2Processor:
    """Tests for the Tier2Processor class."""
    
    def test_initialization(self):
        """Test that the Tier2Processor can be initialized."""
        from backend.ai.companion.tier2.tier2_processor import Tier2Processor
        
        processor = Tier2Processor()
        
        assert processor is not None
        assert hasattr(processor, 'process')
        assert hasattr(processor, 'ollama_client')
    
    @pytest.mark.asyncio
    async def test_process(self, sample_request, sample_ollama_response):
        """Test processing a request."""
        from backend.ai.companion.tier2.tier2_processor import Tier2Processor
        
        processor = Tier2Processor()
        
        # Mock the ollama_client.generate method
        with patch.object(processor.ollama_client, 'generate') as mock_generate:
            mock_generate.return_value = sample_ollama_response
            
            # Process the request
            response = await processor.process(sample_request)
            
            # Check that the response was generated
            assert response is not None
            assert "東京に行きたいです" in response
            assert "Tōkyō ni ikitai desu" in response
            
            # Check that the ollama_client.generate method was called
            mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_with_error(self, sample_request):
        """Test processing a request with an error."""
        from backend.ai.companion.tier2.tier2_processor import Tier2Processor
        from backend.ai.companion.tier2.ollama_client import OllamaError
        
        processor = Tier2Processor()
        
        # Mock the ollama_client.generate method to raise an exception
        with patch.object(processor.ollama_client, 'generate') as mock_generate:
            mock_generate.side_effect = OllamaError("Failed to generate response")
            
            # Process the request
            response = await processor.process(sample_request)
            
            # Check that a fallback response was generated
            assert response is not None
            assert "I'm sorry" in response
            assert "having trouble" in response
            
            # Check that the ollama_client.generate method was called
            mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_with_different_intent(self, sample_request):
        """Test processing a request with a different intent."""
        from backend.ai.companion.tier2.tier2_processor import Tier2Processor
        
        # Change the intent
        sample_request.intent = IntentCategory.VOCABULARY_HELP
        
        processor = Tier2Processor()
        
        # Mock the ollama_client.generate method
        with patch.object(processor.ollama_client, 'generate') as mock_generate:
            mock_generate.return_value = "The word 'kippu' means 'ticket' in Japanese."
            
            # Process the request
            response = await processor.process(sample_request)
            
            # Check that the response was generated
            assert response is not None
            assert "ticket" in response
            
            # Check that the ollama_client.generate method was called
            mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_select_model_based_on_complexity(self, sample_request):
        """Test selecting a model based on complexity."""
        from backend.ai.companion.tier2.tier2_processor import Tier2Processor
        
        processor = Tier2Processor()
        
        # Test with SIMPLE complexity
        sample_request.complexity = ComplexityLevel.SIMPLE
        
        with patch.object(processor.ollama_client, 'generate') as mock_generate:
            await processor.process(sample_request)
            args, kwargs = mock_generate.call_args
            assert kwargs.get('model') == "llama3"
        
        # Test with MODERATE complexity
        sample_request.complexity = ComplexityLevel.MODERATE
        
        with patch.object(processor.ollama_client, 'generate') as mock_generate:
            await processor.process(sample_request)
            args, kwargs = mock_generate.call_args
            assert kwargs.get('model') == "llama3"
        
        # Test with COMPLEX complexity
        sample_request.complexity = ComplexityLevel.COMPLEX
        
        with patch.object(processor.ollama_client, 'generate') as mock_generate:
            await processor.process(sample_request)
            args, kwargs = mock_generate.call_args
            assert kwargs.get('model') == "llama3:16b"  # Assuming a larger model for complex requests 