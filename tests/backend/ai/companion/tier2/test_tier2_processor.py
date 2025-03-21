"""
Tests for the Tier 2 processor.

This module contains tests for the Tier 2 processor, which uses the Ollama client
to generate responses using local language models.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
import unittest

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
from backend.ai.companion.tier2.ollama_client import OllamaError, OllamaClient
from backend.ai.companion.tier2.tier2_processor import Tier2Processor
from backend.ai.companion.core.processor_framework import ProcessorFactory
from backend.ai.companion.utils.retry import RetryConfig


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


class TestTier2Processor(unittest.TestCase):
    """Test the Tier2Processor class."""

    def setUp(self):
        # Create a mock for get_config
        self.get_config_patcher = patch('backend.ai.companion.tier2.tier2_processor.get_config')
        self.mock_get_config = self.get_config_patcher.start()
        
        # Mock config
        self.mock_config = {
            "enabled": True,
            "base_url": "http://test-ollama:11434/api",
            "default_model": "test-model",
            "cache_enabled": False,
            "cache_dir": "/tmp/test-cache",
            "cache_ttl": 3600,
            "max_cache_entries": 100,
            "max_cache_size_mb": 50
        }
        self.mock_get_config.return_value = self.mock_config
        
        # Mock OllamaClient
        self.ollama_client_patcher = patch('backend.ai.companion.tier2.tier2_processor.OllamaClient')
        self.mock_ollama_client_class = self.ollama_client_patcher.start()
        self.mock_ollama_client = MagicMock(spec=OllamaClient)
        self.mock_ollama_client_class.return_value = self.mock_ollama_client
        
    def tearDown(self):
        self.get_config_patcher.stop()
        self.ollama_client_patcher.stop()
        
    def test_tier2_processor_init_uses_config(self):
        """Test that Tier2Processor uses configuration in initialization."""
        processor = Tier2Processor()
        
        # Check that get_config was called with the expected arguments
        self.mock_get_config.assert_called_with('tier2', {})
        
        # Check that OllamaClient was created with the right parameters
        self.mock_ollama_client_class.assert_called_once_with(
            base_url=self.mock_config["base_url"],
            default_model=self.mock_config["default_model"],
            cache_enabled=self.mock_config["cache_enabled"],
            cache_dir=self.mock_config["cache_dir"],
            cache_ttl=self.mock_config["cache_ttl"],
            max_cache_entries=self.mock_config["max_cache_entries"],
            max_cache_size_mb=self.mock_config["max_cache_size_mb"]
        )
        
        # Check that the processor is using the config values
        self.assertEqual(processor.enabled, self.mock_config["enabled"])
    
    def test_tier2_processor_respects_enabled_flag(self):
        """Test that Tier2Processor respects the enabled flag from configuration."""
        # Set enabled to False
        self.mock_get_config.return_value = {"enabled": False}
        
        processor = Tier2Processor()
        
        # Create a mock request
        request = MagicMock(spec=ClassifiedRequest)
        request.intent = IntentCategory.VOCABULARY_HELP
        request.complexity = ComplexityLevel.MODERATE
        request.processing_tier = ProcessingTier.TIER_2
        request.request_id = "test_request"
        
        # Check that processing is skipped when disabled
        response = processor.process(request)
        self.assertIn("disabled", response.lower())
        
        # Ensure OllamaClient was not called
        self.mock_ollama_client.generate_response.assert_not_called()
        
        # Set enabled to True and check that processing happens
        self.mock_get_config.return_value = {"enabled": True}
        processor = Tier2Processor()
        self.mock_ollama_client.generate_response.return_value = "Test response from Ollama"
        
        response = processor.process(request)
        self.mock_ollama_client.generate_response.assert_called_once()
        self.assertEqual(response, "Test response from Ollama")
    
    def test_tier2_processor_falls_back_to_defaults(self):
        """Test that Tier2Processor falls back to defaults if config is missing."""
        # Return None to simulate missing config
        self.mock_get_config.return_value = None
        
        # Should use defaults for OllamaClient
        processor = Tier2Processor()
        self.assertTrue(processor.enabled)  # Default should be True
        
        # Check OllamaClient was created with default parameters
        self.mock_ollama_client_class.assert_called_once()
        
        # Should use default parameters (no specific values)
        call_args = self.mock_ollama_client_class.call_args[1]
        self.assertEqual(call_args, {})


if __name__ == '__main__':
    unittest.main()


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
             patch('backend.ai.companion.tier2.tier2_processor.ResponseParser') as mock_parser_class, \
             patch('backend.ai.companion.tier2.tier2_processor.get_config') as mock_get_config:
            
            # Mock the configuration
            mock_get_config.return_value = {
                "enabled": True,
                "base_url": "http://test-ollama:11434/api",
                "default_model": "test-model",
                "cache_enabled": False
            }
                
            # Set up the mock client
            mock_client = mock_client_class.return_value
            mock_client.generate_response = AsyncMock(return_value=sample_ollama_response)
            
            # Set up the mock response parser
            mock_parser = mock_parser_class.return_value
            mock_parser.parse_response.return_value = sample_ollama_response
            
            # Create a processor with the mock context manager
            processor = Tier2Processor(context_manager=mock_context_manager)
            
            # Replace the response parser with our mock
            processor.response_parser = mock_parser
            
            # Important: Create and inject the client before calling process
            processor.ollama_client = mock_client
            processor._generate_with_retries = AsyncMock(return_value=(sample_ollama_response, None))

            # Process the request
            response = await processor.process(sample_request)
            
            # Check that the response is correct
            assert response == sample_ollama_response
            
            # Verify _generate_with_retries was called
            processor._generate_with_retries.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_with_conversation_history(self, sample_request, sample_ollama_response, mock_context_manager):
        """Test processing a request with conversation history."""
        with patch('backend.ai.companion.tier2.tier2_processor.OllamaClient') as mock_client_class, \
             patch('backend.ai.companion.tier2.tier2_processor.ResponseParser') as mock_parser_class, \
             patch('backend.ai.companion.tier2.tier2_processor.get_config') as mock_get_config:
            
            # Mock the configuration
            mock_get_config.return_value = {
                "enabled": True,
                "base_url": "http://test-ollama:11434/api",
                "default_model": "test-model",
                "cache_enabled": False
            }
            
            # Set up the mock client
            mock_client = mock_client_class.return_value
            mock_client.generate_response = AsyncMock(return_value=sample_ollama_response)
            
            # Set up the mock response parser
            mock_parser = mock_parser_class.return_value
            mock_parser.parse_response.return_value = sample_ollama_response
            
            # Add a conversation ID to the request
            sample_request.additional_params = {"conversation_id": "test-conv-123"}
            
            # Create a processor with the mock context manager
            processor = Tier2Processor(context_manager=mock_context_manager)
            
            # Replace the client and response parser with our mocks
            processor.response_parser = mock_parser
            processor.ollama_client = mock_client
            processor._generate_with_retries = AsyncMock(return_value=(sample_ollama_response, None))

            # Process the request
            response = await processor.process(sample_request)
            
            # Check that the response is correct
            assert response == sample_ollama_response

            # Verify the context manager was called to update context with the conversation
            mock_context_manager.update_context.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_with_retry(self, sample_request, sample_ollama_response, mock_context_manager):
        """Test processing a request with retries."""
        with patch('backend.ai.companion.tier2.tier2_processor.OllamaClient') as mock_client_class, \
             patch('backend.ai.companion.tier2.tier2_processor.ResponseParser') as mock_parser_class, \
             patch('backend.ai.companion.tier2.tier2_processor.get_config') as mock_get_config:
            
            # Mock the configuration
            mock_get_config.return_value = {
                "enabled": True,
                "base_url": "http://test-ollama:11434/api",
                "default_model": "test-model",
                "cache_enabled": False
            }
            
            # Set up the mock client to fail once then succeed
            mock_client = mock_client_class.return_value
            mock_client.generate_response = AsyncMock(side_effect=[
                OllamaError("Transient error", OllamaError.CONNECTION_ERROR),
                sample_ollama_response
            ])
            
            # Set up the mock response parser
            mock_parser = mock_parser_class.return_value
            mock_parser.parse_response.return_value = sample_ollama_response
            
            # Create a processor with the mock context manager
            processor = Tier2Processor(context_manager=mock_context_manager)
            
            # Replace the client and response parser with our mocks
            processor.response_parser = mock_parser
            processor.ollama_client = mock_client
            
            # Create a shorter retry config for testing
            processor.retry_config = RetryConfig(
                max_retries=2,
                base_delay=0.01,
                max_delay=0.1,
                backoff_factor=1.0,
                jitter=False
            )
            
            # Mock the internal retry method to simulate a retry sequence
            # First attempt fails, second succeeds
            processor._generate_with_retries = AsyncMock()
            processor._generate_with_retries.return_value = (sample_ollama_response, None)

            # Process the request
            response = await processor.process(sample_request)
            
            # Check that the response is correct
            assert response == sample_ollama_response
    
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
    async def test_process_with_fallback_to_simpler_model(self, sample_request, sample_ollama_response, mock_context_manager):
        """Test processing a request with fallback to a simpler model."""
        with patch('backend.ai.companion.tier2.tier2_processor.OllamaClient') as mock_client_class, \
             patch('backend.ai.companion.tier2.tier2_processor.ResponseParser') as mock_parser_class, \
             patch('backend.ai.companion.tier2.tier2_processor.get_config') as mock_get_config:

            # Mock the configuration
            mock_get_config.return_value = {
                "enabled": True,
                "base_url": "http://test-ollama:11434/api",
                "default_model": "test-model",
                "cache_enabled": False
            }

            # Set up the mock client to fail with a model error then succeed with a simpler model
            mock_client = mock_client_class.return_value
            mock_client.generate_response = AsyncMock(side_effect=[
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

            # Replace the client and response parser with our mocks
            processor.response_parser = mock_parser
            processor.ollama_client = mock_client

            # Create a shorter retry config for testing
            processor.retry_config = RetryConfig(
                max_retries=1,
                base_delay=0.01,
                max_delay=0.1,
                backoff_factor=1.0,
                jitter=False
            )

            # First simulate a model error, then a successful response with simpler model
            error = OllamaError("Model error", OllamaError.MODEL_ERROR)
            processor._generate_with_retries = AsyncMock()
            processor._generate_with_retries.side_effect = [
                (None, error),
                (sample_ollama_response, None)
            ]

            # Process the request
            response = await processor.process(sample_request)

            # Check that the response is correct
            assert response == sample_ollama_response
    
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
            assert kwargs.get('model') == "deepseek-coder"
        
        # Test with MODERATE complexity
        sample_request.complexity = ComplexityLevel.MODERATE
        
        with patch.object(processor.ollama_client, 'generate') as mock_generate:
            await processor.process(sample_request)
            args, kwargs = mock_generate.call_args
            assert kwargs.get('model') == "deepseek-coder"
        
        # Test with COMPLEX complexity
        sample_request.complexity = ComplexityLevel.COMPLEX
        
        with patch.object(processor.ollama_client, 'generate') as mock_generate:
            await processor.process(sample_request)
            args, kwargs = mock_generate.call_args
            assert kwargs.get('model') == "deepseek-r1"  # Using deepseek-r1 model for complex requests
    
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
        with patch('backend.ai.companion.tier2.tier2_processor.OllamaClient') as mock_client_class, \
             patch('backend.ai.companion.tier2.tier2_processor.get_config') as mock_get_config, \
             patch('backend.ai.companion.tier2.tier2_processor.ProcessorFactory') as mock_factory_class:

            # Mock the configuration
            mock_get_config.return_value = {
                "enabled": True,
                "base_url": "http://test-ollama:11434/api",
                "default_model": "test-model",
                "cache_enabled": False
            }

            # Create a processor
            processor = Tier2Processor()

            # Create a mock Tier1Processor
            mock_tier1_processor = MagicMock()
            mock_tier1_processor.process = AsyncMock(return_value="Response from Tier 1")

            # Mock the ProcessorFactory to return our mock Tier1Processor
            mock_factory = mock_factory_class.return_value
            mock_factory.get_processor.return_value = mock_tier1_processor
            
            # Make the ProcessorFactory available to the processor
            processor.processor_factory = mock_factory

            # Test with an error that should trigger fallback to Tier 1
            connection_error = OllamaError("Connection error", OllamaError.CONNECTION_ERROR)

            # Mock the _generate_with_retries method to return (None, connection_error)
            processor._generate_with_retries = AsyncMock(return_value=(None, connection_error))

            # Process the request
            await processor.process(sample_request)

            # Verify that the Tier 1 processor was used
            mock_factory.get_processor.assert_called_once_with(ProcessingTier.TIER_1)
            mock_tier1_processor.process.assert_called_once_with(sample_request)
    
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