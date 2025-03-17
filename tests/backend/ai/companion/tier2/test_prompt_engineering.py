"""
Tests for the prompt engineering module.

This module contains tests for the prompt engineering functionality used by the Tier 2 processor
to create effective prompts for local language models.
"""

import pytest
from unittest.mock import patch, MagicMock

from backend.ai.companion.core.models import (
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
        from backend.ai.companion.core.prompt_manager import PromptManager
        
        prompt_manager = PromptManager()
        
        assert prompt_manager is not None
        assert hasattr(prompt_manager, 'create_prompt')
    
    def test_create_prompt_basic(self, sample_request):
        """Test creating a basic prompt."""
        from backend.ai.companion.core.prompt_manager import PromptManager
        
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
        from backend.ai.companion.core.prompt_manager import PromptManager
        
        prompt_manager = PromptManager()
        
        prompt = prompt_manager.create_prompt(sample_request_with_context)
        
        # Check that the prompt contains the game context
        assert "Tokyo Station" in prompt
        assert "ticket office" in prompt
        assert "Station attendant" in prompt
        assert "Japanese: 0.3" in prompt
    
    def test_create_prompt_with_intent(self, sample_request):
        """Test creating a prompt with intent information."""
        from backend.ai.companion.core.prompt_manager import PromptManager
        
        prompt_manager = PromptManager()
        
        # Change the intent
        sample_request.intent = IntentCategory.VOCABULARY_HELP
        
        prompt = prompt_manager.create_prompt(sample_request)
        
        # Check that the prompt contains the intent information
        assert "vocabulary_help" in prompt
        assert "Explain the meaning of the word clearly" in prompt
    
    def test_create_prompt_with_complexity(self, sample_request):
        """Test creating a prompt with complexity information."""
        from backend.ai.companion.core.prompt_manager import PromptManager
        
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
        from backend.ai.companion.core.prompt_manager import PromptManager
        
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
        from backend.ai.companion.core.prompt_manager import PromptManager
        from backend.ai.companion.core.models import CompanionRequest, ClassifiedRequest
        
        prompt_manager = PromptManager()
        
        # Create requests with different types
        translation_request = ClassifiedRequest.from_companion_request(
            request=CompanionRequest(
                request_id="test-1",
                player_input="How do I say 'hello' in Japanese?",
                request_type="translation"
            ),
            intent=IntentCategory.TRANSLATION_CONFIRMATION,
            complexity=ComplexityLevel.SIMPLE,
            processing_tier=ProcessingTier.TIER_2
        )
        
        vocabulary_request = ClassifiedRequest.from_companion_request(
            request=CompanionRequest(
                request_id="test-2",
                player_input="What does 'konnichiwa' mean?",
                request_type="vocabulary"
            ),
            intent=IntentCategory.VOCABULARY_HELP,
            complexity=ComplexityLevel.SIMPLE,
            processing_tier=ProcessingTier.TIER_2
        )
        
        grammar_request = ClassifiedRequest.from_companion_request(
            request=CompanionRequest(
                request_id="test-3",
                player_input="How do I use the particle 'wa'?",
                request_type="grammar"
            ),
            intent=IntentCategory.GRAMMAR_EXPLANATION,
            complexity=ComplexityLevel.MODERATE,
            processing_tier=ProcessingTier.TIER_2
        )
        
        culture_request = ClassifiedRequest.from_companion_request(
            request=CompanionRequest(
                request_id="test-4",
                player_input="Why do people bow in Japan?",
                request_type="culture"
            ),
            intent=IntentCategory.GENERAL_HINT,
            complexity=ComplexityLevel.MODERATE,
            processing_tier=ProcessingTier.TIER_2
        )
        
        # Generate prompts for each request type
        translation_prompt = prompt_manager.create_prompt(translation_request)
        vocabulary_prompt = prompt_manager.create_prompt(vocabulary_request)
        grammar_prompt = prompt_manager.create_prompt(grammar_request)
        culture_prompt = prompt_manager.create_prompt(culture_request)
        
        # Check that each prompt contains type-specific instructions
        assert "translation" in translation_prompt
        assert "kanji/kana and romaji" in translation_prompt
        
        assert "vocabulary" in vocabulary_prompt
        assert "meaning, usage" in vocabulary_prompt
        assert "example sentences" in vocabulary_prompt
        
        assert "grammar" in grammar_prompt
        assert "grammar point" in grammar_prompt
        assert "examples and usage notes" in grammar_prompt
        
        assert "culture" in culture_prompt
        assert "cultural information" in culture_prompt
        assert "historical context" in culture_prompt 