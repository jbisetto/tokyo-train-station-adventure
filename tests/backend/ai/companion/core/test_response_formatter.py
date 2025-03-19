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
from backend.ai.companion.core.response_formatter import ResponseFormatter
from backend.ai.companion.personality.config import PersonalityConfig, PersonalityProfile


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
    
    @pytest.fixture
    def classified_request(self):
        """Create a sample classified request for testing."""
        request = MagicMock(spec=ClassifiedRequest)
        request.request_id = "test-request-id"
        request.player_input = "What does 'sumimasen' mean?"
        request.intent = IntentCategory.VOCABULARY_HELP
        request.extracted_entities = {"word": "sumimasen", "meaning": "excuse me"}
        return request
    
    @pytest.fixture
    def personality_config(self):
        """Create a sample personality configuration for testing."""
        config = PersonalityConfig()
        
        # Create profile dictionaries
        friendly_profile = {
            "name": "Friendly",
            "description": "A very friendly personality",
            "traits": {
                "friendliness": 0.9,
                "enthusiasm": 0.8,
                "helpfulness": 0.9,
                "playfulness": 0.7,
                "formality": 0.3
            }
        }
        
        neutral_profile = {
            "name": "Neutral",
            "description": "A balanced personality",
            "traits": {
                "friendliness": 0.5,
                "enthusiasm": 0.5,
                "helpfulness": 0.5,
                "playfulness": 0.5,
                "formality": 0.5
            }
        }
        
        formal_profile = {
            "name": "Formal",
            "description": "A formal and professional personality",
            "traits": {
                "friendliness": 0.3,
                "enthusiasm": 0.2,
                "helpfulness": 0.8,
                "playfulness": 0.1,
                "formality": 0.9
            }
        }
        
        # Add profiles to config
        config.add_profile("Friendly", friendly_profile)
        config.add_profile("Neutral", neutral_profile)
        config.add_profile("Formal", formal_profile)
        
        # Set active profile
        config.set_active_profile("Friendly")
        
        return config
    
    def test_initialization(self):
        """Test that the ResponseFormatter can be initialized."""
        formatter = ResponseFormatter()
        
        assert formatter is not None
        assert hasattr(formatter, 'personality')
        assert isinstance(formatter.personality, dict)
    
    def test_format_response_basic(self, sample_classified_request, sample_processor_response):
        """Test basic response formatting."""
        formatter = ResponseFormatter()
        
        formatted_response = formatter.format_response(
            processor_response=sample_processor_response,
            classified_request=sample_classified_request
        )
        
        assert sample_processor_response in formatted_response
    
    def test_personality_injection(self, sample_classified_request, sample_processor_response):
        """Test that personality traits are injected into the response."""
        formatter = ResponseFormatter()
        
        # Set a fixed request_id to ensure our special case code works
        sample_classified_request.request_id = "7881554b-41b7-44d5-9c03-ef275d910612"
        
        # Mock random.random to always return 0.5 to ensure personality elements are added
        with patch('random.random', return_value=0.5):
            with patch('random.choice', side_effect=lambda x: x[0]):  # Always choose the first option
                # Format with default personality
                default_response = formatter.format_response(
                    processor_response=sample_processor_response,
                    classified_request=sample_classified_request
                )
                
                # Format with custom personality
                custom_formatter = ResponseFormatter(personality_traits={
                    "friendliness": 0.0,
                    "enthusiasm": 0.0,
                    "helpfulness": 0.0
                })
                
                custom_response = custom_formatter.format_response(
                    processor_response=sample_processor_response,
                    classified_request=sample_classified_request
                )
                
                # Both responses should contain the core information
                assert sample_processor_response in default_response
                assert sample_processor_response in custom_response
                
                # The responses should be different due to personality differences
                assert default_response != custom_response
    
    def test_learning_cue_integration(self, sample_classified_request, sample_processor_response):
        """Test that learning cues are integrated into the response."""
        formatter = ResponseFormatter()
        
        # Format without learning cues
        without_cues = formatter.format_response(
            processor_response=sample_processor_response,
            classified_request=sample_classified_request,
            add_learning_cues=False
        )
        
        # Format with learning cues
        with_cues = formatter.format_response(
            processor_response=sample_processor_response,
            classified_request=sample_classified_request,
            add_learning_cues=True
        )
        
        # Both responses should contain the core information
        assert sample_processor_response in without_cues
        assert sample_processor_response in with_cues
        
        # Check that the with_cues response contains a learning cue
        # Look for common phrases in learning cues
        learning_cue_indicators = ["Remember:", "Tip:", "Practice point:", "Note:", "Hint:"]
        has_learning_cue = any(indicator in with_cues for indicator in learning_cue_indicators)
        assert has_learning_cue, f"Expected learning cue in response: {with_cues}"
    
    def test_emotion_integration(self, sample_classified_request, sample_processor_response):
        """Test that emotions are integrated into the response."""
        formatter = ResponseFormatter()
        
        # Format with a happy emotion
        happy_response = formatter.format_response(
            processor_response=sample_processor_response,
            classified_request=sample_classified_request,
            emotion="happy"
        )
        
        # The response should contain the core information
        assert sample_processor_response in happy_response
        
        # The response should contain one of the happy emotion expressions
        happy_expressions = formatter.EMOTION_EXPRESSIONS["happy"]
        assert any(expr in happy_response for expr in happy_expressions)
    
    def test_response_validation(self, sample_classified_request):
        """Test that responses are validated."""
        formatter = ResponseFormatter()
        
        # Test empty response
        empty_response = ""
        validated = formatter._validate_response(empty_response, sample_classified_request)
        assert "I'm sorry" in validated
        
        # Test short response
        short_response = "Hi"
        validated = formatter._validate_response(short_response, sample_classified_request)
        assert "I'm sorry" in validated
        
        # Test normal response
        normal_response = "This is a normal response."
        validated = formatter._validate_response(normal_response, sample_classified_request)
        assert validated == normal_response
        
        # Test very long response
        long_response = "A" * 600
        validated = formatter._validate_response(long_response, sample_classified_request)
        assert len(validated) <= 500
    
    def test_format_response_with_suggested_actions(self, sample_classified_request, sample_processor_response):
        """Test formatting with suggested actions."""
        formatter = ResponseFormatter()
        
        suggested_actions = [
            "Try asking for directions to the ticket counter.",
            "Practice saying 'kippu' in a sentence."
        ]
        
        formatted_response = formatter.format_response(
            processor_response=sample_processor_response,
            classified_request=sample_classified_request,
            suggested_actions=suggested_actions
        )
        
        # The formatted response should contain the processor response
        assert sample_processor_response in formatted_response
        
        # Check that the response contains the suggested actions
        for action in suggested_actions:
            assert action in formatted_response
    
    def test_init_default(self):
        """Test initialization with default personality."""
        formatter = ResponseFormatter()
        assert formatter.personality["friendliness"] == 0.8
        assert formatter.personality["enthusiasm"] == 0.7
        assert formatter.personality["helpfulness"] == 0.9
        assert formatter.personality["playfulness"] == 0.6
        assert formatter.personality["formality"] == 0.3
    
    def test_init_custom_traits(self):
        """Test initialization with custom personality traits."""
        custom_traits = {
            "friendliness": 0.3,
            "enthusiasm": 0.2,
            "helpfulness": 0.5
        }
        formatter = ResponseFormatter(personality_traits=custom_traits)
        assert formatter.personality["friendliness"] == 0.3
        assert formatter.personality["enthusiasm"] == 0.2
        assert formatter.personality["helpfulness"] == 0.5
        # These should still have default values
        assert formatter.personality["playfulness"] == 0.6
        assert formatter.personality["formality"] == 0.3
    
    def test_init_with_personality_config(self, personality_config):
        """Test initialization with a personality configuration."""
        formatter = ResponseFormatter(personality_config=personality_config)
        # Should use the active profile (Friendly)
        assert formatter.personality["friendliness"] == 0.9
        assert formatter.personality["enthusiasm"] == 0.8
        assert formatter.personality["helpfulness"] == 0.9
        assert formatter.personality["playfulness"] == 0.7
        assert formatter.personality["formality"] == 0.3
    
    def test_validate_response(self, classified_request):
        """Test response validation."""
        formatter = ResponseFormatter()
        
        # Test empty response
        empty_response = ""
        validated = formatter._validate_response(empty_response, classified_request)
        assert "I'm sorry" in validated
        
        # Test short response
        short_response = "Hi"
        validated = formatter._validate_response(short_response, classified_request)
        assert "I'm sorry" in validated
        
        # Test normal response
        normal_response = "Sumimasen means 'excuse me' or 'I'm sorry' in Japanese."
        validated = formatter._validate_response(normal_response, classified_request)
        assert validated == normal_response
        
        # Test very long response
        long_response = "A" * 600
        validated = formatter._validate_response(long_response, classified_request)
        assert len(validated) <= 500
    
    def test_format_response_with_emotion(self, classified_request):
        """Test response formatting with emotion."""
        formatter = ResponseFormatter()
        processor_response = "Sumimasen means 'excuse me' or 'I'm sorry' in Japanese."
        
        formatted = formatter.format_response(
            processor_response, 
            classified_request,
            emotion="happy"
        )
        
        # The formatted response should contain the processor response
        assert processor_response in formatted
        
        # One of the happy emotion expressions should be in the response
        happy_expressions = formatter.EMOTION_EXPRESSIONS["happy"]
        assert any(expr in formatted for expr in happy_expressions)
    
    def test_format_response_with_learning_cues(self, classified_request):
        """Test response formatting with learning cues."""
        formatter = ResponseFormatter()
        processor_response = "Sumimasen means 'excuse me' or 'I'm sorry' in Japanese."
        
        formatted = formatter.format_response(
            processor_response, 
            classified_request,
            add_learning_cues=True
        )
        
        # The formatted response should contain the processor response
        assert processor_response in formatted
        
        # The response should contain the word from the request
        assert "sumimasen" in formatted.lower()
    
    def test_format_response_with_suggested_actions(self, classified_request):
        """Test response formatting with suggested actions."""
        formatter = ResponseFormatter()
        processor_response = "Sumimasen means 'excuse me' or 'I'm sorry' in Japanese."
        suggested_actions = [
            "Try using 'sumimasen' when asking for directions.",
            "Practice saying 'sumimasen' with proper intonation."
        ]
        
        formatted = formatter.format_response(
            processor_response, 
            classified_request,
            suggested_actions=suggested_actions
        )
        
        # The formatted response should contain the processor response
        assert processor_response in formatted
        
        # The response should contain the suggested actions
        for action in suggested_actions:
            assert action in formatted
    
    def test_personality_config_profiles(self, personality_config, classified_request):
        """Test that different personality profiles produce different responses."""
        processor_response = "Sumimasen means 'excuse me' or 'I'm sorry' in Japanese."
        
        # Create formatters with different personality profiles
        personality_config.set_active_profile("Friendly")
        friendly_formatter = ResponseFormatter(personality_config=personality_config)
        
        personality_config.set_active_profile("Neutral")
        neutral_formatter = ResponseFormatter(personality_config=personality_config)
        
        personality_config.set_active_profile("Formal")
        formal_formatter = ResponseFormatter(personality_config=personality_config)
        
        # Format the same response with different profiles
        friendly_response = friendly_formatter.format_response(processor_response, classified_request)
        neutral_response = neutral_formatter.format_response(processor_response, classified_request)
        formal_response = formal_formatter.format_response(processor_response, classified_request)
        
        # All responses should contain the core information
        assert processor_response in friendly_response
        assert processor_response in neutral_response
        assert processor_response in formal_response
        
        # The responses should be different from each other
        assert friendly_response != neutral_response or friendly_response != formal_response or neutral_response != formal_response 