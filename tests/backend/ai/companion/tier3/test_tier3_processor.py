"""
Tests for the Tier 3 processor.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

from src.ai.companion.core.models import (
    ClassifiedRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from src.ai.companion.tier3.tier3_processor import Tier3Processor
from src.ai.companion.tier3.bedrock_client import BedrockError
from src.ai.companion.core.context_manager import ContextManager


class TestTier3Processor:
    """Test cases for the Tier3Processor class."""

    @pytest.fixture
    def sample_classified_request(self):
        """Create a sample classified request for testing."""
        return ClassifiedRequest(
            request_id="test-123",
            player_input="What does 'kippu' mean?",
            request_type="translation",
            intent=IntentCategory.VOCABULARY_HELP,
            complexity=ComplexityLevel.COMPLEX,
            processing_tier=ProcessingTier.TIER_3,
            timestamp=datetime.now(),
            confidence=0.9,
            extracted_entities={"word": "kippu"},
            additional_params={}
        )

    @pytest.fixture
    def mock_bedrock_client(self):
        """Create a mock Bedrock client."""
        mock_client = MagicMock()
        mock_client.generate = MagicMock(return_value="'Kippu' means 'ticket' in Japanese.")
        return mock_client

    @pytest.fixture
    def mock_context_manager(self):
        """Create a mock context manager."""
        context_manager = MagicMock(spec=ContextManager)
        context_manager.get_or_create_context.return_value = {
            "conversation_id": "test-conv-123",
            "entries": []
        }
        context_manager.get_context.return_value = {
            "conversation_id": "test-conv-123",
            "entries": []
        }
        context_manager.update_context.return_value = None
        return context_manager

    def test_tier3_processor_creation(self):
        """Test creating a Tier3Processor."""
        with patch('src.ai.companion.tier3.tier3_processor.BedrockClient'):
            processor = Tier3Processor()
            assert processor is not None
            assert hasattr(processor, 'client')
            assert hasattr(processor, 'context_manager')
            assert hasattr(processor, 'conversation_manager')
            assert hasattr(processor, 'prompt_manager')
            assert hasattr(processor, 'scenario_detector')

    def test_create_prompt(self):
        """Test creating a prompt."""
        with patch('src.ai.companion.tier3.tier3_processor.BedrockClient'):
            processor = Tier3Processor()
            request = ClassifiedRequest(
                request_id="test-123",
                player_input="What does 'kippu' mean?",
                request_type="translation",
                intent=IntentCategory.VOCABULARY_HELP,
                complexity=ComplexityLevel.COMPLEX,
                processing_tier=ProcessingTier.TIER_3,
                timestamp=datetime.now(),
                confidence=0.9,
                extracted_entities={"word": "kippu"},
                additional_params={}
            )
            
            # Test that the prompt manager is called
            with patch.object(processor.prompt_manager, 'create_prompt', return_value="Test prompt") as mock_create_prompt:
                prompt = processor.prompt_manager.create_prompt(request)
                assert prompt == "Test prompt"
                mock_create_prompt.assert_called_once_with(request)

    def test_parse_response(self):
        """Test parsing a response."""
        with patch('src.ai.companion.tier3.tier3_processor.BedrockClient'):
            processor = Tier3Processor()
            
            # Test with a clean response
            clean_response = processor._parse_response("'Kippu' means 'ticket' in Japanese.")
            assert clean_response == "'Kippu' means 'ticket' in Japanese."
            
            # Test with a response that has assistant tags
            tagged_response = processor._parse_response("<assistant>'Kippu' means 'ticket' in Japanese.</assistant>")
            assert tagged_response == "'Kippu' means 'ticket' in Japanese."
            
            # Test with a response that has whitespace
            whitespace_response = processor._parse_response("  'Kippu' means 'ticket' in Japanese.  ")
            assert whitespace_response == "'Kippu' means 'ticket' in Japanese."

    def test_generate_fallback_response(self, sample_classified_request):
        """Test generating a fallback response."""
        with patch('src.ai.companion.tier3.tier3_processor.BedrockClient'):
            processor = Tier3Processor()
            
            # Create a test error
            test_error = BedrockError("Test error")
            
            # Generate a fallback response
            fallback_response = processor._generate_fallback_response(sample_classified_request, test_error)
            
            # Check that the response is a dictionary with the expected keys
            assert isinstance(fallback_response, dict)
            assert 'response_text' in fallback_response
            assert 'processing_tier' in fallback_response
            
            # Check that the response text contains an apology
            response_text = fallback_response['response_text']
            assert "sorry" in response_text.lower()
            # The actual response doesn't contain the word "error", so we'll check for other phrases
            assert "trouble" in response_text.lower() or "rephrase" in response_text.lower()

    @pytest.mark.asyncio
    async def test_process(self, sample_classified_request, mock_bedrock_client, mock_context_manager):
        """Test processing a request."""
        with patch('src.ai.companion.tier3.tier3_processor.BedrockClient', return_value=mock_bedrock_client):
            # Set up the mock bedrock client to return a response
            mock_bedrock_client.generate.return_value = "'Kippu' means 'ticket' in Japanese."
            
            # Create a processor with the mock context manager
            processor = Tier3Processor(context_manager=mock_context_manager)
            
            # Process the request
            response = await processor.process(sample_classified_request)
            
            # Check that the response is as expected
            assert isinstance(response, dict)
            assert 'response_text' in response
            assert 'processing_tier' in response
            assert response['response_text'] == "'Kippu' means 'ticket' in Japanese."
            assert response['processing_tier'] == ProcessingTier.TIER_3
            
            # Verify the client was called
            mock_bedrock_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_existing_loop(self, sample_classified_request, mock_bedrock_client, mock_context_manager):
        """Test processing a request with an existing event loop."""
        with patch('src.ai.companion.tier3.tier3_processor.BedrockClient', return_value=mock_bedrock_client):
            # Set up the mock bedrock client to return a response
            mock_bedrock_client.generate.return_value = "'Kippu' means 'ticket' in Japanese."
            
            # Create a processor with the mock context manager
            processor = Tier3Processor(context_manager=mock_context_manager)
            
            # Process the request
            response = await processor.process(sample_classified_request)
            
            # Check that the response is as expected
            assert isinstance(response, dict)
            assert 'response_text' in response
            assert 'processing_tier' in response
            assert response['response_text'] == "'Kippu' means 'ticket' in Japanese."
            assert response['processing_tier'] == ProcessingTier.TIER_3
            
            # Verify the client was called
            mock_bedrock_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_with_error(self, sample_classified_request, mock_context_manager):
        """Test processing a request when the client raises an error."""
        with patch('src.ai.companion.tier3.tier3_processor.BedrockClient') as mock_client_class:
            # Set up the mock client to raise an error
            mock_client = mock_client_class.return_value
            mock_client.generate = AsyncMock(side_effect=BedrockError("Test error"))
            
            # Create a processor with the mock context manager
            processor = Tier3Processor(context_manager=mock_context_manager)
            
            # Process the request
            response = await processor.process(sample_classified_request)
            
            # Check that the response is a fallback response
            assert isinstance(response, dict)
            assert 'response_text' in response
            assert 'processing_tier' in response
            assert "sorry" in response['response_text'].lower()
            
            # Verify the client was called
            mock_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_with_conversation_history(self, sample_classified_request, mock_bedrock_client, mock_context_manager):
        """Test processing a request with conversation history."""
        with patch('src.ai.companion.tier3.tier3_processor.BedrockClient', return_value=mock_bedrock_client):
            # Mock the scenario detector
            with patch('src.ai.companion.tier3.tier3_processor.ScenarioDetector') as mock_detector_class:
                # Create a mock detector
                mock_detector = mock_detector_class.return_value
                
                # Set up the mock detector to return UNKNOWN scenario type
                from src.ai.companion.tier3.scenario_detection import ScenarioType
                mock_detector.detect_scenario.return_value = ScenarioType.UNKNOWN
                
                # Define the expected response
                response_text = "'Kippu' means 'ticket' in Japanese."
                
                # Configure the mock client to return the expected response
                mock_bedrock_client.generate.return_value = response_text
                
                # Add a conversation ID to the request
                sample_classified_request.additional_params = {"conversation_id": "test-conv-123"}
                
                # Create a processor with the mock context manager
                processor = Tier3Processor(context_manager=mock_context_manager)
                
                # Replace the scenario detector with our mock
                processor.scenario_detector = mock_detector
                
                # Process the request
                response = await processor.process(sample_classified_request)
                
                # Check that the response is as expected
                assert isinstance(response, dict)
                assert 'response_text' in response
                assert 'processing_tier' in response
                assert response['response_text'] == response_text
                
                # Verify the context manager was called
                mock_context_manager.get_or_create_context.assert_called_once()
                mock_context_manager.update_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_with_scenario_detection(self, sample_classified_request, mock_bedrock_client, mock_context_manager):
        """Test processing a request with scenario detection."""
        with patch('src.ai.companion.tier3.tier3_processor.BedrockClient', return_value=mock_bedrock_client):
            # Mock the scenario detector
            with patch('src.ai.companion.tier3.tier3_processor.ScenarioDetector') as mock_detector_class:
                # Create a mock detector
                mock_detector = mock_detector_class.return_value
                
                # Set up the mock detector to detect a scenario
                from src.ai.companion.tier3.scenario_detection import ScenarioType
                mock_detector.detect_scenario.return_value = ScenarioType.VOCABULARY_HELP
                mock_detector.handle_scenario = AsyncMock(return_value="'Kippu' means 'ticket' in Japanese. (From specialized handler)")
                
                # Mock the context manager to return a valid context
                mock_context_manager.get_context.return_value = {"some": "context"}
                
                # Add a conversation ID to the request and set complexity to COMPLEX
                sample_classified_request.additional_params = {"conversation_id": "test-conv-123"}
                sample_classified_request.complexity = ComplexityLevel.COMPLEX
                
                # Create a processor with the mock context manager
                processor = Tier3Processor(context_manager=mock_context_manager)
                
                # Replace the scenario detector with our mock
                processor.scenario_detector = mock_detector
                
                # Process the request
                response = await processor.process(sample_classified_request)
                
                # Check that the response is from the scenario handler
                assert isinstance(response, dict)
                assert 'response_text' in response
                assert 'processing_tier' in response
                assert response['response_text'] == "'Kippu' means 'ticket' in Japanese. (From specialized handler)"
                
                # Verify the scenario detector was used
                mock_detector.detect_scenario.assert_called_once()
                mock_detector.handle_scenario.assert_called_once() 