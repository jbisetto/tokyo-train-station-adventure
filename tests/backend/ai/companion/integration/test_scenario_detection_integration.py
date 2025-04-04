"""
Integration tests for the scenario detection system.

These tests verify that the scenario detection system works correctly
with the rest of the companion AI system.
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

from src.ai.companion.core.models import (
    ClassifiedRequest,
    CompanionRequest,
    ConversationContext,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from src.ai.companion.core.request_handler import RequestHandler
from src.ai.companion.tier3.scenario_detection import ScenarioDetector, ScenarioType
from src.ai.companion.tier3.tier3_processor import Tier3Processor
from src.ai.companion.tier3.context_manager import ContextManager


@pytest.fixture
def mock_context_manager():
    """Create a mock context manager for testing."""
    context_manager = MagicMock(spec=ContextManager)
    # Set up the mock to return a valid context
    context_manager.get_context.return_value = MagicMock(
        player_language_level="N5",
        current_location="ticket_counter",
        entries=[]
    )
    return context_manager


@pytest.fixture
def mock_bedrock_client():
    """Create a mock Bedrock client for testing."""
    client = MagicMock()
    client.generate_text = AsyncMock(return_value="This is a test response.")
    client.generate = AsyncMock(return_value="This is a test response.")
    return client


class TestScenarioDetectionIntegration:
    """Integration tests for the scenario detection system."""
    
    @pytest.mark.asyncio
    async def test_scenario_detection_with_tier3_processor(self, mock_context_manager, mock_bedrock_client):
        """Test that the scenario detection system works with the Tier3Processor."""
        # Create a Tier3Processor with our mocks
        with patch('src.ai.companion.tier3.tier3_processor.BedrockClient', return_value=mock_bedrock_client):
            processor = Tier3Processor(context_manager=mock_context_manager)
            
            # Create a request that should trigger the ticket purchase scenario
            request = ClassifiedRequest(
                request_id=str(uuid.uuid4()),
                player_input="I want to buy a ticket to Tokyo",
                request_type="transaction",
                timestamp=datetime.now(),
                intent=IntentCategory.GENERAL_HINT,
                complexity=ComplexityLevel.COMPLEX,
                processing_tier=ProcessingTier.TIER_3,
                confidence=0.9,
                extracted_entities={"destination": "Tokyo"},
                additional_params={"conversation_id": "test-conversation"}
            )
            
            # Process the request
            response = await processor.process(request)
            
            # Verify that the response is what we expect
            assert isinstance(response, dict)
            assert 'response_text' in response
            assert 'processing_tier' in response
            assert response['response_text'] == "This is a test response."
            assert response['processing_tier'] == ProcessingTier.TIER_3
            
            # Verify that the scenario detection was used
            mock_bedrock_client.generate_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scenario_detection_with_request_handler(self, mock_context_manager, mock_bedrock_client):
        """Test that the scenario detection system works with the RequestHandler."""
        # Create a Tier3Processor with our mocks
        with patch('src.ai.companion.tier3.tier3_processor.BedrockClient', return_value=mock_bedrock_client):
            processor = Tier3Processor(context_manager=mock_context_manager)
            
            # Create mocks for the RequestHandler dependencies
            intent_classifier = MagicMock()
            processor_factory = MagicMock()
            processor_factory.get_processor.return_value = processor
            response_formatter = MagicMock()
            response_formatter.format_response.return_value = "Formatted response"
            
            # Create a RequestHandler with our mocks
            handler = RequestHandler(
                intent_classifier=intent_classifier,
                processor_factory=processor_factory,
                response_formatter=response_formatter
            )
            
            # Create a request that should trigger the ticket purchase scenario
            request_id = str(uuid.uuid4())
            player_input = "I want to buy a ticket to Tokyo"
            
            # Create a CompanionRequest
            companion_request = CompanionRequest(
                request_id=request_id,
                player_input=player_input,
                request_type="transaction",
                timestamp=datetime.now(),
                additional_params={"conversation_id": "test-conversation"}
            )
            
            # Create a ConversationContext
            conversation_context = ConversationContext(
                conversation_id="test-conversation",
                request_history=[],
                response_history=[]
            )
            
            # Mock the intent classifier to return values that will trigger scenario detection
            intent_classifier.classify.return_value = (
                IntentCategory.GENERAL_HINT,
                ComplexityLevel.COMPLEX,
                ProcessingTier.TIER_3,
                0.9,
                {"destination": "Tokyo"}
            )
            
            # Process the request
            response = await handler.handle_request(companion_request, conversation_context)
            
            # Verify that the response is what we expect
            assert response == "Formatted response"
            
            # Verify that the processor was called
            processor_factory.get_processor.assert_called_once_with(ProcessingTier.TIER_3)
            
            # Verify that the scenario detection was used (indirectly through the processor)
            mock_bedrock_client.generate_text.assert_called_once()
    
    def test_different_scenario_types(self, mock_context_manager, mock_bedrock_client):
        """Test that different scenario types are detected correctly."""
        # Create a ScenarioDetector
        detector = ScenarioDetector()
        
        # Test ticket purchase scenario
        ticket_request = ClassifiedRequest(
            request_id=str(uuid.uuid4()),
            player_input="I want to buy a ticket to Tokyo",
            request_type="transaction",
            timestamp=datetime.now(),
            intent=IntentCategory.GENERAL_HINT,
            complexity=ComplexityLevel.COMPLEX,
            processing_tier=ProcessingTier.TIER_3,
            confidence=0.9,
            extracted_entities={"destination": "Tokyo"}
        )
        assert detector.detect_scenario(ticket_request) == ScenarioType.TICKET_PURCHASE
        
        # Test navigation scenario
        navigation_request = ClassifiedRequest(
            request_id=str(uuid.uuid4()),
            player_input="How do I get to platform 3?",
            request_type="navigation",
            timestamp=datetime.now(),
            intent=IntentCategory.DIRECTION_GUIDANCE,
            complexity=ComplexityLevel.COMPLEX,
            processing_tier=ProcessingTier.TIER_3,
            confidence=0.9,
            extracted_entities={"location": "platform 3"}
        )
        assert detector.detect_scenario(navigation_request) == ScenarioType.NAVIGATION
        
        # Test vocabulary help scenario
        vocabulary_request = ClassifiedRequest(
            request_id=str(uuid.uuid4()),
            player_input="What does 'eki' mean?",
            request_type="vocabulary",
            timestamp=datetime.now(),
            intent=IntentCategory.VOCABULARY_HELP,
            complexity=ComplexityLevel.COMPLEX,
            processing_tier=ProcessingTier.TIER_3,
            confidence=0.9,
            extracted_entities={"word": "eki"}
        )
        assert detector.detect_scenario(vocabulary_request) == ScenarioType.VOCABULARY_HELP 