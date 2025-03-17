"""
Tests for the Tier 2 processor.

This module contains tests for the Tier 2 processor, which uses the Ollama client
to generate responses using local language models.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from backend.ai.companion.core.models import (
    CompanionRequest,
    ClassifiedRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from backend.ai.companion.core.prompt_manager import PromptManager
from backend.ai.companion.core.conversation_manager import ConversationManager
from backend.ai.companion.core.context_manager import ContextManager
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


@pytest.fixture
def mock_context_manager():
    """Create a mock context manager for testing."""
    context_manager = MagicMock(spec=ContextManager)
    context_manager.get_or_create_context.return_value = {
        "conversation_id": "test-conv-123",
        "entries": []
    }
    context_manager.update_context.return_value = {
        "conversation_id": "test-conv-123",
        "entries": [
            {
                "request": "How do I say 'I want to go to Tokyo' in Japanese?",
                "response": "「東京に行きたいです」(Tōkyō ni ikitai desu) is how you say 'I want to go to Tokyo' in Japanese."
            }
        ]
    }
    return context_manager


class TestTier2Processor:
    """Tests for the Tier2Processor class."""
    
    def test_initialization(self):
        """Test that a Tier2Processor can be initialized."""
        with patch('backend.ai.companion.tier2.tier2_processor.OllamaClient') as mock_client:
            processor = Tier2Processor()
            
            assert processor is not None
            assert hasattr(processor, 'process')
            assert hasattr(processor, 'prompt_manager')
            assert hasattr(processor, 'conversation_manager')
            assert hasattr(processor, 'context_manager')
    
    @pytest.mark.asyncio
    async def test_process(self, sample_request, sample_ollama_response, mock_context_manager):
        """Test processing a request."""
        with patch('backend.ai.companion.tier2.tier2_processor.OllamaClient') as mock_client_class, \
             patch('backend.ai.companion.tier2.tier2_processor.ResponseParser') as mock_parser_class:
            # Set up the mock client
            mock_client = mock_client_class.return_value
            mock_client.generate = AsyncMock(return_value=sample_ollama_response)
            
            # Set up the mock response parser
            mock_parser = mock_parser_class.return_value
            mock_parser.parse_response.return_value = sample_ollama_response
            
            # Create a processor with the mock context manager
            processor = Tier2Processor(context_manager=mock_context_manager)
            
            # Replace the response parser with our mock
            processor.response_parser = mock_parser
            
            # Process the request
            response = await processor.process(sample_request)
            
            # Check that the response is correct
            assert response == sample_ollama_response
            
            # Check that the client was called with the correct prompt
            mock_client.generate.assert_called_once()
            
            # Check that the context manager was used to update context
            # Note: get_or_create_context is not called in the process method
            mock_context_manager.update_context.assert_not_called()  # No conversation_id in additional_params
    
    @pytest.mark.asyncio
    async def test_process_with_error(self, sample_request, mock_context_manager):
        """Test processing a request when the client raises an error."""
        with patch('backend.ai.companion.tier2.tier2_processor.ResponseParser') as mock_parser_class:
            # Set up the mock response parser
            mock_parser = mock_parser_class.return_value
            fallback_response = "I'm sorry, I couldn't provide a translation right now. Could you try asking in a different way?"
            mock_parser._create_fallback_response.return_value = fallback_response
            
            # Create a processor with the mock context manager
            processor = Tier2Processor(context_manager=mock_context_manager)
            
            # Replace the response parser with our mock
            processor.response_parser = mock_parser
            
            # Mock the _generate_with_retries method to simulate an error
            error = OllamaError("Test error", OllamaError.CONNECTION_ERROR)
            processor._generate_with_retries = AsyncMock(return_value=(None, error))
            
            # Mock the _get_tier1_processor method to avoid the actual import
            processor._get_tier1_processor = MagicMock(side_effect=ImportError("No module named 'backend.ai.companion.tier1.tier1_processor'"))
            
            # Process the request
            response = await processor.process(sample_request)
            
            # Check that we got a fallback response
            assert response == fallback_response
            assert "sorry" in response.lower()
            
            # Check that _generate_with_retries was called
            processor._generate_with_retries.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_with_conversation_history(self, sample_request, sample_ollama_response, mock_context_manager):
        """Test processing a request with conversation history."""
        with patch('backend.ai.companion.tier2.tier2_processor.OllamaClient') as mock_client_class, \
             patch('backend.ai.companion.tier2.tier2_processor.ResponseParser') as mock_parser_class:
            # Set up the mock client
            mock_client = mock_client_class.return_value
            mock_client.generate = AsyncMock(return_value=sample_ollama_response)
            
            # Set up the mock response parser
            mock_parser = mock_parser_class.return_value
            mock_parser.parse_response.return_value = sample_ollama_response
            
            # Add a conversation ID to the request
            sample_request.additional_params = {"conversation_id": "test-conv-123"}
            
            # Create a processor with the mock context manager
            processor = Tier2Processor(context_manager=mock_context_manager)
            
            # Replace the response parser with our mock
            processor.response_parser = mock_parser
            
            # Process the request
            response = await processor.process(sample_request)
            
            # Check that the response is correct
            assert response == sample_ollama_response
            
            # Check that the context manager was used to update context
            # Note: get_or_create_context is not called in the process method
            mock_context_manager.update_context.assert_called_once_with("test-conv-123", sample_request, sample_ollama_response)
    
    @pytest.mark.asyncio
    async def test_process_with_retry(self, sample_request, sample_ollama_response, mock_context_manager):
        """Test processing a request with retries."""
        with patch('backend.ai.companion.tier2.tier2_processor.OllamaClient') as mock_client_class, \
             patch('backend.ai.companion.tier2.tier2_processor.ResponseParser') as mock_parser_class:
            # Set up the mock client to fail once then succeed
            mock_client = mock_client_class.return_value
            mock_client.generate = AsyncMock(side_effect=[
                OllamaError("Transient error", OllamaError.CONNECTION_ERROR),
                sample_ollama_response
            ])
            
            # Set up the mock response parser
            mock_parser = mock_parser_class.return_value
            mock_parser.parse_response.return_value = sample_ollama_response
            
            # Create a processor with the mock context manager
            processor = Tier2Processor(context_manager=mock_context_manager)
            
            # Replace the response parser with our mock
            processor.response_parser = mock_parser
            
            # Process the request
            response = await processor.process(sample_request)
            
            # Check that the response is correct
            assert response == sample_ollama_response
            
            # Check that the client was called twice
            assert mock_client.generate.call_count == 2
    
    @pytest.mark.asyncio
    async def test_process_with_fallback_to_simpler_model(self, sample_request, sample_ollama_response, mock_context_manager):
        """Test processing a request with fallback to a simpler model."""
        with patch('backend.ai.companion.tier2.tier2_processor.OllamaClient') as mock_client_class, \
             patch('backend.ai.companion.tier2.tier2_processor.ResponseParser') as mock_parser_class:
            # Set up the mock client to fail with a model error then succeed with a simpler model
            mock_client = mock_client_class.return_value
            mock_client.generate = AsyncMock(side_effect=[
                OllamaError("Model error", OllamaError.MODEL_ERROR),
                sample_ollama_response
            ])
            
            # Set up the mock response parser
            mock_parser = mock_parser_class.return_value
            mock_parser.parse_response.return_value = sample_ollama_response
            
            # Set the request complexity to COMPLEX to trigger model selection
            sample_request.complexity = ComplexityLevel.COMPLEX
            
            # Create a processor with the mock context manager
            processor = Tier2Processor(context_manager=mock_context_manager)
            
            # Replace the response parser with our mock
            processor.response_parser = mock_parser
            
            # Process the request
            response = await processor.process(sample_request)
            
            # Check that the response is correct
            assert response == sample_ollama_response
            
            # Check that the client was called twice
            assert mock_client.generate.call_count == 2
    
    @pytest.mark.asyncio
    async def test_process_with_different_intent(self, sample_request):
        """Test processing a request with a different intent."""
        # Change the intent
        sample_request.intent = IntentCategory.VOCABULARY_HELP
        
        # Create a processor
        processor = Tier2Processor()
        
        # Mock the _generate_with_retries method to return a successful response
        response_text = "The word 'kippu' means 'ticket' in Japanese."
        processor._generate_with_retries = AsyncMock(return_value=(response_text, None))
        
        # Process the request
        response = await processor.process(sample_request)
        
        # Check that the response is correct
        assert response == response_text
        
        # Check that _generate_with_retries was called
        processor._generate_with_retries.assert_called_once()
    
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
            assert kwargs.get('model') == "llama3:8b"  # Using 8b model for complex requests
    
    @pytest.mark.asyncio
    async def test_should_fallback_to_tier1(self, sample_request):
        """Test the _should_fallback_to_tier1 method."""
        processor = Tier2Processor()
        
        # Test with connection error
        connection_error = OllamaError("Connection error", OllamaError.CONNECTION_ERROR)
        assert processor._should_fallback_to_tier1(connection_error) is True
        
        # Test with timeout error
        timeout_error = OllamaError("Timeout error", OllamaError.TIMEOUT_ERROR)
        assert processor._should_fallback_to_tier1(timeout_error) is False
        
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
        assert processor._should_fallback_to_tier1(unknown_error) is False
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_to_tier1(self, sample_request):
        """Test the graceful degradation to Tier 1."""
        processor = Tier2Processor()
        
        # Create a mock Tier1Processor
        mock_tier1_processor = MagicMock()
        mock_tier1_processor.process.return_value = "Response from Tier 1"
        
        # Mock the _get_tier1_processor method to return our mock
        processor._get_tier1_processor = MagicMock(return_value=mock_tier1_processor)
        
        # Mock the response parser
        processor.response_parser = MagicMock()
        processor.response_parser._create_fallback_response.return_value = "Fallback response"
        
        # Test with an error that should trigger fallback to Tier 1
        connection_error = OllamaError("Connection error", OllamaError.CONNECTION_ERROR)
        
        # We need to test the process method, not _generate_fallback_response
        # Mock the _generate_with_retries method to return (None, connection_error)
        processor._generate_with_retries = AsyncMock(return_value=(None, connection_error))
        
        # Process the request
        response = await processor.process(sample_request)
        
        # Verify that the Tier 1 processor was used
        processor._get_tier1_processor.assert_called_once()
        mock_tier1_processor.process.assert_called_once_with(sample_request)
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
        
        # Mock the response parser
        processor.response_parser = MagicMock()
        fallback_response = "I'm sorry, I couldn't provide a translation right now. Could you try asking in a different way?"
        processor.response_parser._create_fallback_response.return_value = fallback_response
        
        # Test with an error that should trigger fallback to Tier 1
        connection_error = OllamaError("Connection error", OllamaError.CONNECTION_ERROR)
        
        # We need to test the process method, not _generate_fallback_response
        # Mock the _generate_with_retries method to return (None, connection_error)
        processor._generate_with_retries = AsyncMock(return_value=(None, connection_error))
        
        # Process the request
        response = await processor.process(sample_request)
        
        # Verify that the Tier 1 processor was used
        processor._get_tier1_processor.assert_called_once()
        mock_tier1_processor.process.assert_called_once_with(sample_request)
        
        # Verify that we got a fallback response since Tier 1 failed
        assert response == fallback_response
    
    @pytest.mark.asyncio
    async def test_no_fallback_to_tier1_for_content_error(self, sample_request):
        """Test that we don't fall back to Tier 1 for content errors."""
        processor = Tier2Processor()
        
        # Create a mock Tier1Processor
        mock_tier1_processor = MagicMock()
        
        # Mock the _get_tier1_processor method to return our mock
        processor._get_tier1_processor = MagicMock(return_value=mock_tier1_processor)
        
        # Mock the response parser
        processor.response_parser = MagicMock()
        fallback_response = "I'm sorry, I couldn't provide a translation due to content restrictions. Could you try asking in a different way?"
        processor.response_parser._create_fallback_response.return_value = fallback_response
        
        # Test with a content error that should not trigger fallback to Tier 1
        content_error = OllamaError("Content error", OllamaError.CONTENT_ERROR)
        
        # We need to test the process method, not _generate_fallback_response
        # Mock the _generate_with_retries method to return (None, content_error)
        processor._generate_with_retries = AsyncMock(return_value=(None, content_error))
        
        # Process the request
        response = await processor.process(sample_request)
        
        # Verify that the Tier 1 processor was not used
        processor._get_tier1_processor.assert_not_called()
        mock_tier1_processor.process.assert_not_called()
        
        # Verify that we got the fallback response
        assert response == fallback_response 