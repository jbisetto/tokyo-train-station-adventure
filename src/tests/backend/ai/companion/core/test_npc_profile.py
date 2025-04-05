import json
import os
import tempfile
import pytest
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

from src.ai.companion.core.models import ClassifiedRequest, IntentCategory, ComplexityLevel, ProcessingTier, GameContext
from src.ai.companion.core.npc.profile import NPCProfile, NPCProfileRegistry


class TestNPCProfile:
    """Test the NPCProfile class and functionality."""
    
    @pytest.fixture
    def sample_profile_data(self) -> Dict[str, Any]:
        """Return sample profile data for testing."""
        return {
            "profile_id": "station_attendant",
            "name": "Tanaka",
            "role": "Station Attendant",
            "personality_traits": {
                "friendliness": 0.7,
                "enthusiasm": 0.5,
                "helpfulness": 0.9,
                "formality": 0.8,
                "playfulness": 0.2
            },
            "speech_patterns": {
                "common_phrases": [
                    "May I assist you?",
                    "Thank you for your patience.",
                    "Please follow me.",
                    "Let me help you with that."
                ],
                "formality_level": "polite",
                "speaking_style": "professional"
            },
            "knowledge_areas": ["tickets", "train_schedules", "station_layout"],
            "backstory": "Tanaka has worked at Tokyo Station for 15 years and knows every corner of the facility.",
            "visual_traits": {
                "uniform": "Blue station uniform with cap",
                "age": "mid-40s",
                "appearance": "Neat and professional"
            },
            "emotion_expressions": {
                "happy": [
                    "I'm pleased to assist you.",
                    "*gives a professional smile*",
                    "I'm glad I could help."
                ],
                "concerned": [
                    "*looks concerned*",
                    "I apologize for the inconvenience.",
                    "Let me see what I can do about this."
                ]
            }
        }
    
    @pytest.fixture
    def sample_hachi_profile_data(self) -> Dict[str, Any]:
        """Return sample Hachi profile data for testing."""
        return {
            "profile_id": "companion_dog",
            "name": "Hachi",
            "role": "Companion Dog",
            "personality_traits": {
                "friendliness": 0.9,
                "enthusiasm": 0.8,
                "helpfulness": 0.9,
                "formality": 0.3,
                "playfulness": 0.7
            },
            "speech_patterns": {
                "common_phrases": [
                    "Woof! I'm here to help!",
                    "Let me sniff out the answer for you!",
                    "I'm pawsitively sure about this!",
                    "You're doing great!"
                ],
                "formality_level": "casual",
                "speaking_style": "enthusiastic"
            },
            "knowledge_areas": ["japanese_language", "tokyo_station", "cultural_tips"],
            "backstory": "Hachi is a magical talking dog who loves helping travelers learn Japanese.",
            "visual_traits": {
                "breed": "Shiba Inu",
                "appearance": "Fluffy with a curly tail",
                "accessories": "Red bandana"
            },
            "emotion_expressions": {
                "happy": [
                    "I wag my tail happily!",
                    "*happy bark*",
                    "My tail wags with joy!"
                ],
                "excited": [
                    "I bounce around excitedly!",
                    "*excited barking*",
                    "*tail wagging intensifies*"
                ]
            }
        }
    
    @pytest.fixture
    def sample_profile(self, sample_profile_data) -> NPCProfile:
        """Create a sample NPCProfile for testing."""
        return NPCProfile.from_dict(sample_profile_data)
    
    @pytest.fixture
    def sample_request(self) -> ClassifiedRequest:
        """Create a sample classified request for testing."""
        return ClassifiedRequest(
            request_id="test-123",
            player_input="Where can I buy a ticket?",
            request_type="assistance",
            intent=IntentCategory.DIRECTION_GUIDANCE,
            complexity=ComplexityLevel.SIMPLE,
            processing_tier=ProcessingTier.TIER_2,
            game_context=None
        )
    
    def test_create_profile(self, sample_profile_data):
        """Test creating an NPCProfile from a dictionary."""
        profile = NPCProfile.from_dict(sample_profile_data)
        
        assert profile.profile_id == "station_attendant"
        assert profile.name == "Tanaka"
        assert profile.role == "Station Attendant"
        assert profile.personality_traits["friendliness"] == 0.7
        assert profile.speech_patterns["formality_level"] == "polite"
        assert "tickets" in profile.knowledge_areas
        assert "Blue station uniform" in profile.visual_traits["uniform"]
    
    def test_to_dict(self, sample_profile):
        """Test converting a profile back to a dictionary."""
        profile_dict = sample_profile.to_dict()
        
        assert profile_dict["profile_id"] == "station_attendant"
        assert profile_dict["name"] == "Tanaka"
        assert profile_dict["personality_traits"]["friendliness"] == 0.7
        assert "tickets" in profile_dict["knowledge_areas"]
    
    def test_get_system_prompt_additions(self, sample_profile):
        """Test getting profile-specific additions to system prompts."""
        prompt_additions = sample_profile.get_system_prompt_additions()
        
        assert sample_profile.name in prompt_additions
        assert sample_profile.role in prompt_additions
        assert "Tokyo Station for 15 years" in prompt_additions
        assert "professional" in prompt_additions
        assert "tickets" in prompt_additions
    
    def test_get_emotion_expression(self, sample_profile):
        """Test getting an emotion expression from the profile."""
        happy_expression = sample_profile.get_emotion_expression("happy")
        
        assert happy_expression in sample_profile.emotion_expressions["happy"]
        
        # Test fallback for unknown emotion
        unknown_expression = sample_profile.get_emotion_expression("confused")
        assert unknown_expression is not None
    
    def test_format_response(self, sample_profile, sample_request):
        """Test formatting a response using the profile."""
        response = "The ticket machines are located near the entrance."
        
        # Patch random.random to ensure consistent behavior
        with patch('random.random', return_value=0.6):  # This ensures emotion expression is added at the end
            formatted_response = sample_profile.format_response(response, sample_request, emotion="happy")
            
            assert response in formatted_response
            assert sample_profile.name in formatted_response
            # Should include an emotion expression
            assert any(expr in formatted_response for expr in sample_profile.emotion_expressions["happy"])
    
    def test_get_common_phrase(self, sample_profile):
        """Test getting a common phrase from the profile."""
        phrase = sample_profile.get_common_phrase()
        
        assert phrase in sample_profile.speech_patterns["common_phrases"]
    
    def test_has_knowledge_area(self, sample_profile):
        """Test checking if a profile has a specific knowledge area."""
        assert sample_profile.has_knowledge_area("tickets") is True
        assert sample_profile.has_knowledge_area("cooking") is False


