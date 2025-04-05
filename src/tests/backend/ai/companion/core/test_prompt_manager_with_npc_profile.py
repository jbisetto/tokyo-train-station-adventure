"""
Tests for PromptManager integration with NPC profiles.

These tests verify that the PromptManager can use NPC profiles
to customize prompts based on the NPC's personality and characteristics.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.ai.companion.core.models import ClassifiedRequest, IntentCategory, ComplexityLevel, ProcessingTier
from src.ai.companion.core.prompt_manager import PromptManager
from src.ai.companion.core.npc.profile import NPCProfile, NPCProfileRegistry


class TestPromptManagerWithNPCProfile:
    """Test the PromptManager's integration with NPC profiles."""
    
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
    def prompt_manager(self, profile_registry) -> PromptManager:
        """Create a PromptManager with a profile registry."""
        return PromptManager(profile_registry=profile_registry)
    
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
    
    def test_create_prompt_with_profile(self, prompt_manager, sample_request_with_profile):
        """Test creating a prompt with a specific NPC profile."""
        # Create a prompt for the request with a profile
        prompt = prompt_manager.create_prompt(sample_request_with_profile)
        
        # The prompt should include elements from the station attendant profile
        assert "Tanaka" in prompt
        assert "Station Attendant" in prompt
        assert "professional" in prompt
        assert "tickets" in prompt
    
    def test_create_prompt_with_default_profile(self, prompt_manager, sample_request_without_profile):
        """Test creating a prompt with the default NPC profile."""
        # Create a prompt for the request without a profile
        prompt = prompt_manager.create_prompt(sample_request_without_profile)
        
        # The prompt should include elements from the companion dog profile
        assert "Hachi" in prompt
        assert "Companion Dog" in prompt
        assert "enthusiastic" in prompt
        assert "japanese_language" in prompt
    
    def test_profile_integration_with_tier_specific_prompts(self, prompt_manager, sample_request_with_profile):
        """Test that profile information is integrated into tier-specific prompts."""
        # Configure prompt manager with tier-specific settings
        prompt_manager.tier_specific_config = {
            "additional_instructions": "Be concise in your responses."
        }
        
        # Create a prompt with tier-specific configuration
        prompt = prompt_manager.create_prompt(sample_request_with_profile)
        
        # The prompt should include both profile elements and tier-specific instructions
        assert "Tanaka" in prompt
        assert "Station Attendant" in prompt
        assert "Be concise" in prompt 