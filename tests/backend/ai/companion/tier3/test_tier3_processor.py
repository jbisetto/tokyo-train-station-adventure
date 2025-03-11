"""
Tests for the Tier 3 processor.
"""

import pytest
import asyncio
import uuid
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from backend.ai.companion.core.models import (
    ClassifiedRequest,
    CompanionRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from backend.ai.companion.tier3.tier3_processor import Tier3Processor
from backend.ai.companion.tier3.bedrock_client import BedrockClient, BedrockError
from backend.ai.companion.tier3.specialized_handlers import (
    SpecializedHandler,
    SpecializedHandlerRegistry,
    DefaultHandler,
    GrammarExplanationHandler,
    TranslationHandler
)


@pytest.fixture
def sample_classified_request():
    """Create a sample classified request for testing."""
    return ClassifiedRequest(
        request_id=str(uuid.uuid4()),
        player_input="What does 'kippu' mean?",
        request_type="vocabulary",
        timestamp=datetime.now(),
        intent=IntentCategory.VOCABULARY_HELP,
        complexity=ComplexityLevel.COMPLEX,
        processing_tier=ProcessingTier.TIER_3,
        confidence=0.9,
        extracted_entities={"word": "kippu"}
    )


@pytest.fixture
def sample_grammar_request():
    """Create a sample grammar explanation request for testing."""
    return ClassifiedRequest(
        request_id=str(uuid.uuid4()),
        player_input="Can you explain the difference between は and が particles in Japanese?",
        request_type="grammar",
        timestamp=datetime.now(),
        intent=IntentCategory.GRAMMAR_EXPLANATION,
        complexity=ComplexityLevel.COMPLEX,
        processing_tier=ProcessingTier.TIER_3,
        confidence=0.9,
        extracted_entities={"grammar_point": "は vs が"}
    )


@pytest.fixture
def mock_bedrock_client():
    """Create a mock Bedrock client for testing."""
    client = MagicMock(spec=BedrockClient)
    client.generate = AsyncMock(return_value="'Kippu' means 'ticket' in Japanese.")
    return client


@pytest.fixture
def mock_specialized_handler():
    """Create a mock specialized handler for testing."""
    handler = MagicMock(spec=SpecializedHandler)
    handler.can_handle = MagicMock(return_value=True)
    handler.create_prompt = MagicMock(return_value="This is a specialized prompt.")
    handler.process_response = MagicMock(return_value="This is a processed response.")
    handler.handle_request = AsyncMock(return_value="This is a response from the specialized handler.")
    handler.bedrock_client = None
    return handler


@pytest.fixture
def mock_handler_registry(mock_specialized_handler):
    """Create a mock handler registry for testing."""
    registry = MagicMock(spec=SpecializedHandlerRegistry)
    registry.get_handler = MagicMock(return_value=mock_specialized_handler)
    return registry


class TestTier3Processor:
    """Tests for the Tier3Processor class."""
    
    def test_tier3_processor_creation(self):
        """Test that a Tier3Processor can be created."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient'), \
             patch('backend.ai.companion.tier3.tier3_processor.SpecializedHandlerRegistry'):
            processor = Tier3Processor()
            
            assert processor is not None
            assert hasattr(processor, 'process')
            assert hasattr(processor, '_create_bedrock_client')
            assert hasattr(processor, '_initialize_handler_registry')
            assert hasattr(processor, '_get_handler_for_request')
            assert hasattr(processor, '_generate_response')
            assert hasattr(processor, '_create_custom_prompt')
            assert hasattr(processor, '_parse_response')
            assert hasattr(processor, '_generate_fallback_response')
    
    def test_initialize_handler_registry(self):
        """Test initializing the specialized handler registry."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient'), \
             patch('backend.ai.companion.tier3.tier3_processor.SpecializedHandlerRegistry') as mock_registry_class:
            mock_registry = MagicMock()
            mock_registry_class.return_value = mock_registry
            
            processor = Tier3Processor()
            
            mock_registry_class.assert_called_once()
            mock_registry.initialize_default_handlers.assert_called_once()
            assert processor.handler_registry == mock_registry
    
    def test_get_handler_for_request(self, sample_classified_request, mock_handler_registry, mock_specialized_handler):
        """Test getting a specialized handler for a request."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient'), \
             patch('backend.ai.companion.tier3.tier3_processor.SpecializedHandlerRegistry', return_value=mock_handler_registry):
            processor = Tier3Processor()
            
            handler = processor._get_handler_for_request(sample_classified_request)
            
            mock_handler_registry.get_handler.assert_called_once_with(sample_classified_request.intent)
            assert handler == mock_specialized_handler
    
    def test_create_custom_prompt(self, sample_classified_request):
        """Test creating a custom prompt for the Bedrock API."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient'), \
             patch('backend.ai.companion.tier3.tier3_processor.SpecializedHandlerRegistry'):
            processor = Tier3Processor()
            
            prompt = processor._create_custom_prompt(sample_classified_request)
            
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert "Intent: vocabulary_help" in prompt
            assert "word: kippu" in prompt
    
    def test_parse_response(self):
        """Test parsing a response from the Bedrock API."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient'), \
             patch('backend.ai.companion.tier3.tier3_processor.SpecializedHandlerRegistry'):
            processor = Tier3Processor()
            
            # Test with a clean response
            clean_response = "This is a clean response."
            parsed_clean = processor._parse_response(clean_response)
            assert parsed_clean == "This is a clean response."
            
            # Test with a response that includes assistant tags
            tagged_response = "<assistant>This is a tagged response.</assistant>"
            parsed_tagged = processor._parse_response(tagged_response)
            assert parsed_tagged == "This is a tagged response."
            
            # Test with a response that has extra whitespace
            whitespace_response = "  This has extra whitespace.  "
            parsed_whitespace = processor._parse_response(whitespace_response)
            assert parsed_whitespace == "This has extra whitespace."
    
    def test_generate_fallback_response(self, sample_classified_request):
        """Test generating a fallback response when an error occurs."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient'), \
             patch('backend.ai.companion.tier3.tier3_processor.SpecializedHandlerRegistry'):
            processor = Tier3Processor()
            
            # Test with a generic error
            generic_error = Exception("Something went wrong")
            fallback_generic = processor._generate_fallback_response(sample_classified_request, generic_error)
            assert "I'm having trouble" in fallback_generic
            
            # Test with a Bedrock error
            bedrock_error = BedrockError("API error", BedrockError.CONNECTION_ERROR)
            fallback_bedrock = processor._generate_fallback_response(sample_classified_request, bedrock_error)
            assert "I'm having trouble" in fallback_bedrock
    
    @pytest.mark.asyncio
    async def test_generate_response_with_specialized_handler(self, sample_grammar_request, mock_bedrock_client, mock_specialized_handler):
        """Test generating a response using a specialized handler."""
        with patch('backend.ai.companion.tier3.tier3_processor.SpecializedHandlerRegistry') as mock_registry_class:
            # Set up the mock registry to return our mock handler
            mock_registry = MagicMock()
            mock_registry.get_handler.return_value = mock_specialized_handler
            mock_registry_class.return_value = mock_registry
            
            # Create a companion request
            companion_request = CompanionRequest(
                request_id=sample_grammar_request.request_id,
                player_input=sample_grammar_request.player_input,
                request_type=sample_grammar_request.request_type,
                timestamp=sample_grammar_request.timestamp
            )
            
            # Create the processor with our mock client
            processor = Tier3Processor()
            processor.client = mock_bedrock_client
            
            # Generate a response
            response = await processor._generate_response(companion_request, sample_grammar_request)
            
            # Check that the handler was used
            mock_registry.get_handler.assert_called_once_with(sample_grammar_request.intent)
            mock_specialized_handler.handle_request.assert_called_once_with(sample_grammar_request)
            assert response == "This is a response from the specialized handler."
    
    @pytest.mark.asyncio
    async def test_generate_response_with_handler_error(self, sample_grammar_request, mock_bedrock_client):
        """Test generating a response when the specialized handler fails."""
        with patch('backend.ai.companion.tier3.tier3_processor.SpecializedHandlerRegistry') as mock_registry_class:
            # Set up a handler that raises an exception
            error_handler = MagicMock(spec=SpecializedHandler)
            error_handler.handle_request = AsyncMock(side_effect=Exception("Handler error"))
            error_handler.bedrock_client = None
            
            # Set up the mock registry to return our error handler
            mock_registry = MagicMock()
            mock_registry.get_handler.return_value = error_handler
            mock_registry_class.return_value = mock_registry
            
            # Create a companion request
            companion_request = CompanionRequest(
                request_id=sample_grammar_request.request_id,
                player_input=sample_grammar_request.player_input,
                request_type=sample_grammar_request.request_type,
                timestamp=sample_grammar_request.timestamp
            )
            
            # Create the processor with our mock client
            processor = Tier3Processor()
            processor.client = mock_bedrock_client
            
            # Generate a response
            response = await processor._generate_response(companion_request, sample_grammar_request)
            
            # Check that the fallback method was used
            mock_registry.get_handler.assert_called_once_with(sample_grammar_request.intent)
            error_handler.handle_request.assert_called_once_with(sample_grammar_request)
            mock_bedrock_client.generate.assert_called_once()
            assert response == "'Kippu' means 'ticket' in Japanese."
    
    def test_process(self, sample_classified_request, mock_bedrock_client, mock_specialized_handler):
        """Test processing a request."""
        with patch('backend.ai.companion.tier3.tier3_processor.SpecializedHandlerRegistry') as mock_registry_class:
            # Set up the mock registry to return our mock handler
            mock_registry = MagicMock()
            mock_registry.get_handler.return_value = mock_specialized_handler
            mock_registry_class.return_value = mock_registry
            
            # Create the processor with our mock client
            processor = Tier3Processor()
            processor.client = mock_bedrock_client
            
            # Process a request
            response = processor.process(sample_classified_request)
            
            # Check that the response is correct
            assert response == "This is a response from the specialized handler."
    
    def test_process_with_error(self, sample_classified_request):
        """Test processing a request when an error occurs."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient') as mock_client_class, \
             patch('backend.ai.companion.tier3.tier3_processor.SpecializedHandlerRegistry'):
            # Set up the mock client to raise an exception
            mock_client = MagicMock()
            mock_client.generate = AsyncMock(side_effect=BedrockError("API error", BedrockError.CONNECTION_ERROR))
            mock_client_class.return_value = mock_client
            
            # Create the processor
            processor = Tier3Processor()
            
            # Process a request
            response = processor.process(sample_classified_request)
            
            # Check that a fallback response was returned
            assert "I'm having trouble" in response
    
    def test_integration_with_grammar_handler(self, sample_grammar_request, mock_bedrock_client):
        """Test integration with the GrammarExplanationHandler."""
        # Create a real GrammarExplanationHandler with a mock client
        grammar_handler = GrammarExplanationHandler(bedrock_client=mock_bedrock_client)
        
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient', return_value=mock_bedrock_client), \
             patch('backend.ai.companion.tier3.tier3_processor.SpecializedHandlerRegistry') as mock_registry_class:
            # Set up the mock registry to return our real handler
            mock_registry = MagicMock()
            mock_registry.get_handler.return_value = grammar_handler
            mock_registry_class.return_value = mock_registry
            
            # Create the processor
            processor = Tier3Processor()
            
            # Process a request
            response = processor.process(sample_grammar_request)
            
            # Check that the response contains the expected content
            assert "'Kippu' means 'ticket' in Japanese." in response
            assert "がんばって (Ganbatte)!" in response
            
            # Check that the handler was used correctly
            mock_registry.get_handler.assert_called_once_with(sample_grammar_request.intent)
            mock_bedrock_client.generate.assert_called_once() 