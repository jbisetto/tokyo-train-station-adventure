"""
Tests for scenario detection in Tier 3.

These tests verify that the companion AI can detect specific scenarios
in player requests and handle them appropriately.
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from backend.ai.companion.core.models import (
    ClassifiedRequest,
    CompanionRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from backend.ai.companion.tier3.context_manager import (
    ConversationContext,
    ContextManager,
    ContextEntry
)


@pytest.fixture
def sample_context():
    """Create a sample conversation context for testing."""
    context = ConversationContext(
        conversation_id="conv-123",
        player_id="player-456",
        player_language_level="N5",
        current_location="ticket_counter",
        created_at=datetime.now() - timedelta(minutes=10),
        updated_at=datetime.now() - timedelta(minutes=5)
    )
    
    # Add some entries to the context
    context.entries = [
        ContextEntry(
            request="What does 'kippu' mean?",
            response="'Kippu' means 'ticket' in Japanese.",
            timestamp=datetime.now() - timedelta(minutes=5),
            intent=IntentCategory.VOCABULARY_HELP,
            entities={"word": "kippu"}
        ),
        ContextEntry(
            request="How do I ask for a ticket to Odawara?",
            response="You can say 'Odawara made no kippu o kudasai'.",
            timestamp=datetime.now() - timedelta(minutes=3),
            intent=IntentCategory.TRANSLATION_CONFIRMATION,
            entities={"destination": "Odawara"}
        )
    ]
    
    return context


@pytest.fixture
def sample_classified_request():
    """Create a sample classified request for testing."""
    return ClassifiedRequest(
        request_id=str(uuid.uuid4()),
        player_input="I want to buy a ticket to Tokyo",
        request_type="transaction",
        timestamp=datetime.now(),
        intent=IntentCategory.GENERAL_HINT,
        complexity=ComplexityLevel.COMPLEX,
        processing_tier=ProcessingTier.TIER_3,
        confidence=0.9,
        extracted_entities={"destination": "Tokyo"},
        additional_params={"conversation_id": "conv-123"}
    )


class TestScenarioDetector:
    """Tests for the ScenarioDetector class."""
    
    def test_scenario_detector_creation(self):
        """Test that a ScenarioDetector can be created."""
        from backend.ai.companion.tier3.scenario_detection import ScenarioDetector
        
        detector = ScenarioDetector()
        
        assert detector is not None
        assert hasattr(detector, 'detect_scenario')
        assert hasattr(detector, 'get_scenario_handler')
    
    def test_detect_ticket_purchase_scenario(self, sample_classified_request):
        """Test detecting a ticket purchase scenario."""
        from backend.ai.companion.tier3.scenario_detection import (
            ScenarioDetector,
            ScenarioType
        )
        
        detector = ScenarioDetector()
        
        # Test with a ticket purchase request
        sample_classified_request.player_input = "I want to buy a ticket to Tokyo"
        sample_classified_request.intent = IntentCategory.GENERAL_HINT
        sample_classified_request.extracted_entities = {"destination": "Tokyo"}
        
        scenario = detector.detect_scenario(sample_classified_request)
        
        assert scenario == ScenarioType.TICKET_PURCHASE
    
    def test_detect_navigation_scenario(self, sample_classified_request):
        """Test detecting a navigation scenario."""
        from backend.ai.companion.tier3.scenario_detection import (
            ScenarioDetector,
            ScenarioType
        )
        
        detector = ScenarioDetector()
        
        # Test with a navigation request
        sample_classified_request.player_input = "How do I get to platform 3?"
        sample_classified_request.intent = IntentCategory.DIRECTION_GUIDANCE
        sample_classified_request.extracted_entities = {"location": "platform 3"}
        
        scenario = detector.detect_scenario(sample_classified_request)
        
        assert scenario == ScenarioType.NAVIGATION
    
    def test_detect_vocabulary_scenario(self, sample_classified_request):
        """Test detecting a vocabulary help scenario."""
        from backend.ai.companion.tier3.scenario_detection import (
            ScenarioDetector,
            ScenarioType
        )
        
        detector = ScenarioDetector()
        
        # Test with a vocabulary help request
        sample_classified_request.player_input = "What does 'eki' mean?"
        sample_classified_request.intent = IntentCategory.VOCABULARY_HELP
        sample_classified_request.extracted_entities = {"word": "eki"}
        
        scenario = detector.detect_scenario(sample_classified_request)
        
        assert scenario == ScenarioType.VOCABULARY_HELP
    
    def test_detect_grammar_scenario(self, sample_classified_request):
        """Test detecting a grammar explanation scenario."""
        from backend.ai.companion.tier3.scenario_detection import (
            ScenarioDetector,
            ScenarioType
        )
        
        detector = ScenarioDetector()
        
        # Test with a grammar explanation request
        sample_classified_request.player_input = "Can you explain the difference between は and が?"
        sample_classified_request.intent = IntentCategory.GRAMMAR_EXPLANATION
        sample_classified_request.extracted_entities = {"grammar_point": "は vs が"}
        
        scenario = detector.detect_scenario(sample_classified_request)
        
        assert scenario == ScenarioType.GRAMMAR_EXPLANATION
    
    def test_detect_cultural_scenario(self, sample_classified_request):
        """Test detecting a cultural information scenario."""
        from backend.ai.companion.tier3.scenario_detection import (
            ScenarioDetector,
            ScenarioType
        )
        
        detector = ScenarioDetector()
        
        # Test with a cultural information request
        sample_classified_request.player_input = "What's the proper etiquette when riding a train in Japan?"
        sample_classified_request.intent = IntentCategory.GENERAL_HINT
        sample_classified_request.extracted_entities = {"topic": "train etiquette"}
        
        scenario = detector.detect_scenario(sample_classified_request)
        
        assert scenario == ScenarioType.CULTURAL_INFORMATION
    
    def test_get_scenario_handler(self, sample_classified_request):
        """Test getting a handler for a detected scenario."""
        from backend.ai.companion.tier3.scenario_detection import (
            ScenarioDetector,
            ScenarioType
        )
        
        detector = ScenarioDetector()
        
        # Test with a ticket purchase request
        sample_classified_request.player_input = "I want to buy a ticket to Tokyo"
        sample_classified_request.intent = IntentCategory.GENERAL_HINT
        sample_classified_request.extracted_entities = {"destination": "Tokyo"}
        
        scenario = detector.detect_scenario(sample_classified_request)
        handler = detector.get_scenario_handler(scenario)
        
        assert handler is not None
        assert hasattr(handler, 'handle')
    
    def test_handle_scenario(self, sample_classified_request, sample_context):
        """Test handling a detected scenario."""
        from backend.ai.companion.tier3.scenario_detection import ScenarioDetector
        
        detector = ScenarioDetector()
        context_manager = MagicMock()
        context_manager.get_context.return_value = sample_context
        bedrock_client = MagicMock()
        bedrock_client.generate_text.return_value = "To buy a ticket to Tokyo, you can use the ticket machine or go to the ticket counter. At the ticket counter, you can say 'Tokyo made no kippu o kudasai'."
        
        # Test with a ticket purchase request
        sample_classified_request.player_input = "I want to buy a ticket to Tokyo"
        sample_classified_request.intent = IntentCategory.GENERAL_HINT
        sample_classified_request.extracted_entities = {"destination": "Tokyo"}
        
        response = detector.handle_scenario(
            sample_classified_request,
            context_manager,
            bedrock_client
        )
        
        assert response is not None
        assert "Tokyo" in response
        assert "ticket" in response
    
    def test_integration_with_tier3_processor(self, sample_classified_request):
        """Test integration with the Tier3Processor."""
        from backend.ai.companion.tier3.scenario_detection import (
            ScenarioDetector,
            ScenarioType
        )
        
        # Mock the necessary components
        detector = ScenarioDetector()
        context_manager = MagicMock()
        bedrock_client = MagicMock()
        bedrock_client.generate_text.return_value = "To buy a ticket to Tokyo, you can use the ticket machine or go to the ticket counter. At the ticket counter, you can say 'Tokyo made no kippu o kudasai'."
        
        # Mock the scenario detection
        with patch.object(
            detector,
            'detect_scenario',
            return_value=ScenarioType.TICKET_PURCHASE
        ):
            # Test the handle_scenario method
            response = detector.handle_scenario(
                sample_classified_request,
                context_manager,
                bedrock_client
            )
            
            assert response is not None
            assert "Tokyo" in response
            assert "ticket" in response 