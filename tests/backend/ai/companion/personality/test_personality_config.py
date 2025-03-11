"""
Tests for the personality configuration system.

This module contains tests for the personality configuration system, which is responsible
for defining and managing the companion's personality traits and behaviors.
"""

import pytest
from unittest.mock import patch, MagicMock
import json
import os
from typing import Dict, Any

# Import the module we're testing
# These imports will be implemented later
from backend.ai.companion.personality.config import (
    PersonalityConfig,
    PersonalityTrait,
    PersonalityProfile,
    DEFAULT_PERSONALITY_PROFILE
)


@pytest.fixture
def sample_personality_profile() -> Dict[str, Any]:
    """Create a sample personality profile for testing."""
    return {
        "name": "Friendly Helper",
        "description": "A friendly and helpful companion focused on assisting with language learning.",
        "traits": {
            "friendliness": 0.8,
            "enthusiasm": 0.7,
            "helpfulness": 0.9,
            "playfulness": 0.6,
            "formality": 0.3,
            "patience": 0.8,
            "curiosity": 0.5
        },
        "voice_style": "warm and encouraging",
        "language_style": {
            "greeting_style": "warm",
            "explanation_style": "clear and simple",
            "encouragement_style": "supportive"
        },
        "behavioral_tendencies": {
            "asks_follow_up_questions": 0.7,
            "provides_examples": 0.8,
            "uses_humor": 0.6,
            "shows_empathy": 0.8
        },
        "adaptation_settings": {
            "adapt_to_player_language_level": True,
            "adapt_to_player_progress": True,
            "adapt_to_player_mood": True,
            "adaptation_rate": 0.3
        }
    }


@pytest.fixture
def sample_personality_config(sample_personality_profile):
    """Create a sample personality configuration for testing."""
    config = PersonalityConfig()
    config.add_profile("default", sample_personality_profile)
    return config


class TestPersonalityTrait:
    """Tests for the PersonalityTrait class."""
    
    def test_trait_initialization(self):
        """Test that a personality trait can be initialized with valid values."""
        trait = PersonalityTrait("friendliness", 0.8, 0.0, 1.0)
        assert trait.name == "friendliness"
        assert trait.value == 0.8
        assert trait.min_value == 0.0
        assert trait.max_value == 1.0
    
    def test_trait_value_clamping(self):
        """Test that trait values are clamped to the specified range."""
        trait = PersonalityTrait("enthusiasm", 1.5, 0.0, 1.0)
        assert trait.value == 1.0
        
        trait.value = -0.5
        assert trait.value == 0.0
    
    def test_trait_serialization(self):
        """Test that traits can be serialized to and from dictionaries."""
        trait = PersonalityTrait("helpfulness", 0.9, 0.0, 1.0)
        trait_dict = trait.to_dict()
        
        assert trait_dict["name"] == "helpfulness"
        assert trait_dict["value"] == 0.9
        assert trait_dict["min_value"] == 0.0
        assert trait_dict["max_value"] == 1.0
        
        new_trait = PersonalityTrait.from_dict(trait_dict)
        assert new_trait.name == trait.name
        assert new_trait.value == trait.value
        assert new_trait.min_value == trait.min_value
        assert new_trait.max_value == trait.max_value


