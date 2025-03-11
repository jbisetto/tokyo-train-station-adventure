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
def mock_bedrock_client():
    """Create a mock Bedrock client for testing."""
    client = MagicMock(spec=BedrockClient)
    client.generate = AsyncMock(return_value="'Kippu' means 'ticket' in Japanese.")
    return client


class TestTier3Processor:
    """Tests for the Tier3Processor class."""
    
    def test_tier3_processor_creation(self):
        """Test that a Tier3Processor can be created."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient'):
            processor = Tier3Processor()
            
            assert processor is not None
            assert hasattr(processor, 'process')
            assert hasattr(processor, '_create_bedrock_client')
            assert hasattr(processor, '_generate_response')
            assert hasattr(processor, '_create_custom_prompt')
            assert hasattr(processor, '_parse_response')
            assert hasattr(processor, '_generate_fallback_response')
    
    def test_create_custom_prompt(self, sample_classified_request):
        """Test creating a custom prompt for the Bedrock API."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient'):
            processor = Tier3Processor()
            
            prompt = processor._create_custom_prompt(sample_classified_request)
            
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert "You are a helpful bilingual dog companion" in prompt
            assert sample_classified_request.player_input in prompt
            assert sample_classified_request.intent.value in prompt
            assert "word: kippu" in prompt.lower()
    
    def test_parse_response(self):
        """Test parsing a response from the Bedrock API."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient'):
            processor = Tier3Processor()
            
            # Test with a clean response
            clean_response = "This is a clean response."
            assert processor._parse_response(clean_response) == clean_response
            
            # Test with a response that has assistant tags
            tagged_response = "<assistant>This is a tagged response.</assistant>"
            assert processor._parse_response(tagged_response) == "This is a tagged response."
            
            # Test with a response that has whitespace
            whitespace_response = "  This response has whitespace.  "
            assert processor._parse_response(whitespace_response) == "This response has whitespace."
    
    def test_generate_fallback_response(self, sample_classified_request):
        """Test generating a fallback response when an error occurs."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient'):
            processor = Tier3Processor()
            
            # Test with a quota error
            quota_error = BedrockError("Quota exceeded", error_type=BedrockError.QUOTA_ERROR)
            fallback_response = processor._generate_fallback_response(sample_classified_request, quota_error)
            assert "limit for complex questions" in fallback_response
            
            # Test with a generic error
            generic_error = Exception("Generic error")
            fallback_response = processor._generate_fallback_response(sample_classified_request, generic_error)
            assert "trouble understanding" in fallback_response
    
    @pytest.mark.asyncio
    async def test_generate_response(self, sample_classified_request, mock_bedrock_client):
        """Test generating a response using the Bedrock client."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient', return_value=mock_bedrock_client):
            processor = Tier3Processor()
            
            # Create a companion request from the classified request
            companion_request = CompanionRequest(
                request_id=sample_classified_request.request_id,
                player_input=sample_classified_request.player_input,
                request_type=sample_classified_request.request_type,
                timestamp=sample_classified_request.timestamp
            )
            
            # Generate a response
            response = await processor._generate_response(companion_request, sample_classified_request)
            
            # Check that the response is correct
            assert response == "'Kippu' means 'ticket' in Japanese."
            
            # Check that the Bedrock client was called with the correct arguments
            mock_bedrock_client.generate.assert_called_once()
            args, kwargs = mock_bedrock_client.generate.call_args
            assert kwargs["request"] == companion_request
            assert "prompt" in kwargs
    
    def test_process(self, sample_classified_request, mock_bedrock_client):
        """Test processing a request using the Tier3Processor."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient', return_value=mock_bedrock_client):
            processor = Tier3Processor()
            
            # Process a request
            response = processor.process(sample_classified_request)
            
            # Check that the response is correct
            assert response == "'Kippu' means 'ticket' in Japanese."
            
            # Check that the Bedrock client was called
            mock_bedrock_client.generate.assert_called_once()
    
    def test_process_with_error(self, sample_classified_request):
        """Test processing a request when an error occurs."""
        # Create a mock Bedrock client that raises an error
        mock_client = MagicMock(spec=BedrockClient)
        mock_client.generate = AsyncMock(side_effect=BedrockError("Test error", error_type=BedrockError.QUOTA_ERROR))
        
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient', return_value=mock_client):
            processor = Tier3Processor()
            
            # Process a request
            response = processor.process(sample_classified_request)
            
            # Check that a fallback response was returned
            assert "limit for complex questions" in response
            
            # Check that the Bedrock client was called
            mock_client.generate.assert_called_once() 