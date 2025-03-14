"""
Tests for the Request Handler component.
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch

from backend.ai.companion.core.models import (
    CompanionRequest,
    ClassifiedRequest,
    GameContext,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)


@pytest.fixture
def mock_intent_classifier():
    """Create a mock intent classifier."""
    mock = MagicMock()
    mock.classify.return_value = (
        IntentCategory.VOCABULARY_HELP,
        ComplexityLevel.SIMPLE,
        ProcessingTier.TIER_1,
        0.9,
        {"word": "kippu"}
    )
    return mock


@pytest.fixture
def mock_processor_factory():
    """Create a mock processor factory."""
    mock = MagicMock()
    mock_processor = MagicMock()
    mock_processor.process.return_value = "This is a test response."
    mock.get_processor.return_value = mock_processor
    return mock


@pytest.fixture
def mock_response_formatter():
    """Create a mock response formatter."""
    mock = MagicMock()
    mock.format_response.return_value = "Formatted response."
    return mock


@pytest.fixture
def sample_game_context():
    """Create a sample game context."""
    return GameContext(
        player_location="main_concourse",
        current_objective="find_ticket_machine",
        nearby_npcs=["station_attendant", "tourist"],
        nearby_objects=["ticket_machine", "information_board"],
        player_inventory=["wallet", "phone"],
        language_proficiency={"vocabulary": 0.4, "grammar": 0.3, "reading": 0.5},
        game_progress={"tutorial_completed": True, "tickets_purchased": 0}
    )


class TestRequestHandler:
    """Tests for the RequestHandler class."""
    
    def test_initialization(self, mock_intent_classifier, mock_processor_factory, mock_response_formatter):
        """Test that the RequestHandler can be initialized with the required components."""
        from backend.ai.companion.core.request_handler import RequestHandler
        
        handler = RequestHandler(
            intent_classifier=mock_intent_classifier,
            processor_factory=mock_processor_factory,
            response_formatter=mock_response_formatter
        )
        
        assert handler.intent_classifier == mock_intent_classifier
        assert handler.processor_factory == mock_processor_factory
        assert handler.response_formatter == mock_response_formatter
    
    @pytest.mark.asyncio
    async def test_handle_request_flow(self, mock_intent_classifier, mock_processor_factory, mock_response_formatter, sample_game_context):
        """Test the complete request handling flow."""
        from backend.ai.companion.core.request_handler import RequestHandler
        
        # Create a request handler
        handler = RequestHandler(
            intent_classifier=mock_intent_classifier,
            processor_factory=mock_processor_factory,
            response_formatter=mock_response_formatter
        )
        
        # Create a request
        request_id = str(uuid.uuid4())
        request = CompanionRequest(
            request_id=request_id,
            player_input="What does 'kippu' mean?",
            request_type="vocabulary",
            game_context=sample_game_context
        )
        
        # Handle the request
        response = await handler.handle_request(request)
        
        # Check that the classifier was called
        mock_intent_classifier.classify.assert_called_once_with(request)
        
        # Check that the processor factory was called with the correct tier
        mock_processor_factory.get_processor.assert_called_once_with(ProcessingTier.TIER_1)
        
        # Check that the processor was called with the classified request
        processor = mock_processor_factory.get_processor.return_value
        processor.process.assert_called_once()
        
        # Check that the response formatter was called
        mock_response_formatter.format_response.assert_called_once()
        
        # Check that the response is correct
        assert response == "Formatted response."
    
    @pytest.mark.asyncio
    async def test_handle_request_with_conversation_context(self, mock_intent_classifier, mock_processor_factory, mock_response_formatter):
        """Test handling a request with conversation context."""
        from backend.ai.companion.core.request_handler import RequestHandler
        from backend.ai.companion.core.models import ConversationContext
        
        # Create a request handler
        handler = RequestHandler(
            intent_classifier=mock_intent_classifier,
            processor_factory=mock_processor_factory,
            response_formatter=mock_response_formatter
        )
        
        # Create a conversation context
        conversation_context = ConversationContext(conversation_id="conv-123")
        
        # Create a request
        request = CompanionRequest(
            request_id="req-123",
            player_input="What does 'kippu' mean?",
            request_type="vocabulary"
        )
        
        # Handle the request with conversation context
        response = await handler.handle_request(request, conversation_context)
        
        # Check that the conversation context was updated
        assert len(conversation_context.request_history) == 1
        assert len(conversation_context.response_history) == 1
        assert conversation_context.request_history[0] == request
    
    @pytest.mark.asyncio
    async def test_handle_request_with_error(self, mock_intent_classifier, mock_processor_factory, mock_response_formatter):
        """Test handling a request when an error occurs."""
        from backend.ai.companion.core.request_handler import RequestHandler
        
        # Configure the processor to raise an exception
        processor = mock_processor_factory.get_processor.return_value
        processor.process.side_effect = Exception("Test error")
        
        # Create a request handler
        handler = RequestHandler(
            intent_classifier=mock_intent_classifier,
            processor_factory=mock_processor_factory,
            response_formatter=mock_response_formatter
        )
        
        # Create a request
        request = CompanionRequest(
            request_id="req-456",
            player_input="What does 'kippu' mean?",
            request_type="vocabulary"
        )
        
        # Handle the request and check that it handles the error
        response = await handler.handle_request(request)
        
        # Check that the error was handled and a fallback response was returned
        assert "error" in response.lower() or "sorry" in response.lower() 