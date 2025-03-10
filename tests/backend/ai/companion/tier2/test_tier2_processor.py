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
from backend.ai.companion.tier2.ollama_client import OllamaError
from backend.ai.companion.tier2.tier2_processor import Tier2Processor


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
        processor = Tier2Processor()
        
        assert processor is not None
        assert hasattr(processor, 'process')
        assert hasattr(processor, 'ollama_client')
    
    @pytest.mark.asyncio
    async def test_process(self, sample_request, sample_ollama_response):
        """Test processing a request."""
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
        processor = Tier2Processor()
        
        # Mock the Tier 1 processor to return a specific response
        mock_tier1_processor = MagicMock()
        mock_tier1_processor.process.return_value = "Tier 1 fallback response"
        processor._get_tier1_processor = MagicMock(return_value=mock_tier1_processor)
        
        # Mock the ollama_client.generate method to raise an exception
        with patch.object(processor.ollama_client, 'generate') as mock_generate:
            mock_generate.side_effect = OllamaError("Failed to generate response")
            
            # Process the request
            response = await processor.process(sample_request)
            
            # Check that the Tier 1 processor was used
            processor._get_tier1_processor.assert_called_once()
            mock_tier1_processor.process.assert_called_once()
            
            # Check that the fallback response was returned
            assert response == "Tier 1 fallback response"
    
    @pytest.mark.asyncio
    async def test_process_with_specific_error_types(self, sample_request):
        """Test processing a request with different types of errors."""
        processor = Tier2Processor()
        
        # Mock the Tier 1 processor to return a specific response
        mock_tier1_processor = MagicMock()
        mock_tier1_processor.process.return_value = "Tier 1 fallback response"
        processor._get_tier1_processor = MagicMock(return_value=mock_tier1_processor)
        
        # Test with connection error
        with patch.object(processor.ollama_client, 'generate') as mock_generate:
            mock_generate.side_effect = OllamaError("Failed to connect to Ollama server", OllamaError.CONNECTION_ERROR)
            
            response = await processor.process(sample_request)
            
            # Check that the Tier 1 processor was used
            processor._get_tier1_processor.assert_called_once()
            mock_tier1_processor.process.assert_called_once()
            
            # Check that the fallback response was returned
            assert response == "Tier 1 fallback response"
            
            # Reset the mocks for the next test
            processor._get_tier1_processor.reset_mock()
            mock_tier1_processor.process.reset_mock()
        
        # Test with content error (should not fall back to Tier 1)
        with patch.object(processor.ollama_client, 'generate') as mock_generate:
            mock_generate.side_effect = OllamaError("Content policy violation", OllamaError.CONTENT_ERROR)
            
            response = await processor.process(sample_request)
            
            # Check that the Tier 1 processor was not used
            processor._get_tier1_processor.assert_not_called()
            mock_tier1_processor.process.assert_not_called()
            
            # Check that the content error fallback response was returned
            assert "content restrictions" in response
    
    @pytest.mark.asyncio
    async def test_process_with_retry(self, sample_request, sample_ollama_response):
        """Test processing a request with retry on transient errors."""
        processor = Tier2Processor()
        
        # Mock the ollama_client.generate method to fail once then succeed
        with patch.object(processor.ollama_client, 'generate') as mock_generate:
            # First call raises a transient error, second call succeeds
            mock_generate.side_effect = [
                OllamaError("Request timed out"),
                sample_ollama_response
            ]
            
            # Process the request
            response = await processor.process(sample_request)
            
            # Check that the successful response was returned after retry
            assert response is not None
            assert "東京に行きたいです" in response
            assert "Tōkyō ni ikitai desu" in response
            
            # Check that the ollama_client.generate method was called twice
            assert mock_generate.call_count == 2
    
    @pytest.mark.asyncio
    async def test_process_with_fallback_to_simpler_model(self, sample_request, sample_ollama_response):
        """Test falling back to a simpler model when a complex model fails."""
        # Set request to complex to trigger larger model selection
        sample_request.complexity = ComplexityLevel.COMPLEX
        
        processor = Tier2Processor()
        
        # Mock the ollama_client.generate method to fail with the complex model but succeed with the simple one
        with patch.object(processor.ollama_client, 'generate') as mock_generate:
            # First call with complex model fails, second call with simple model succeeds
            mock_generate.side_effect = [
                OllamaError("Model too large for available memory"),
                sample_ollama_response
            ]
            
            # Process the request
            response = await processor.process(sample_request)
            
            # Check that the successful response was returned after fallback
            assert response is not None
            assert "東京に行きたいです" in response
            assert "Tōkyō ni ikitai desu" in response
            
            # Check that the ollama_client.generate method was called twice
            assert mock_generate.call_count == 2
            
            # Check that the second call used the simpler model
            args1, kwargs1 = mock_generate.call_args_list[0]
            args2, kwargs2 = mock_generate.call_args_list[1]
            assert kwargs1.get('model') == "llama3:16b"  # First call with complex model
            assert kwargs2.get('model') == "llama3"      # Second call with simple model
    
    @pytest.mark.asyncio
    async def test_process_with_different_intent(self, sample_request):
        """Test processing a request with a different intent."""
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
    
    @pytest.mark.asyncio
    async def test_should_fallback_to_tier1(self, sample_request):
        """Test the _should_fallback_to_tier1 method."""
        processor = Tier2Processor()
        
        # Test with connection error
        connection_error = OllamaError("Connection error", OllamaError.CONNECTION_ERROR)
        assert processor._should_fallback_to_tier1(connection_error) is True
        
        # Test with timeout error
        timeout_error = OllamaError("Timeout error", OllamaError.TIMEOUT_ERROR)
        assert processor._should_fallback_to_tier1(timeout_error) is True
        
        # Test with memory error
        memory_error = OllamaError("Memory error", OllamaError.MEMORY_ERROR)
        assert processor._should_fallback_to_tier1(memory_error) is True
        
        # Test with model error
        model_error = OllamaError("Model error", OllamaError.MODEL_ERROR)
        assert processor._should_fallback_to_tier1(model_error) is True
        
        # Test with content error
        content_error = OllamaError("Content error", OllamaError.CONTENT_ERROR)
        assert processor._should_fallback_to_tier1(content_error) is False
        
        # Test with unknown error
        unknown_error = Exception("Unknown error")
        assert processor._should_fallback_to_tier1(unknown_error) is True
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_to_tier1(self, sample_request):
        """Test the graceful degradation to Tier 1."""
        processor = Tier2Processor()
        
        # Create a mock Tier1Processor
        mock_tier1_processor = MagicMock()
        mock_tier1_processor.process.return_value = "Response from Tier 1"
        
        # Mock the _get_tier1_processor method to return our mock
        processor._get_tier1_processor = MagicMock(return_value=mock_tier1_processor)
        
        # Test with an error that should trigger fallback to Tier 1
        connection_error = OllamaError("Connection error", OllamaError.CONNECTION_ERROR)
        response = processor._generate_fallback_response(sample_request, connection_error)
        
        # Verify that the Tier 1 processor was used
        processor._get_tier1_processor.assert_called_once()
        mock_tier1_processor.process.assert_called_once()
        assert response == "Response from Tier 1"
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_to_tier1_with_tier1_error(self, sample_request):
        """Test the graceful degradation to Tier 1 when Tier 1 also fails."""
        processor = Tier2Processor()
        
        # Create a mock Tier1Processor that raises an exception
        mock_tier1_processor = MagicMock()
        mock_tier1_processor.process.side_effect = Exception("Tier 1 error")
        
        # Mock the _get_tier1_processor method to return our mock
        processor._get_tier1_processor = MagicMock(return_value=mock_tier1_processor)
        
        # Test with an error that should trigger fallback to Tier 1
        connection_error = OllamaError("Connection error", OllamaError.CONNECTION_ERROR)
        response = processor._generate_fallback_response(sample_request, connection_error)
        
        # Verify that the Tier 1 processor was used
        processor._get_tier1_processor.assert_called_once()
        mock_tier1_processor.process.assert_called_once()
        
        # Verify that we got a fallback response since Tier 1 failed
        assert "I'm sorry" in response
    
    @pytest.mark.asyncio
    async def test_no_fallback_to_tier1_for_content_error(self, sample_request):
        """Test that we don't fall back to Tier 1 for content errors."""
        processor = Tier2Processor()
        
        # Create a mock Tier1Processor
        mock_tier1_processor = MagicMock()
        
        # Mock the _get_tier1_processor method to return our mock
        processor._get_tier1_processor = MagicMock(return_value=mock_tier1_processor)
        
        # Test with a content error that should not trigger fallback to Tier 1
        content_error = OllamaError("Content error", OllamaError.CONTENT_ERROR)
        response = processor._generate_fallback_response(sample_request, content_error)
        
        # Verify that the Tier 1 processor was not used
        processor._get_tier1_processor.assert_not_called()
        mock_tier1_processor.process.assert_not_called()
        
        # Verify that we got the content error fallback response
        assert "content restrictions" in response 