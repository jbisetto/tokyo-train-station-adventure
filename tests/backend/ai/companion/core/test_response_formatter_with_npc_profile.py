"""
Tests for ResponseFormatter integration with NPC profiles.

These tests verify that the ResponseFormatter can use NPC profiles to
format responses based on the NPC's personality and characteristics.
"""

import pytest
from unittest.mock import MagicMock

from backend.ai.companion.core.models import ClassifiedRequest, IntentCategory, ComplexityLevel, ProcessingTier
from backend.ai.companion.core.response_formatter import ResponseFormatter
from backend.ai.companion.core.npc.profile import NPCProfile, NPCProfileRegistry


class TestResponseFormatterWithNPCProfile:
    """Test the ResponseFormatter's integration with NPC profiles."""
    
    @pytest.fixture
    def station_attendant_profile(self) -> NPCProfile:
        """Return a sample station attendant profile for testing."""
        return NPCProfile(
            profile_id="station_attendant",
            name="Tanaka",
            role="Station Attendant",
            personality_traits={
                "friendliness": 0.7,
                "enthusiasm": 0.5,
                "helpfulness": 0.9,
                "formality": 0.8,
                "playfulness": 0.2
            },
            speech_patterns={
                "common_phrases": ["May I assist you?"],
                "formality_level": "polite",
                "speaking_style": "professional"
            },
            knowledge_areas=["tickets", "train_schedules", "station_layout"],
            backstory="Tanaka has worked at Tokyo Station for 15 years."
        )
    
    @pytest.fixture
    def companion_dog_profile(self) -> NPCProfile:
        """Return a sample companion dog profile for testing."""
        return NPCProfile(
            profile_id="companion_dog",
            name="Hachi",
            role="Companion Dog",
            personality_traits={
                "friendliness": 0.9,
                "enthusiasm": 0.8,
                "helpfulness": 0.9,
                "formality": 0.3,
                "playfulness": 0.7
            },
            speech_patterns={
                "common_phrases": ["Woof! I'm here to help!"],
                "formality_level": "casual",
                "speaking_style": "enthusiastic"
            },
            knowledge_areas=["japanese_language", "tokyo_station", "cultural_tips"],
            backstory="Hachi is a magical talking dog who loves helping travelers learn Japanese."
        )
    
    @pytest.fixture
    def profile_registry(self, station_attendant_profile, companion_dog_profile) -> NPCProfileRegistry:
        """Create a profile registry with test profiles."""
        registry = NPCProfileRegistry(default_profile_id="companion_dog")
        registry.register_profile(station_attendant_profile)
        registry.register_profile(companion_dog_profile)
        return registry
    
    @pytest.fixture
    def response_formatter(self, profile_registry) -> ResponseFormatter:
        """Create a ResponseFormatter with a profile registry."""
        return ResponseFormatter(profile_registry=profile_registry)
    
    @pytest.fixture
    def sample_request_with_profile(self) -> ClassifiedRequest:
        """Create a sample classified request with a profile ID."""
        return ClassifiedRequest(
            request_id="test-123",
            player_input="Where can I buy a ticket?",
            request_type="assistance",
            intent=IntentCategory.DIRECTION_GUIDANCE,
            complexity=ComplexityLevel.SIMPLE,
            processing_tier=ProcessingTier.TIER_2,
            profile_id="station_attendant"
        )
    
    @pytest.fixture
    def sample_request_without_profile(self) -> ClassifiedRequest:
        """Create a sample classified request without a profile ID."""
        return ClassifiedRequest(
            request_id="test-456",
            player_input="How do I say 'ticket' in Japanese?",
            request_type="vocabulary",
            intent=IntentCategory.VOCABULARY_HELP,
            complexity=ComplexityLevel.SIMPLE,
            processing_tier=ProcessingTier.TIER_2
        )
    
    def test_format_response_with_profile(self, response_formatter, sample_request_with_profile):
        """Test formatting a response with a specific NPC profile."""
        # Format a response with a specific profile
        response = "The ticket machines are located near the entrance."
        formatted_response = response_formatter.format_response(response, sample_request_with_profile, "happy")
        
        # The response should include elements from the station attendant profile
        assert "Tanaka" in formatted_response
        assert response in formatted_response
        assert formatted_response.startswith("Tanaka:")
    
    def test_format_response_with_default_profile(self, response_formatter, sample_request_without_profile, companion_dog_profile):
        """Test formatting a response with the default NPC profile."""
        # Format a response without a specific profile
        response = "'Kippu' means 'ticket' in Japanese."
        formatted_response = response_formatter.format_response(response, sample_request_without_profile, "happy")
        
        # The response should include elements from the companion dog profile
        assert formatted_response.startswith("Hachi:")
        assert response in formatted_response
    
    def test_format_response_with_no_profile_registry(self):
        """Test formatting a response without a profile registry."""
        # Create a formatter without a profile registry
        formatter = ResponseFormatter()
        
        # Create a request with a profile ID that doesn't exist
        request = ClassifiedRequest(
            request_id="test-789",
            player_input="Hello",
            request_type="greeting",
            intent=IntentCategory.GENERAL_HINT,
            complexity=ComplexityLevel.SIMPLE,
            processing_tier=ProcessingTier.TIER_1,
            profile_id="non_existent_profile"
        )
        
        # Format a response
        response = "Hello! How can I help you?"
        formatted_response = formatter.format_response(response, request, "neutral")
        
        # The response should be formatted with the default personality
        assert formatted_response.startswith("Hachi:")
        assert response in formatted_response