"""
Tests for the PersonalityEngine class.
"""

import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch

from src.ai.companion.core.models import ClassifiedRequest, CompanionResponse, IntentCategory
from src.ai.companion.personality.engine import PersonalityEngine
from src.ai.companion.personality.config import PersonalityConfig


class TestPersonalityEngine:
    """Tests for the PersonalityEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create a PersonalityEngine instance for testing."""
        return PersonalityEngine()
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample ClassifiedRequest for testing."""
        request = MagicMock(spec=ClassifiedRequest)
        request.request_id = "test-request-id"
        request.player_input = "What does 'sumimasen' mean?"
        request.intent = IntentCategory.VOCABULARY_HELP
        request.extracted_entities = {"word": "sumimasen", "meaning": "excuse me"}
        return request
    
    @pytest.fixture
    def sample_response(self):
        """Create a sample CompanionResponse for testing."""
        response = MagicMock(spec=CompanionResponse)
        response.response_text = "Sumimasen means 'excuse me' or 'I'm sorry' in Japanese."
        response.suggested_emotion = None
        response.add_learning_cues = False
        response.suggested_actions = []
        return response
    
    def test_initialization(self, engine):
        """Test that the PersonalityEngine initializes correctly."""
        assert engine is not None
        assert hasattr(engine, 'config')
        assert hasattr(engine, 'player_preferences')
        assert engine.interaction_count == 0
    
    def test_get_active_profile(self, engine):
        """Test getting the active personality profile."""
        profile = engine.get_active_profile()
        assert profile is not None
        assert hasattr(profile, 'get_trait_value')
    
    def test_set_active_profile(self, engine):
        """Test setting the active personality profile."""
        # The default profile should already be active
        default_profile_name = engine.get_active_profile().name
        
        # Create a new profile
        engine.create_profile("Test Profile", {
            "friendliness": 0.5,
            "enthusiasm": 0.5,
            "helpfulness": 0.5
        })
        
        # Set it as active
        result = engine.set_active_profile("Test Profile")
        assert result is True
        
        # Check that it's now the active profile
        assert engine.get_active_profile().name == "Test Profile"
        
        # Set it back to the default
        engine.set_active_profile(default_profile_name)
    
    def test_create_profile(self, engine):
        """Test creating a new personality profile."""
        # Create a new profile
        result = engine.create_profile("Test Profile 2", {
            "friendliness": 0.3,
            "enthusiasm": 0.4,
            "helpfulness": 0.5
        })
        
        assert result is True
        
        # Check that it's in the available profiles
        profiles = engine.get_available_profiles()
        assert "Test Profile 2" in profiles
        
        # Try to create a profile with the same name
        result = engine.create_profile("Test Profile 2", {
            "friendliness": 0.6,
            "enthusiasm": 0.7,
            "helpfulness": 0.8
        })
        
        assert result is False  # Should fail because the profile already exists
    
    def test_save_and_load_configuration(self, engine):
        """Test saving and loading the personality configuration."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp_path = temp.name
        
        try:
            # Create a profile
            engine.create_profile("Save Test Profile", {
                "friendliness": 0.1,
                "enthusiasm": 0.2,
                "helpfulness": 0.3
            })
            
            # Save the configuration
            result = engine.save_configuration(temp_path)
            assert result is True
            
            # Create a new engine and load the configuration
            new_engine = PersonalityEngine(config_path=temp_path)
            
            # Check that the profile was loaded
            profiles = new_engine.get_available_profiles()
            assert "Save Test Profile" in profiles
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_process_player_feedback(self, engine):
        """Test processing player feedback."""
        # Reset preferences to default
        engine.player_preferences["formality_preference"] = 0.5
        engine.player_preferences["detail_preference"] = 0.5
        
        # Process some positive feedback with clear formality and detail cues
        engine.process_player_feedback(
            "test-request-id",
            "I really liked how formal and detailed your response was!",
            5
        )
        
        # Check that the interaction was counted
        assert engine.interaction_count == 1
        assert engine.positive_interactions == 1
        
        # Check that the preferences were adjusted
        assert engine.player_preferences["formality_preference"] > 0.5
        assert engine.player_preferences["detail_preference"] > 0.5
        
        # Store the current values
        formality_after_positive = engine.player_preferences["formality_preference"]
        detail_after_positive = engine.player_preferences["detail_preference"]
        
        # Process some negative feedback with clear casual and brief cues
        engine.process_player_feedback(
            "test-request-id-2",
            "I prefer casual and brief responses.",
            2
        )
        
        # Check that the interaction was counted
        assert engine.interaction_count == 2
        assert engine.negative_interactions == 1
        
        # Check that the preferences were adjusted in the right direction
        assert engine.player_preferences["formality_preference"] < formality_after_positive
        assert engine.player_preferences["detail_preference"] < detail_after_positive
    
    def test_adapt_to_player(self, engine):
        """Test adapting to player preferences."""
        # Set up some preferences
        engine.player_preferences["formality_preference"] = 0.8
        engine.player_preferences["humor_preference"] = 0.2
        
        # Add some interactions
        engine.interaction_count = 10
        engine.positive_interactions = 8
        
        # Adapt
        result = engine.adapt_to_player(frequency=10)
        assert result is True
        
        # Check that the active profile was adapted
        profile = engine.get_active_profile()
        
        # Formality should have increased
        assert profile.get_trait_value("formality") > 0.3
        
        # Playfulness should have decreased
        assert profile.get_trait_value("playfulness") < 0.6
    
    def test_analyze_request(self, engine, sample_request):
        """Test analyzing a request for personality cues."""
        # Analyze a formal request
        sample_request.player_input = "Could you please explain what 'sumimasen' means in detail?"
        analysis = engine.analyze_request(sample_request)
        
        assert "formality_cue" in analysis
        assert analysis["formality_cue"] > 0.5  # Should detect formal cues
        assert analysis["detail_preference"] > 0.5  # Should detect detail preference
        
        # Analyze a casual request
        sample_request.player_input = "Hey, what's 'sumimasen' mean? Keep it brief."
        analysis = engine.analyze_request(sample_request)
        
        assert "formality_cue" in analysis
        assert analysis["formality_cue"] < 0.5  # Should detect casual cues
        assert analysis["detail_preference"] < 0.5  # Should detect concise preference
    
    def test_enhance_response(self, engine, sample_request, sample_response):
        """Test enhancing a response with personality."""
        # Analyze the request
        analysis = engine.analyze_request(sample_request)
        
        # Enhance the response
        enhanced = engine.enhance_response(sample_response, analysis)
        
        # Check that the response was enhanced
        assert enhanced is not None
        
        # Test with a formal analysis
        formal_analysis = {
            "formality_cue": 0.9,
            "detail_preference": 0.8,
            "topic": IntentCategory.VOCABULARY_HELP,
            "entities": {"word": "sumimasen"}
        }
        
        # Create a fresh response object for this test
        formal_response = MagicMock(spec=CompanionResponse)
        formal_response.response_text = "Sumimasen means 'excuse me' or 'I'm sorry' in Japanese."
        formal_response.suggested_emotion = None
        formal_response.add_learning_cues = False
        formal_response.suggested_actions = []
        
        # Mock random.choice to always return "neutral" for this test
        with patch('random.choice', return_value="neutral"):
            enhanced = engine.enhance_response(formal_response, formal_analysis)
            assert enhanced.suggested_emotion == "neutral"  # Formal responses should be neutral
            assert enhanced.add_learning_cues is True  # Detailed responses should have learning cues
        
        # Test with a casual analysis
        casual_analysis = {
            "formality_cue": 0.1,
            "detail_preference": 0.2,
            "topic": IntentCategory.VOCABULARY_HELP,
            "entities": {"word": "sumimasen"}
        }
        
        # Create a fresh response object for this test
        casual_response = MagicMock(spec=CompanionResponse)
        casual_response.response_text = "Sumimasen means 'excuse me' or 'I'm sorry' in Japanese."
        casual_response.suggested_emotion = None
        casual_response.add_learning_cues = False
        casual_response.suggested_actions = []
        
        # Mock random.choice to always return "happy" for this test
        with patch('random.choice', return_value="happy"):
            enhanced = engine.enhance_response(casual_response, casual_analysis)
            assert enhanced.suggested_emotion == "happy"  # Casual responses should be more emotional
            assert enhanced.add_learning_cues is False  # Brief responses should not have learning cues
    
    def test_generate_suggested_actions(self, engine):
        """Test generating suggested actions based on a topic."""
        # Test vocabulary help
        actions = engine._generate_suggested_actions("VOCABULARY_HELP")
        assert len(actions) > 0
        assert any("word" in action.lower() for action in actions)
        
        # Test grammar explanation
        actions = engine._generate_suggested_actions("GRAMMAR_EXPLANATION")
        assert len(actions) > 0
        assert any("grammar" in action.lower() for action in actions)
        
        # Test direction guidance
        actions = engine._generate_suggested_actions("DIRECTION_GUIDANCE")
        assert len(actions) > 0
        assert any("station" in action.lower() for action in actions)
        
        # Test translation confirmation
        actions = engine._generate_suggested_actions("TRANSLATION_CONFIRMATION")
        assert len(actions) > 0
        assert any("phrase" in action.lower() for action in actions)
        
        # Test unknown topic
        actions = engine._generate_suggested_actions("UNKNOWN")
        assert len(actions) > 0  # Should still generate generic actions 