class TestNPCProfileRegistry:
    """Test the NPCProfileRegistry class."""
    
    @pytest.fixture
    def sample_profile_data(self) -> Dict[str, Any]:
        """Return sample profile data for testing."""
        return {
            "profile_id": "station_attendant",
            "name": "Tanaka",
            "role": "Station Attendant",
            "personality_traits": {
                "friendliness": 0.7,
                "enthusiasm": 0.5,
                "helpfulness": 0.9,
                "formality": 0.8,
                "playfulness": 0.2
            },
            "speech_patterns": {
                "common_phrases": [
                    "May I assist you?",
                    "Thank you for your patience."
                ],
                "formality_level": "polite",
                "speaking_style": "professional"
            },
            "knowledge_areas": ["tickets", "train_schedules"],
            "backstory": "Tanaka has worked at Tokyo Station for 15 years."
        }
    
    @pytest.fixture
    def sample_hachi_profile_data(self) -> Dict[str, Any]:
        """Return sample Hachi profile data for testing."""
        return {
            "profile_id": "companion_dog",
            "name": "Hachi",
            "role": "Companion Dog",
            "personality_traits": {
                "friendliness": 0.9,
                "enthusiasm": 0.8,
                "helpfulness": 0.9,
                "formality": 0.3,
                "playfulness": 0.7
            },
            "speech_patterns": {
                "common_phrases": [
                    "Woof! I'm here to help!",
                    "Let me sniff out the answer for you!"
                ],
                "formality_level": "casual",
                "speaking_style": "enthusiastic"
            },
            "knowledge_areas": ["japanese_language", "tokyo_station"],
            "backstory": "Hachi is a magical talking dog who loves helping travelers learn Japanese."
        }
    
    @pytest.fixture
    def sample_profiles(self, sample_profile_data, sample_hachi_profile_data) -> List[Dict[str, Any]]:
        """Return sample profiles for testing."""
        return [sample_profile_data, sample_hachi_profile_data]
    
    @pytest.fixture
    def temp_profile_dir(self, sample_profiles) -> str:
        """Create a temporary directory with profile files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write sample profiles to the directory
            for profile_data in sample_profiles:
                filename = f"{profile_data['profile_id']}.json"
                with open(os.path.join(temp_dir, filename), "w") as f:
                    json.dump(profile_data, f)
            
            yield temp_dir
    
    def test_load_profiles_from_directory(self, temp_profile_dir):
        """Test loading profiles from a directory."""
        registry = NPCProfileRegistry()
        registry.load_profiles_from_directory(temp_profile_dir)
        
        assert len(registry.profiles) == 2
        assert "station_attendant" in registry.profiles
        assert "companion_dog" in registry.profiles
        
        # Check that profiles are loaded correctly
        assert registry.profiles["station_attendant"].name == "Tanaka"
        assert registry.profiles["companion_dog"].name == "Hachi"
    
    def test_register_profile(self, sample_profile_data):
        """Test registering a profile in the registry."""
        registry = NPCProfileRegistry()
        profile = NPCProfile.from_dict(sample_profile_data)
        
        registry.register_profile(profile)
        
        assert "station_attendant" in registry.profiles
        assert registry.profiles["station_attendant"] is profile
    
    def test_get_profile(self, sample_profiles, temp_profile_dir):
        """Test getting a profile from the registry."""
        registry = NPCProfileRegistry()
        registry.load_profiles_from_directory(temp_profile_dir)
        
        # Get existing profile
        profile = registry.get_profile("station_attendant")
        assert profile.name == "Tanaka"
        
        # Get default profile when requesting non-existent profile
        profile = registry.get_profile("non_existent")
        assert profile.name == "Hachi"  # Assuming companion_dog is default
        
        # Get default profile when no profile_id is provided
        profile = registry.get_profile()
        assert profile.name == "Hachi"
    
    def test_set_default_profile(self, sample_profiles, temp_profile_dir):
        """Test setting the default profile."""
        registry = NPCProfileRegistry()
        registry.load_profiles_from_directory(temp_profile_dir)
        
        # Set station_attendant as default
        registry.set_default_profile("station_attendant")
        
        # Get default profile
        profile = registry.get_profile()
        assert profile.name == "Tanaka" 