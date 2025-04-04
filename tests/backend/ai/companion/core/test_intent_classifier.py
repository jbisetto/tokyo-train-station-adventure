"""
Tests for the Intent Classifier component.
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch

from src.ai.companion.core.models import (
    CompanionRequest,
    GameContext,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from src.ai.companion.config import TIER_CONFIG


@pytest.fixture
def vocabulary_request():
    """Create a sample vocabulary request."""
    return CompanionRequest(
        request_id=str(uuid.uuid4()),
        player_input="What does 'kippu' mean?",
        request_type="vocabulary"
    )


@pytest.fixture
def grammar_request():
    """Create a sample grammar request."""
    return CompanionRequest(
        request_id=str(uuid.uuid4()),
        player_input="How do I use the particle 'wa' versus 'ga'?",
        request_type="grammar"
    )


@pytest.fixture
def direction_request():
    """Create a sample direction request."""
    return CompanionRequest(
        request_id=str(uuid.uuid4()),
        player_input="How do I get to platform 3?",
        request_type="direction"
    )


@pytest.fixture
def translation_request():
    """Create a sample translation request."""
    return CompanionRequest(
        request_id=str(uuid.uuid4()),
        player_input="Can you translate this sign for me?",
        request_type="translation"
    )


@pytest.fixture
def hint_request():
    """Create a sample hint request."""
    return CompanionRequest(
        request_id=str(uuid.uuid4()),
        player_input="What should I do next?",
        request_type="hint"
    )


@pytest.fixture
def sample_game_context():
    """Provide a sample game context for testing."""
    return GameContext(
        player_location="main_concourse",
        current_objective="find_ticket_machine",
        nearby_npcs=["station_attendant", "tourist"],
        nearby_objects=["information_board", "ticket_machine"],
        player_inventory=["wallet", "phone"],
        language_proficiency={"vocabulary": 0.4, "grammar": 0.3, "reading": 0.5},
        game_progress={"tutorial_completed": True, "tickets_purchased": 0}
    )


class TestIntentClassifier:
    """Tests for the IntentClassifier class."""
    
    def test_initialization(self):
        """Test that the IntentClassifier can be initialized."""
        from src.ai.companion.core.intent_classifier import IntentClassifier
        
        classifier = IntentClassifier()
        
        assert classifier is not None
        assert hasattr(classifier, 'classify')
    
    def test_classify_vocabulary_request(self, vocabulary_request):
        """Test classification of a vocabulary request."""
        from src.ai.companion.core.intent_classifier import IntentClassifier
        
        classifier = IntentClassifier()
        
        intent, complexity, tier, confidence, entities = classifier.classify(vocabulary_request)
        
        assert intent == IntentCategory.VOCABULARY_HELP
        assert isinstance(complexity, ComplexityLevel)
        assert isinstance(tier, ProcessingTier)
        assert 0 <= confidence <= 1
        assert isinstance(entities, dict)
        assert "word" in entities
        assert entities["word"] == "kippu"
    
    def test_classify_grammar_request(self, grammar_request):
        """Test classification of a grammar request."""
        from src.ai.companion.core.intent_classifier import IntentClassifier
        
        classifier = IntentClassifier()
        
        intent, complexity, tier, confidence, entities = classifier.classify(grammar_request)
        
        assert intent == IntentCategory.GRAMMAR_EXPLANATION
        assert isinstance(complexity, ComplexityLevel)
        assert isinstance(tier, ProcessingTier)
        assert 0 <= confidence <= 1
        assert isinstance(entities, dict)
    
    def test_classify_direction_request(self, direction_request):
        """Test classification of a direction request."""
        from src.ai.companion.core.intent_classifier import IntentClassifier
        
        classifier = IntentClassifier()
        
        intent, complexity, tier, confidence, entities = classifier.classify(direction_request)
        
        assert intent == IntentCategory.DIRECTION_GUIDANCE
        assert isinstance(complexity, ComplexityLevel)
        assert isinstance(tier, ProcessingTier)
        assert 0 <= confidence <= 1
        assert isinstance(entities, dict)
    
    def test_classify_translation_request(self, translation_request):
        """Test classification of a translation request."""
        from src.ai.companion.core.intent_classifier import IntentClassifier
        
        classifier = IntentClassifier()
        
        intent, complexity, tier, confidence, entities = classifier.classify(translation_request)
        
        assert intent == IntentCategory.TRANSLATION_CONFIRMATION
        assert isinstance(complexity, ComplexityLevel)
        assert isinstance(tier, ProcessingTier)
        assert 0 <= confidence <= 1
        assert isinstance(entities, dict)
    
    def test_classify_hint_request(self, hint_request):
        """Test classification of a hint request."""
        from src.ai.companion.core.intent_classifier import IntentClassifier
        
        classifier = IntentClassifier()
        
        intent, complexity, tier, confidence, entities = classifier.classify(hint_request)
        
        assert intent == IntentCategory.GENERAL_HINT
        assert isinstance(complexity, ComplexityLevel)
        assert isinstance(tier, ProcessingTier)
        assert 0 <= confidence <= 1
        assert isinstance(entities, dict)
    
    def test_classify_with_game_context(self, vocabulary_request, sample_game_context):
        """Test classification with game context."""
        from src.ai.companion.core.intent_classifier import IntentClassifier
        
        # Add game context to the request
        vocabulary_request.game_context = sample_game_context
        
        classifier = IntentClassifier()
        
        intent, complexity, tier, confidence, entities = classifier.classify(vocabulary_request)
        
        # The classification should take into account the game context
        assert intent == IntentCategory.VOCABULARY_HELP
        assert isinstance(complexity, ComplexityLevel)
        assert isinstance(tier, ProcessingTier)
        assert 0 <= confidence <= 1
        assert isinstance(entities, dict)
    
    def test_complexity_determination(self):
        """Test that the classifier determines complexity correctly."""
        from src.ai.companion.core.intent_classifier import IntentClassifier
        
        classifier = IntentClassifier()
        
        # Simple request
        simple_request = CompanionRequest(
            request_id=str(uuid.uuid4()),
            player_input="What does 'kippu' mean?",
            request_type="vocabulary"
        )
        
        # Moderate request
        moderate_request = CompanionRequest(
            request_id=str(uuid.uuid4()),
            player_input="Can you explain the difference between 'wa' and 'ga' when marking the subject?",
            request_type="grammar"
        )
        
        # Complex request
        complex_request = CompanionRequest(
            request_id=str(uuid.uuid4()),
            player_input="If I wanted to say 'I would have gone to Tokyo if I had more time', how would I express that?",
            request_type="grammar"
        )
        
        # Test simple request
        _, complexity_simple, _, _, _ = classifier.classify(simple_request)
        assert complexity_simple == ComplexityLevel.SIMPLE
        
        # Test moderate request
        _, complexity_moderate, _, _, _ = classifier.classify(moderate_request)
        assert complexity_moderate == ComplexityLevel.MODERATE
        
        # Test complex request
        _, complexity_complex, _, _, _ = classifier.classify(complex_request)
        assert complexity_complex == ComplexityLevel.COMPLEX
    
    def test_tier_selection(self):
        """Test that the classifier selects the appropriate tier based on complexity."""
        from src.ai.companion.core.intent_classifier import IntentClassifier
        
        classifier = IntentClassifier()
        
        # Simple request should go to Tier 1
        simple_request = CompanionRequest(
            request_id=str(uuid.uuid4()),
            player_input="What does 'kippu' mean?",
            request_type="vocabulary"
        )
        
        # Moderate request should go to Tier 2
        moderate_request = CompanionRequest(
            request_id=str(uuid.uuid4()),
            player_input="Can you explain the difference between 'wa' and 'ga' when marking the subject?",
            request_type="grammar"
        )
        
        # Complex request should go to Tier 3
        complex_request = CompanionRequest(
            request_id=str(uuid.uuid4()),
            player_input="If I wanted to say 'I would have gone to Tokyo if I had more time', how would I express that?",
            request_type="grammar"
        )
        
        # Test simple request
        _, _, tier_simple, _, _ = classifier.classify(simple_request)
        assert tier_simple == ProcessingTier.TIER_1
        
        # Test moderate request
        _, _, tier_moderate, _, _ = classifier.classify(moderate_request)
        assert tier_moderate == ProcessingTier.TIER_2
        
        # Test complex request
        _, _, tier_complex, _, _ = classifier.classify(complex_request)
        assert tier_complex == ProcessingTier.TIER_3
    
    def test_entity_extraction(self):
        """Test that the classifier extracts entities correctly."""
        from src.ai.companion.core.intent_classifier import IntentClassifier
        
        classifier = IntentClassifier()
        
        # Request with a vocabulary word
        vocab_request = CompanionRequest(
            request_id=str(uuid.uuid4()),
            player_input="What does 'kippu' mean?",
            request_type="vocabulary"
        )
        
        # Request with a grammar concept - using a simpler example that will match our extraction pattern
        grammar_request = CompanionRequest(
            request_id=str(uuid.uuid4()),
            player_input="How do I use 'wa'?",
            request_type="grammar"
        )
        
        # Request with a location
        direction_request = CompanionRequest(
            request_id=str(uuid.uuid4()),
            player_input="How do I get to platform 3?",
            request_type="direction"
        )
        
        # Test vocabulary request
        _, _, _, _, entities_vocab = classifier.classify(vocab_request)
        assert "word" in entities_vocab
        assert entities_vocab["word"] == "kippu"
        
        # Test grammar request
        _, _, _, _, entities_grammar = classifier.classify(grammar_request)
        assert "grammar_point" in entities_grammar
        assert entities_grammar["grammar_point"] == "wa"
        
        # Test direction request
        _, _, _, _, entities_direction = classifier.classify(direction_request)
        assert "location" in entities_direction
        assert entities_direction["location"] == "platform 3" 