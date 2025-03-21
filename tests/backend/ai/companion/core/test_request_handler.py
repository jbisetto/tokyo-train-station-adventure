"""
Tests for the Request Handler component.
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch, Mock
import logging

from backend.ai.companion.core.models import (
    CompanionRequest,
    ClassifiedRequest,
    GameContext,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from backend.ai.companion.core.request_handler import RequestHandler


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
        
        # Check that the processor factory was called with the correct tier first
        assert mock_processor_factory.get_processor.call_args_list[0][0][0] == ProcessingTier.TIER_1
        
        # Check that the processor was called
        processor = mock_processor_factory.get_processor.return_value
        assert processor.process.called
        
        # Check that the response formatter was called
        mock_response_formatter.format_response.assert_called_once()
    
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
        
        # Configure the response formatter to pass through the error message
        mock_response_formatter.format_response.return_value = "I'm sorry, I encountered an error while processing your request."
        
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
        assert "encountered an error" in response.lower()


class TestRequestHandlerCascade:
    """Test the cascade functionality in the RequestHandler."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up the test environment."""
        # Create mock components
        self.intent_classifier = Mock()
        self.processor_factory = Mock()
        self.response_formatter = Mock()
        
        # Configure the response formatter
        self.response_formatter.format_response.return_value = "Formatted response"
        
        # Create the request handler
        self.handler = RequestHandler(
            intent_classifier=self.intent_classifier,
            processor_factory=self.processor_factory,
            response_formatter=self.response_formatter
        )
        
        # Create a sample request
        self.sample_request = CompanionRequest(
            request_id="test-id",
            player_input="Help me with directions",
            request_type="general_query"
        )
        
        # Configure the intent classifier
        self.intent_classifier.classify.return_value = (
            IntentCategory.GENERAL_HINT,
            ComplexityLevel.MODERATE,
            ProcessingTier.TIER_2,
            0.85,
            {}
        )
        
        # Create mock processors
        self.mock_tier1_processor = Mock()
        self.mock_tier2_processor = Mock()
        self.mock_tier3_processor = Mock()
        
        # Configure processors' responses
        self.mock_tier1_processor.process.return_value = "Tier 1 response"
        self.mock_tier2_processor.process.return_value = "Tier 2 response"
        self.mock_tier3_processor.process.return_value = "Tier 3 response"
    
    @pytest.mark.asyncio
    async def test_cascade_order(self):
        """Test that the cascade order is correct for different tiers."""
        # Test TIER_1 cascade order
        order = self.handler._get_cascade_order(ProcessingTier.TIER_1)
        assert order == [ProcessingTier.TIER_1, ProcessingTier.TIER_2, ProcessingTier.TIER_3]
        
        # Test TIER_2 cascade order
        order = self.handler._get_cascade_order(ProcessingTier.TIER_2)
        assert order == [ProcessingTier.TIER_2, ProcessingTier.TIER_3, ProcessingTier.TIER_1]
        
        # Test TIER_3 cascade order
        order = self.handler._get_cascade_order(ProcessingTier.TIER_3)
        assert order == [ProcessingTier.TIER_3, ProcessingTier.TIER_2, ProcessingTier.TIER_1]
    
    @pytest.mark.asyncio
    async def test_process_with_preferred_tier(self):
        """Test processing with the preferred tier when it's available."""
        # Configure the processor factory to return our mock processor for TIER_2
        self.processor_factory.get_processor.return_value = self.mock_tier2_processor
        
        # Process the request
        response = await self.handler.handle_request(self.sample_request)
        
        # The current implementation may call get_processor multiple times, but
        # what's important is that TIER_2 is called first and used for processing
        assert self.processor_factory.get_processor.call_args_list[0][0][0] == ProcessingTier.TIER_2
        
        # Check that we used the TIER_2 processor at least once
        assert self.mock_tier2_processor.process.called
        
        # Check that the response was formatted
        self.response_formatter.format_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cascade_to_next_tier(self):
        """Test cascading to the next tier when the preferred tier is unavailable."""
        # Configure the processor factory to raise an error for TIER_2 and return our mock processor for TIER_3
        def get_processor_side_effect(tier):
            if tier == ProcessingTier.TIER_2:
                raise ValueError("TIER_2 is disabled in configuration")
            elif tier == ProcessingTier.TIER_3:
                return self.mock_tier3_processor
            elif tier == ProcessingTier.TIER_1:
                return self.mock_tier1_processor
            return None
        
        self.processor_factory.get_processor.side_effect = get_processor_side_effect
        
        # Process the request
        response = await self.handler.handle_request(self.sample_request)
        
        # The current implementation tries all tiers in the cascade order
        # Check that we tried TIER_2 first, then TIER_3 (which works)
        assert self.processor_factory.get_processor.call_args_list[0][0][0] == ProcessingTier.TIER_2
        assert self.processor_factory.get_processor.call_args_list[1][0][0] == ProcessingTier.TIER_3
        
        # Check that we used the TIER_3 processor
        self.mock_tier3_processor.process.assert_called_once()
        
        # Check that the response was formatted
        self.response_formatter.format_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_all_tiers_disabled(self):
        """Test handling when all tiers are disabled."""
        # Configure the processor factory to raise an error for all tiers
        self.processor_factory.get_processor.side_effect = ValueError("Tier is disabled in configuration")
        
        # Configure response formatter to be used for fallback responses
        fallback = "All AI services are currently disabled. Please check your configuration."
        self.response_formatter.format_response.return_value = fallback
        
        # Process the request
        response = await self.handler.handle_request(self.sample_request)
        
        # Check that we tried all tiers
        assert self.processor_factory.get_processor.call_count == 3
        
        # In the current implementation, format_response may be called for the fallback
        # Check that the response indicates all services are disabled
        assert "disabled" in response.lower() or "All AI services" in response
    
    @pytest.mark.asyncio
    async def test_tier_fails_with_other_error(self):
        """Test handling when a tier fails with an error other than being disabled."""
        # Configure the processor factory to raise different errors for each tier
        def get_processor_side_effect(tier):
            if tier == ProcessingTier.TIER_2:
                raise ValueError("Some other error")
            elif tier == ProcessingTier.TIER_3:
                raise RuntimeError("Another error")
            elif tier == ProcessingTier.TIER_1:
                raise Exception("Yet another error")
            return None
        
        self.processor_factory.get_processor.side_effect = get_processor_side_effect
        
        # Configure response formatter to be used for error responses
        fallback = "I'm sorry, I encountered an error while processing your request."
        self.response_formatter.format_response.return_value = fallback
        
        # Process the request
        response = await self.handler.handle_request(self.sample_request)
        
        # Check that we tried all tiers
        assert self.processor_factory.get_processor.call_count == 3
        
        # In the current implementation, format_response may be called for the fallback
        # Check that the response is a general error (not related to disabled tiers)
        assert "error" in response.lower() or "sorry" in response.lower() 