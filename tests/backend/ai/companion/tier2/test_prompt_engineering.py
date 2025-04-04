"""
Tests for the prompt engineering module.

This module contains tests for the prompt engineering functionality used by the Tier 2 processor
to create effective prompts for local language models.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.ai.companion.core.models import (
    CompanionRequest,
    ClassifiedRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier,
    GameContext
)


@pytest.fixture
def sample_request():
    """Create a sample request for testing."""
    request = CompanionRequest(
        request_id="test-123",
        player_input="How do I say 'I want to go to Tokyo' in Japanese?",
        request_type="translation"
    )
    
    return ClassifiedRequest.from_companion_request(
        request=request,
        intent=IntentCategory.TRANSLATION_CONFIRMATION,
        complexity=ComplexityLevel.MODERATE,
        processing_tier=ProcessingTier.TIER_2,
        confidence=0.85,
        extracted_entities={"destination": "Tokyo"}
    )


@pytest.fixture
def sample_request_with_context():
    """Create a sample request with game context for testing."""
    game_context = GameContext(
        player_location="Tokyo Station",
        current_objective="Find the ticket office",
        nearby_npcs=["Station attendant", "Tourist"],
        nearby_objects=["Train schedule", "Map"],
        player_inventory=["Guidebook", "Phone"],
        language_proficiency={"Japanese": 0.3}
    )
    
    request = CompanionRequest(
        request_id="test-456",
        player_input="How do I ask where the ticket office is?",
        request_type="translation",
        game_context=game_context
    )
    
    return ClassifiedRequest.from_companion_request(
        request=request,
        intent=IntentCategory.TRANSLATION_CONFIRMATION,
        complexity=ComplexityLevel.MODERATE,
        processing_tier=ProcessingTier.TIER_2,
        confidence=0.85,
        extracted_entities={"location": "ticket office"}
    )


class TestPromptManager:
    """Tests for the PromptManager class."""
    
    def test_initialization(self):
        """Test that the PromptManager can be initialized."""
        from src.ai.companion.core.prompt_manager import PromptManager
        
        prompt_manager = PromptManager()
        
        assert prompt_manager is not None
        assert hasattr(prompt_manager, 'create_prompt')
    
    def test_create_prompt_basic(self, sample_request):
        """Test creating a basic prompt."""
        from src.ai.companion.core.prompt_manager import PromptManager
        
        prompt_manager = PromptManager()
        
        prompt = prompt_manager.create_prompt(sample_request)
        
        # Check that the prompt contains the necessary information
        assert "Hachiko" in prompt
        assert "companion" in prompt
        assert "Tokyo Train Station Adventure" in prompt
        assert "How do I say 'I want to go to Tokyo' in Japanese?" in prompt
        assert "translation" in prompt
        
        # Check that the prompt includes instructions for the model
        assert "helpful" in prompt
        assert "concise" in prompt
        assert "Japanese" in prompt
    
    def test_create_prompt_with_context(self, sample_request_with_context):
        """Test creating a prompt with game context."""
        from src.ai.companion.core.prompt_manager import PromptManager
        
        prompt_manager = PromptManager()
        
        prompt = prompt_manager.create_prompt(sample_request_with_context)
        
        # Check that the prompt contains the game context
        assert "Tokyo Station" in prompt
        assert "ticket office" in prompt
        assert "Station attendant" in prompt
        assert "Japanese: 0.3" in prompt
    
    def test_create_prompt_with_intent(self, sample_request):
        """Test creating a prompt with intent information."""
        from src.ai.companion.core.prompt_manager import PromptManager
        
        prompt_manager = PromptManager()
        
        # Change the intent
        sample_request.intent = IntentCategory.VOCABULARY_HELP
        
        prompt = prompt_manager.create_prompt(sample_request)
        
        # Check that the prompt contains the intent information
        assert "vocabulary_help" in prompt
        assert "Explain the meaning of the word clearly" in prompt
    
    def test_create_prompt_with_complexity(self, sample_request):
        """Test creating a prompt with complexity information."""
        from src.ai.companion.core.prompt_manager import PromptManager
        
        prompt_manager = PromptManager()
        
        # Test with different complexity levels
        sample_request.complexity = ComplexityLevel.SIMPLE
        simple_prompt = prompt_manager.create_prompt(sample_request)
        
        sample_request.complexity = ComplexityLevel.COMPLEX
        complex_prompt = prompt_manager.create_prompt(sample_request)
        
        # Check that the prompts reflect the complexity
        assert "simple" in simple_prompt.lower()
        assert "complex" in complex_prompt.lower()
        assert len(complex_prompt) > len(simple_prompt)
    
    def test_create_prompt_with_entities(self, sample_request):
        """Test creating a prompt with extracted entities."""
        from src.ai.companion.core.prompt_manager import PromptManager
        
        prompt_manager = PromptManager()
        
        # Add more extracted entities
        sample_request.extracted_entities.update({
            "phrase": "I want to go to Tokyo",
            "language": "Japanese"
        })
        
        prompt = prompt_manager.create_prompt(sample_request)
        
        # Check that the prompt contains the extracted entities
        assert "destination: Tokyo" in prompt
        assert "phrase: I want to go to Tokyo" in prompt
        assert "language: Japanese" in prompt
    
    def test_create_prompt_for_different_request_types(self):
        """Test creating prompts for different request types."""
        from src.ai.companion.core.prompt_manager import PromptManager
        from src.ai.companion.core.models import ClassifiedRequest, IntentCategory, ComplexityLevel, ProcessingTier
        
        prompt_manager = PromptManager()
        
        # Test with different request types
        request_types = ["translation", "vocabulary", "grammar", "culture", "directions"]
        
        for req_type in request_types:
            request = ClassifiedRequest(
                request_id=f"test-{req_type}",
                player_input="Test input",
                request_type=req_type,
                intent=IntentCategory.VOCABULARY_HELP,
                complexity=ComplexityLevel.SIMPLE,
                processing_tier=ProcessingTier.TIER_2
            )
            
            prompt = prompt_manager.create_prompt(request)
            
            # Check that the prompt contains request-type specific instructions
            assert req_type in prompt.lower()
            
            # Different request types should have different content
            if req_type == "translation":
                assert "translation" in prompt.lower()
            elif req_type == "vocabulary":
                assert "vocabulary" in prompt.lower()
            # ... etc.
    
    def test_prompt_includes_guardrails(self, sample_request):
        """Test that the prompt includes topic boundaries and redirection instructions."""
        from src.ai.companion.core.prompt_manager import PromptManager
        
        prompt_manager = PromptManager()
        prompt = prompt_manager.create_prompt(sample_request)
        
        # Check for topic boundary instructions
        assert "STRICT TOPIC BOUNDARIES" in prompt
        assert "ONLY respond to questions about Japanese language" in prompt
        assert "ONLY respond to questions about train station navigation" in prompt
        assert "ONLY respond to questions about basic cultural aspects" in prompt
        assert "ONLY respond to questions about how to play the game" in prompt
        assert "If asked about ANY other topic, politely redirect" in prompt
        
        # Check for redirection examples
        assert "REDIRECTION EXAMPLES" in prompt
        assert "I'm just a station dog" in prompt
        assert "I focus on helping you navigate the station" in prompt
        
        # Check that final instructions include guardrails
        assert "ONLY respond to game-relevant topics" in prompt
        assert "Politely redirect ANY off-topic questions" in prompt 