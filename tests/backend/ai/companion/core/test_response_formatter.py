"""
Tests for the Response Formatter component.
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch

from backend.ai.companion.core.models import (
    ClassifiedRequest,
    CompanionRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from backend.ai.companion.config import PERSONALITY_TRAITS


@pytest.fixture
def sample_classified_request():
    """Create a sample classified request."""
    request_id = str(uuid.uuid4())
    return ClassifiedRequest(
        request_id=request_id,
        player_input="What does 'kippu' mean?",
        request_type="vocabulary",
        intent=IntentCategory.VOCABULARY_HELP,
        complexity=ComplexityLevel.SIMPLE,
        processing_tier=ProcessingTier.TIER_1,
        confidence=0.9,
        extracted_entities={"word": "kippu"}
    )


@pytest.fixture
def sample_processor_response():
    """Create a sample processor response."""
    return "'Kippu' means 'ticket' in Japanese. It's written as '切符' in kanji."


class TestResponseFormatter:
    """Tests for the ResponseFormatter class."""
    
    def test_initialization(self):
        """Test that the ResponseFormatter can be initialized."""
        from backend.ai.companion.core.response_formatter import ResponseFormatter
        
        formatter = ResponseFormatter()
        
        assert formatter is not None
        assert hasattr(formatter, 'format_response')
    
    def test_format_response_basic(self, sample_classified_request, sample_processor_response):
        """Test basic response formatting."""
        from backend.ai.companion.core.response_formatter import ResponseFormatter
        
        formatter = ResponseFormatter()
        
        # Format the response
        formatted_response = formatter.format_response(
            processor_response=sample_processor_response,
            classified_request=sample_classified_request
        )
        
        # Check that the response is a string
        assert isinstance(formatted_response, str)
        assert len(formatted_response) > 0
        
        # Check that the response contains the processor response
        assert sample_processor_response in formatted_response
    
    def test_personality_injection(self, sample_classified_request, sample_processor_response):
        """Test that personality traits are injected into the response."""
        from backend.ai.companion.core.response_formatter import ResponseFormatter
        
        formatter = ResponseFormatter()
        
        # Format the response with different personality settings
        friendly_formatter = ResponseFormatter(personality_traits={"friendliness": 1.0})
        neutral_formatter = ResponseFormatter(personality_traits={"friendliness": 0.5})
        unfriendly_formatter = ResponseFormatter(personality_traits={"friendliness": 0.0})
        
        friendly_response = friendly_formatter.format_response(
            processor_response=sample_processor_response,
            classified_request=sample_classified_request
        )
        
        neutral_response = neutral_formatter.format_response(
            processor_response=sample_processor_response,
            classified_request=sample_classified_request
        )
        
        unfriendly_response = unfriendly_formatter.format_response(
            processor_response=sample_processor_response,
            classified_request=sample_classified_request
        )
        
        # Check that the responses are different
        assert friendly_response != neutral_response or neutral_response != unfriendly_response
        
        # Check that the friendly response has more friendly words
        friendly_words = ["happy", "glad", "friend", "great", "wonderful", "excellent"]
        friendly_count = sum(word in friendly_response.lower() for word in friendly_words)
        unfriendly_count = sum(word in unfriendly_response.lower() for word in friendly_words)
        
        assert friendly_count >= unfriendly_count
    
    def test_learning_cue_integration(self, sample_classified_request, sample_processor_response):
        """Test that learning cues are integrated into the response."""
        from backend.ai.companion.core.response_formatter import ResponseFormatter
        
        formatter = ResponseFormatter()
        
        # Format the response
        formatted_response = formatter.format_response(
            processor_response=sample_processor_response,
            classified_request=sample_classified_request,
            add_learning_cues=True
        )
        
        # Check that the response contains learning cues
        learning_cue_indicators = ["Remember", "Note", "Tip", "Hint", "Practice"]
        has_learning_cue = any(indicator in formatted_response for indicator in learning_cue_indicators)
        
        assert has_learning_cue
    
    def test_emotion_integration(self, sample_classified_request, sample_processor_response):
        """Test that emotions are integrated into the response."""
        from backend.ai.companion.core.response_formatter import ResponseFormatter
        
        # Get the emotion expressions directly from the class to ensure test matches implementation
        happy_expressions = [expr.lower() for expr in ResponseFormatter.EMOTION_EXPRESSIONS["happy"]]
        excited_expressions = [expr.lower() for expr in ResponseFormatter.EMOTION_EXPRESSIONS["excited"]]
        neutral_expressions = [expr.lower() for expr in ResponseFormatter.EMOTION_EXPRESSIONS["neutral"]]
        
        formatter = ResponseFormatter()
        
        # Format the response with different emotions
        happy_response = formatter.format_response(
            processor_response=sample_processor_response,
            classified_request=sample_classified_request,
            emotion="happy"
        )
        
        excited_response = formatter.format_response(
            processor_response=sample_processor_response,
            classified_request=sample_classified_request,
            emotion="excited"
        )
        
        neutral_response = formatter.format_response(
            processor_response=sample_processor_response,
            classified_request=sample_classified_request,
            emotion="neutral"
        )
        
        # Check that the responses are different
        assert happy_response != excited_response or excited_response != neutral_response
        
        # Check that the responses contain emotion expressions
        happy_response_lower = happy_response.lower()
        excited_response_lower = excited_response.lower()
        neutral_response_lower = neutral_response.lower()
        
        # Check that at least one of the emotion expressions is in the response
        assert any(expr in happy_response_lower for expr in happy_expressions)
        assert any(expr in excited_response_lower for expr in excited_expressions)
        assert any(expr in neutral_response_lower for expr in neutral_expressions)
    
    def test_response_validation(self, sample_classified_request):
        """Test that responses are validated."""
        from backend.ai.companion.core.response_formatter import ResponseFormatter
        
        formatter = ResponseFormatter()
        
        # Test with an empty response
        empty_response = ""
        
        # Format the response
        formatted_response = formatter.format_response(
            processor_response=empty_response,
            classified_request=sample_classified_request
        )
        
        # Check that the response is not empty
        assert len(formatted_response) > 0
        
        # Test with a very short response
        short_response = "Yes."
        
        # Format the response
        formatted_response = formatter.format_response(
            processor_response=short_response,
            classified_request=sample_classified_request
        )
        
        # Check that the response is longer than the original
        assert len(formatted_response) > len(short_response)
    
    def test_format_response_with_suggested_actions(self, sample_classified_request, sample_processor_response):
        """Test formatting with suggested actions."""
        from backend.ai.companion.core.response_formatter import ResponseFormatter
        
        formatter = ResponseFormatter()
        
        # Format the response with suggested actions
        suggested_actions = ["Look at the ticket machine", "Ask the station attendant"]
        
        formatted_response = formatter.format_response(
            processor_response=sample_processor_response,
            classified_request=sample_classified_request,
            suggested_actions=suggested_actions
        )
        
        # Check that the response contains the suggested actions
        for action in suggested_actions:
            assert action in formatted_response 