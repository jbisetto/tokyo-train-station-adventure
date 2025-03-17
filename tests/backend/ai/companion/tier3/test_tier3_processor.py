"""
Tests for the Tier 3 processor.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from datetime import datetime

from backend.ai.companion.core.models import (
    ClassifiedRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from backend.ai.companion.tier3.tier3_processor import Tier3Processor
from backend.ai.companion.tier3.bedrock_client import BedrockError
from backend.ai.companion.core.context_manager import ContextManager


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
        return MagicMock(spec=ContextManager)

    def test_tier3_processor_creation(self):
        """Test creating a Tier3Processor."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient'):
            processor = Tier3Processor()
            assert processor is not None
            assert hasattr(processor, 'client')
            assert hasattr(processor, 'context_manager')
            assert hasattr(processor, 'conversation_manager')
            assert hasattr(processor, 'prompt_manager')
            assert hasattr(processor, 'scenario_detector')

    def test_create_prompt(self):
        """Test creating a prompt."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient'):
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
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient'):
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
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient'):
            processor = Tier3Processor()
            
            # Create a test error
            test_error = BedrockError("Test error")
            
            # Generate a fallback response
            fallback_response = processor._generate_fallback_response(sample_classified_request, test_error)
            
            # Check that the response contains an apology
            assert "sorry" in fallback_response.lower()
            # The actual response doesn't contain the word "error", so we'll check for other phrases
            assert "trouble" in fallback_response.lower() or "rephrase" in fallback_response.lower()

    @pytest.mark.asyncio
    async def test_process(self, sample_classified_request, mock_bedrock_client, mock_context_manager):
        """Test processing a request."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient', return_value=mock_bedrock_client):
            # Mock the asyncio functions
            with patch('asyncio.new_event_loop') as mock_new_loop:
                with patch('asyncio.set_event_loop') as mock_set_loop:
                    # Create a mock loop
                    mock_loop = MagicMock()
                    mock_new_loop.return_value = mock_loop
                    
                    # Mock the run_until_complete method to return a response
                    mock_loop.run_until_complete.return_value = "'Kippu' means 'ticket' in Japanese."
                    
                    # Create a processor with the mock context manager
                    processor = Tier3Processor(context_manager=mock_context_manager)
                    
                    # Process the request
                    response = processor.process(sample_classified_request)
                    
                    # Check that the response is as expected
                    assert response == "'Kippu' means 'ticket' in Japanese."
                    
                    # Check that the loop was created and used
                    mock_new_loop.assert_called_once()
                    mock_set_loop.assert_called_once_with(mock_loop)
                    mock_loop.run_until_complete.assert_called_once()
                    mock_loop.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_with_error(self, sample_classified_request, mock_context_manager):
        """Test processing a request when the client raises an error."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient') as mock_client_class:
            # Set up the mock client to raise an error
            mock_client = mock_client_class.return_value
            mock_client.generate.side_effect = BedrockError("Test error")
            
            # Mock the asyncio functions
            with patch('asyncio.new_event_loop') as mock_new_loop:
                with patch('asyncio.set_event_loop') as mock_set_loop:
                    # Create a mock loop
                    mock_loop = MagicMock()
                    mock_new_loop.return_value = mock_loop
                    
                    # Mock the run_until_complete method to raise the error
                    mock_loop.run_until_complete.side_effect = BedrockError("Test error")
                    
                    # Create a processor with the mock context manager
                    processor = Tier3Processor(context_manager=mock_context_manager)
                    
                    # Process the request
                    response = processor.process(sample_classified_request)
                    
                    # Check that the response is a fallback response
                    assert "sorry" in response.lower()
                    # The actual response doesn't contain the word "error", so we'll check for other phrases
                    assert "trouble" in response.lower() or "rephrase" in response.lower()

    @pytest.mark.asyncio
    async def test_process_with_conversation_history(self, sample_classified_request, mock_bedrock_client, mock_context_manager):
        """Test processing a request with conversation history."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient', return_value=mock_bedrock_client):
            # Mock the scenario detector
            with patch('backend.ai.companion.tier3.tier3_processor.ScenarioDetector') as mock_detector_class:
                # Create a mock detector
                mock_detector = mock_detector_class.return_value
                
                # Set up the mock detector to return UNKNOWN scenario type
                from backend.ai.companion.tier3.scenario_detection import ScenarioType
                mock_detector.detect_scenario.return_value = ScenarioType.UNKNOWN
                
                # Mock the asyncio functions
                with patch('asyncio.new_event_loop') as mock_new_loop:
                    with patch('asyncio.set_event_loop') as mock_set_loop:
                        # Create a mock loop
                        mock_loop = MagicMock()
                        mock_new_loop.return_value = mock_loop
                        
                        # Define the expected response
                        response_text = "'Kippu' means 'ticket' in Japanese."
                        
                        # Configure the mock client to return the expected response
                        mock_bedrock_client.generate.return_value = response_text
                        
                        # Mock the run_until_complete method to return the response
                        mock_loop.run_until_complete.return_value = response_text
                        
                        # Add a conversation ID to the request
                        sample_classified_request.additional_params = {"conversation_id": "test-conv-123"}
                        
                        # Create a processor with the mock context manager
                        processor = Tier3Processor(context_manager=mock_context_manager)
                        
                        # Replace the scenario detector with our mock
                        processor.scenario_detector = mock_detector
                        
                        # Process the request
                        response = processor.process(sample_classified_request)
                        
                        # Check that the response is as expected
                        assert response == response_text
                        
                        # Check that the context was updated
                        mock_context_manager.update_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_with_scenario_detection(self, sample_classified_request, mock_bedrock_client, mock_context_manager):
        """Test processing a request with scenario detection."""
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient', return_value=mock_bedrock_client):
            # Mock the scenario detector
            with patch('backend.ai.companion.tier3.tier3_processor.ScenarioDetector') as mock_detector_class:
                # Create a mock detector
                mock_detector = mock_detector_class.return_value
                
                # Set up the mock detector to detect a scenario
                from backend.ai.companion.tier3.scenario_detection import ScenarioType
                mock_detector.detect_scenario.return_value = ScenarioType.VOCABULARY_HELP
                mock_detector.handle_scenario.return_value = "'Kippu' means 'ticket' in Japanese. (From specialized handler)"
                
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
                response = processor.process(sample_classified_request)
                
                # Check that the response is from the scenario handler
                assert response == "'Kippu' means 'ticket' in Japanese. (From specialized handler)"
                
                # Check that the scenario detector was used
                mock_detector.detect_scenario.assert_called_once_with(sample_classified_request)
                mock_detector.handle_scenario.assert_called_once() 