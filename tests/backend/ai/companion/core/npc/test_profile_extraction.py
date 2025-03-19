"""
Tests for extracting NPC profiles from existing components.

These tests verify the functionality of extracting a default companion profile 
from the existing ResponseFormatter which contains hardcoded personality traits
for Hachi the companion dog.
"""

import pytest
from typing import Dict, Any

from backend.ai.companion.core.response_formatter import ResponseFormatter
from backend.ai.companion.core.npc.profile import NPCProfile
from backend.ai.companion.core.npc.extraction import extract_companion_profile


class TestProfileExtraction:
    """Test extracting NPC profiles from existing components."""
    
    @pytest.fixture
    def response_formatter(self) -> ResponseFormatter:
        """Create a ResponseFormatter with default settings."""
        return ResponseFormatter()
    
    def test_extract_companion_profile(self, response_formatter):
        """Test extracting a companion profile from the ResponseFormatter."""
        # Extract the profile
        profile = extract_companion_profile(response_formatter)
        
        # Verify the profile was created correctly
        assert profile.profile_id == "companion_dog"
        assert profile.name == "Hachi"
        assert profile.role == "Companion Dog"
        
        # Verify personality traits were extracted
        assert profile.personality_traits["friendliness"] == response_formatter.DEFAULT_PERSONALITY["friendliness"]
        assert profile.personality_traits["enthusiasm"] == response_formatter.DEFAULT_PERSONALITY["enthusiasm"]
        
        # Verify emotion expressions were extracted
        assert "I wag my tail happily!" in profile.emotion_expressions.get("happy", [])
        assert "*excited barking*" in profile.emotion_expressions.get("excited", [])
        
        # Verify knowledge areas were included
        assert "japanese_language" in profile.knowledge_areas
        assert "tokyo_station" in profile.knowledge_areas
        
        # Verify backstory was created
        assert "magical talking shiba inu" in profile.backstory.lower()
    
    def test_convert_profile_to_json(self, response_formatter):
        """Test converting an extracted profile to JSON format."""
        # Extract the profile
        profile = extract_companion_profile(response_formatter)
        
        # Convert to dictionary
        profile_dict = profile.to_dict()
        
        # Verify the dictionary has the expected fields
        assert "profile_id" in profile_dict
        assert "name" in profile_dict
        assert "role" in profile_dict
        assert "personality_traits" in profile_dict
        assert "speech_patterns" in profile_dict
        assert "knowledge_areas" in profile_dict
        assert "backstory" in profile_dict
        assert "emotion_expressions" in profile_dict
        
        # Verify values
        assert profile_dict["name"] == "Hachi"
        assert profile_dict["profile_id"] == "companion_dog" 