class TestPersonalityProfile:
    """Tests for the PersonalityProfile class."""
    
    def test_profile_initialization(self, sample_personality_profile):
        """Test that a personality profile can be initialized with valid values."""
        profile = PersonalityProfile.from_dict(sample_personality_profile)
        
        assert profile.name == "Friendly Helper"
        assert profile.description == "A friendly and helpful companion focused on assisting with language learning."
        assert len(profile.traits) == 7
        assert profile.traits["friendliness"].value == 0.8
        assert profile.voice_style == "warm and encouraging"
        assert profile.language_style["greeting_style"] == "warm"
        assert profile.behavioral_tendencies["asks_follow_up_questions"] == 0.7
        assert profile.adaptation_settings["adapt_to_player_language_level"] is True
    
    def test_profile_serialization(self, sample_personality_profile):
        """Test that profiles can be serialized to and from dictionaries."""
        profile = PersonalityProfile.from_dict(sample_personality_profile)
        profile_dict = profile.to_dict()
        
        assert profile_dict["name"] == "Friendly Helper"
        assert profile_dict["traits"]["friendliness"] == 0.8
        assert profile_dict["voice_style"] == "warm and encouraging"
        
        new_profile = PersonalityProfile.from_dict(profile_dict)
        assert new_profile.name == profile.name
        assert new_profile.traits["friendliness"].value == profile.traits["friendliness"].value
    
    def test_profile_trait_access(self, sample_personality_profile):
        """Test that traits can be accessed and modified."""
        profile = PersonalityProfile.from_dict(sample_personality_profile)
        
        assert profile.get_trait_value("friendliness") == 0.8
        
        profile.set_trait_value("friendliness", 0.9)
        assert profile.get_trait_value("friendliness") == 0.9
    
    def test_profile_validation(self):
        """Test that profiles are validated during initialization."""
        invalid_profile = {
            "name": "Invalid Profile",
            "traits": {
                "friendliness": 2.0,  # Invalid value
                "enthusiasm": -0.5    # Invalid value
            }
        }
        
        profile = PersonalityProfile.from_dict(invalid_profile)
        
        # Values should be clamped to valid range
        assert profile.get_trait_value("friendliness") == 1.0
        assert profile.get_trait_value("enthusiasm") == 0.0


class TestPersonalityConfig:
    """Tests for the PersonalityConfig class."""
    
    def test_config_initialization(self):
        """Test that a personality configuration can be initialized."""
        config = PersonalityConfig()
        assert config.get_active_profile_name() == "default"
        assert isinstance(config.get_active_profile(), PersonalityProfile)
    
    def test_add_profile(self, sample_personality_profile):
        """Test that profiles can be added to the configuration."""
        config = PersonalityConfig()
        config.add_profile("test_profile", sample_personality_profile)
        
        assert "test_profile" in config.get_available_profiles()
        assert config.get_profile("test_profile").name == "Friendly Helper"
    
    def test_switch_profile(self, sample_personality_profile):
        """Test that the active profile can be switched."""
        config = PersonalityConfig()
        config.add_profile("test_profile", sample_personality_profile)
        config.set_active_profile("test_profile")
        
        assert config.get_active_profile_name() == "test_profile"
        assert config.get_active_profile().name == "Friendly Helper"
    
    def test_save_and_load_profiles(self, sample_personality_profile, tmp_path):
        """Test that profiles can be saved to and loaded from files."""
        config_file = tmp_path / "personality_config.json"
        
        config = PersonalityConfig()
        config.add_profile("test_profile", sample_personality_profile)
        config.save_to_file(str(config_file))
        
        new_config = PersonalityConfig()
        new_config.load_from_file(str(config_file))
        
        assert "test_profile" in new_config.get_available_profiles()
        assert new_config.get_profile("test_profile").name == "Friendly Helper"
    
    def test_get_trait_value(self, sample_personality_config):
        """Test that trait values can be retrieved from the active profile."""
        assert sample_personality_config.get_trait_value("friendliness") == 0.8
        assert sample_personality_config.get_trait_value("enthusiasm") == 0.7
    
    def test_set_trait_value(self, sample_personality_config):
        """Test that trait values can be set in the active profile."""
        sample_personality_config.set_trait_value("friendliness", 0.9)
        assert sample_personality_config.get_trait_value("friendliness") == 0.9
    
    def test_default_profile(self):
        """Test that the default profile is created correctly."""
        config = PersonalityConfig()
        default_profile = config.get_profile("default")
        
        assert default_profile is not None
        assert default_profile.name == DEFAULT_PERSONALITY_PROFILE["name"]
        assert default_profile.get_trait_value("friendliness") == DEFAULT_PERSONALITY_PROFILE["traits"]["friendliness"] 