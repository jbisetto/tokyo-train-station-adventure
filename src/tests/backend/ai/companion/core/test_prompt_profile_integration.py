"""
Integration tests for the refactored prompt and profile system.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

from src.ai.companion.core.models import (
    ClassifiedRequest, 
    IntentCategory, 
    ComplexityLevel, 
    ProcessingTier,
    GameContext
)
from src.ai.companion.core.npc.profile_loader import ProfileLoader
from src.ai.companion.core.npc.profile import NPCProfile, NPCProfileRegistry
from src.ai.companion.core.prompt.prompt_template_loader import PromptTemplateLoader
from src.ai.companion.core.prompt_manager import PromptManager


class TestPromptProfileIntegration:
    """Integration tests for the prompt and profile system."""
    
    @pytest.fixture
    def profiles_dir(self):
        """Fixture for profiles directory path."""
        return os.path.join(os.getcwd(), "src/data/profiles")
    
    @pytest.fixture
    def templates_dir(self):
        """Fixture for templates directory path."""
        return os.path.join(os.getcwd(), "src/data/prompt_templates")
    
    @pytest.fixture
    def profile_loader(self, profiles_dir):
        """Fixture for profile loader."""
        return ProfileLoader(profiles_dir)
    
    @pytest.fixture
    def prompt_template_loader(self, templates_dir):
        """Fixture for prompt template loader."""
        return PromptTemplateLoader(templates_dir)
    
    @pytest.fixture
    def profile_registry(self, profiles_dir):
        """Fixture for profile registry."""
        registry = NPCProfileRegistry(default_profile_id="companion_dog", profiles_directory=profiles_dir)
        return registry
    
    @pytest.fixture
    def prompt_manager(self, profile_registry, templates_dir):
        """Fixture for prompt manager."""
        return PromptManager(
            profile_registry=profile_registry,
            prompt_templates_directory=templates_dir
        )
    
    @pytest.fixture
    def sample_request(self):
        """Fixture for a sample classified request."""
        return ClassifiedRequest(
            request_id="test_id",
            player_input="How do I say 'ticket' in Japanese?",
            request_type="language_help",
            intent=IntentCategory.VOCABULARY_HELP,
            complexity=ComplexityLevel.SIMPLE,
            processing_tier=ProcessingTier.TIER_2,
            profile_id="companion_dog",
            game_context=GameContext(
                player_location="Tokyo Station Central Hall",
                current_objective="Buy a ticket",
                language_proficiency={"japanese": 0.2}
            )
        )
    
    def test_profile_inheritance(self, profile_loader):
        """Test that profile inheritance works correctly."""
        # Get the Hachiko profile which extends base_language_instructor
        hachiko = profile_loader.get_profile("companion_dog")
        
        # Verify inheritance
        assert hachiko["profile_id"] == "companion_dog"
        assert hachiko["name"] == "Hachiko"
        
        # These should be inherited from base_language_instructor
        assert "JLPT N5 vocabulary" in hachiko["knowledge_areas"]
        assert "VOCABULARY_HELP" in hachiko["response_format"]
    
    def test_profile_registry_loads_profiles(self, profile_registry):
        """Test that profile registry loads profiles correctly."""
        # Check if profiles were loaded
        assert "companion_dog" in profile_registry.profiles
        assert "station_attendant" in profile_registry.profiles
        
        # Verify that profiles were converted to NPCProfile objects
        hachiko = profile_registry.get_profile("companion_dog")
        assert isinstance(hachiko, NPCProfile)
        assert hachiko.name == "Hachiko"
    
    def test_prompt_template_loader_with_intents(self, prompt_template_loader):
        """Test that prompt template loader returns correct prompt for intent."""
        # Set the active template
        prompt_template_loader.set_active_template("language_instructor_prompts")
        
        # Get prompt for vocabulary help
        prompt = prompt_template_loader.get_intent_prompt(IntentCategory.VOCABULARY_HELP)
        
        # Verify prompt contains expected content
        assert "VOCABULARY RESPONSE FORMAT" in prompt
        assert "Explain the meaning of the word clearly" in prompt
    
    def test_prompt_manager_creates_prompt_with_profile(self, prompt_manager, sample_request):
        """Test that prompt manager creates a prompt with profile information."""
        # Create a prompt
        prompt = prompt_manager.create_prompt(sample_request)
        
        # Verify prompt contains profile context
        assert "Hachiko" in prompt
        assert "Companion Dog" in prompt
        
        # Verify prompt contains intent-specific format
        assert "VOCABULARY RESPONSE FORMAT" in prompt
        
        # Verify prompt contains response format from profile
        assert "RESPONSE FORMAT GUIDELINES" in prompt
    
    def test_prompt_manager_with_non_instructor_profile(self, prompt_manager):
        """Test that prompt manager creates different prompts for different profiles."""
        # Create a request with station attendant profile
        request = ClassifiedRequest(
            request_id="test_id2",
            player_input="How do I get to the Yamanote Line?",
            request_type="navigation",
            intent=IntentCategory.DIRECTION_GUIDANCE,
            complexity=ComplexityLevel.SIMPLE,
            processing_tier=ProcessingTier.TIER_2,
            profile_id="station_attendant"
        )
        
        # Create a prompt
        prompt = prompt_manager.create_prompt(request)
        
        # Verify prompt contains profile context
        assert "Tanaka" in prompt
        assert "Station Attendant" in prompt
        
        # Japanese-only NPC should have different response format
        assert "Japanese only response" in prompt
    
    @pytest.mark.asyncio
    async def test_contextual_prompt(self, prompt_manager, sample_request):
        """Test that contextual prompt includes conversation history."""
        # Mock conversation manager
        from unittest.mock import AsyncMock
        from src.ai.companion.core.conversation_manager import ConversationState
        
        mock_conv_manager = AsyncMock()
        prompt_manager.conversation_manager = mock_conv_manager
        
        # Mock conversation state
        mock_conv_manager.detect_conversation_state.return_value = ConversationState.FOLLOW_UP
        
        # Mock conversation context
        mock_context = {
            "entries": [
                {"type": "user_message", "text": "How do I say hello in Japanese?"},
                {"type": "assistant_message", "text": "Hello is こんにちは (konnichiwa)."}
            ]
        }
        
        # Create a coroutine mock that can be awaited
        async def mock_get_context(*args, **kwargs):
            return mock_context
        
        # Set the mock to return the coroutine function
        mock_conv_manager.get_or_create_context = mock_get_context
        
        # Mock generate_contextual_prompt to return a formatted string with conversation history
        async def mock_generate_contextual_prompt(*args, **kwargs):
            history_text = "Previous conversation:\nUser: How do I say hello in Japanese?\nAssistant: Hello is こんにちは (konnichiwa)."
            return f"This is a follow-up question.\n\n{history_text}"
            
        mock_conv_manager.generate_contextual_prompt = mock_generate_contextual_prompt
        
        # Create a contextual prompt
        prompt = await prompt_manager.create_contextual_prompt(sample_request, "conv123")
        
        # Verify prompt includes conversation history
        assert "Previous conversation" in prompt
        assert "konnichiwa" in prompt
        assert "follow-up question" in prompt 