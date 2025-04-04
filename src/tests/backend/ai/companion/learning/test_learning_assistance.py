"""
Tests for the Learning Assistance module.

This module contains tests for the learning assistance features, including
hint progression, vocabulary tracking, grammar explanation templates, and
learning pace adaptation.
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch
from typing import Dict, List, Any

from src.ai.companion.core.models import (
    ClassifiedRequest,
    CompanionRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from src.ai.companion.learning.hint_progression import HintProgressionManager
from src.ai.companion.learning.vocabulary_tracker import VocabularyTracker
from src.ai.companion.learning.grammar_templates import GrammarTemplateManager
from src.ai.companion.learning.learning_pace import LearningPaceAdapter


class TestHintProgressionManager:
    """Tests for the HintProgressionManager class."""
    
    @pytest.fixture
    def hint_manager(self):
        """Create a HintProgressionManager instance for testing."""
        return HintProgressionManager()
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample request for testing."""
        request_id = str(uuid.uuid4())
        return ClassifiedRequest(
            request_id=request_id,
            player_input="How do I buy a ticket?",
            request_type="guidance",
            intent=IntentCategory.DIRECTION_GUIDANCE,
            complexity=ComplexityLevel.SIMPLE,
            processing_tier=ProcessingTier.TIER_1,
            confidence=0.9,
            extracted_entities={"action": "buy_ticket"}
        )
    
    def test_initialization(self, hint_manager):
        """Test that the HintProgressionManager initializes correctly."""
        assert hint_manager is not None
        assert hasattr(hint_manager, 'hint_sequences')
        assert hasattr(hint_manager, 'player_hint_history')
    
    def test_get_next_hint_new_topic(self, hint_manager, sample_request):
        """Test getting the first hint for a new topic."""
        hint = hint_manager.get_next_hint(sample_request, "buy_ticket")
        
        assert hint is not None
        assert isinstance(hint, str)
        assert "ticket" in hint.lower()
        
        # Check that the hint was recorded in history
        assert "buy_ticket" in hint_manager.player_hint_history
        assert len(hint_manager.player_hint_history["buy_ticket"]) == 1
    
    def test_get_next_hint_progression(self, hint_manager, sample_request):
        """Test that hints progress through a sequence."""
        # Get first hint
        hint1 = hint_manager.get_next_hint(sample_request, "buy_ticket")
        
        # Get second hint
        hint2 = hint_manager.get_next_hint(sample_request, "buy_ticket")
        
        # They should be different
        assert hint1 != hint2
        
        # Check that both hints are in history
        assert len(hint_manager.player_hint_history["buy_ticket"]) == 2
    
    def test_reset_hint_progression(self, hint_manager, sample_request):
        """Test resetting the hint progression for a topic."""
        # Get first hint
        hint1 = hint_manager.get_next_hint(sample_request, "buy_ticket")
        
        # Reset progression
        hint_manager.reset_hint_progression("buy_ticket")
        
        # Get hint again
        hint2 = hint_manager.get_next_hint(sample_request, "buy_ticket")
        
        # Should get the same first hint again
        assert hint1 == hint2
        
        # Check that history was reset
        assert len(hint_manager.player_hint_history["buy_ticket"]) == 1
    
    def test_get_hint_for_unknown_topic(self, hint_manager, sample_request):
        """Test getting a hint for an unknown topic."""
        hint = hint_manager.get_next_hint(sample_request, "unknown_topic")
        
        # Should still get a generic hint
        assert hint is not None
        assert isinstance(hint, str)
        
        # Check that a generic hint sequence was created
        assert "unknown_topic" in hint_manager.player_hint_history
    
    def test_customize_hint_sequence(self, hint_manager):
        """Test customizing a hint sequence for a topic."""
        custom_hints = [
            "This is the first custom hint.",
            "This is the second custom hint.",
            "This is the third custom hint."
        ]
        
        hint_manager.customize_hint_sequence("custom_topic", custom_hints)
        
        # Check that the custom sequence was added
        assert "custom_topic" in hint_manager.hint_sequences
        assert hint_manager.hint_sequences["custom_topic"] == custom_hints


class TestVocabularyTracker:
    """Tests for the VocabularyTracker class."""
    
    @pytest.fixture
    def vocab_tracker(self):
        """Create a VocabularyTracker instance for testing."""
        return VocabularyTracker()
    
    def test_initialization(self, vocab_tracker):
        """Test that the VocabularyTracker initializes correctly."""
        assert vocab_tracker is not None
        assert hasattr(vocab_tracker, 'vocabulary_items')
        assert hasattr(vocab_tracker, 'player_vocabulary')
    
    def test_add_vocabulary_item(self, vocab_tracker):
        """Test adding a vocabulary item."""
        vocab_tracker.add_vocabulary_item(
            japanese="切符",
            romaji="kippu",
            english="ticket",
            jlpt_level="N5",
            tags=["train", "station"]
        )
        
        # Check that the item was added
        assert "切符" in vocab_tracker.vocabulary_items
        assert vocab_tracker.vocabulary_items["切符"]["romaji"] == "kippu"
        assert vocab_tracker.vocabulary_items["切符"]["english"] == "ticket"
        assert vocab_tracker.vocabulary_items["切符"]["jlpt_level"] == "N5"
        assert "train" in vocab_tracker.vocabulary_items["切符"]["tags"]
    
    def test_record_player_encounter(self, vocab_tracker):
        """Test recording a player encounter with a vocabulary item."""
        # Add the item first
        vocab_tracker.add_vocabulary_item(
            japanese="切符",
            romaji="kippu",
            english="ticket",
            jlpt_level="N5",
            tags=["train", "station"]
        )
        
        # Record an encounter
        vocab_tracker.record_player_encounter("切符", understood=True)
        
        # Check that the encounter was recorded
        assert "切符" in vocab_tracker.player_vocabulary
        assert vocab_tracker.player_vocabulary["切符"]["encounters"] == 1
        assert vocab_tracker.player_vocabulary["切符"]["understood_count"] == 1
        
        # Record another encounter, not understood
        vocab_tracker.record_player_encounter("切符", understood=False)
        
        # Check that the encounter was recorded
        assert vocab_tracker.player_vocabulary["切符"]["encounters"] == 2
        assert vocab_tracker.player_vocabulary["切符"]["understood_count"] == 1
    
    def test_get_vocabulary_status(self, vocab_tracker):
        """Test getting the status of a vocabulary item."""
        # Add the item first
        vocab_tracker.add_vocabulary_item(
            japanese="切符",
            romaji="kippu",
            english="ticket",
            jlpt_level="N5",
            tags=["train", "station"]
        )
        
        # Record some encounters
        vocab_tracker.record_player_encounter("切符", understood=True)
        vocab_tracker.record_player_encounter("切符", understood=True)
        vocab_tracker.record_player_encounter("切符", understood=False)
        
        # Get the status
        status = vocab_tracker.get_vocabulary_status("切符")
        
        # Check the status
        assert status["japanese"] == "切符"
        assert status["romaji"] == "kippu"
        assert status["english"] == "ticket"
        assert status["encounters"] == 3
        assert status["understood_count"] == 2
        assert status["mastery_level"] > 0  # Should have some mastery
    
    def test_get_recommended_vocabulary(self, vocab_tracker):
        """Test getting recommended vocabulary for review."""
        # Add some items
        vocab_tracker.add_vocabulary_item(
            japanese="切符",
            romaji="kippu",
            english="ticket",
            jlpt_level="N5",
            tags=["train", "station"]
        )
        vocab_tracker.add_vocabulary_item(
            japanese="電車",
            romaji="densha",
            english="train",
            jlpt_level="N5",
            tags=["train", "transportation"]
        )
        vocab_tracker.add_vocabulary_item(
            japanese="駅",
            romaji="eki",
            english="station",
            jlpt_level="N5",
            tags=["train", "location"]
        )
        
        # Record encounters with different mastery levels
        vocab_tracker.record_player_encounter("切符", understood=True)
        vocab_tracker.record_player_encounter("切符", understood=True)
        
        vocab_tracker.record_player_encounter("電車", understood=False)
        
        vocab_tracker.record_player_encounter("駅", understood=True)
        vocab_tracker.record_player_encounter("駅", understood=False)
        vocab_tracker.record_player_encounter("駅", understood=False)
        
        # Get recommendations (should prioritize items with low mastery)
        recommendations = vocab_tracker.get_recommended_vocabulary(limit=2)
        
        # Check recommendations
        assert len(recommendations) == 2
        # Items with lower mastery should be recommended first
        assert "電車" in [item["japanese"] for item in recommendations]
        assert "駅" in [item["japanese"] for item in recommendations]
    
    def test_get_vocabulary_by_tag(self, vocab_tracker):
        """Test getting vocabulary items by tag."""
        # Add some items with different tags
        vocab_tracker.add_vocabulary_item(
            japanese="切符",
            romaji="kippu",
            english="ticket",
            jlpt_level="N5",
            tags=["train", "station"]
        )
        vocab_tracker.add_vocabulary_item(
            japanese="電車",
            romaji="densha",
            english="train",
            jlpt_level="N5",
            tags=["train", "transportation"]
        )
        vocab_tracker.add_vocabulary_item(
            japanese="お弁当",
            romaji="obento",
            english="boxed lunch",
            jlpt_level="N5",
            tags=["food"]
        )
        
        # Get items by tag
        train_items = vocab_tracker.get_vocabulary_by_tag("train")
        food_items = vocab_tracker.get_vocabulary_by_tag("food")
        
        # Check results
        assert len(train_items) == 2
        assert "切符" in [item["japanese"] for item in train_items]
        assert "電車" in [item["japanese"] for item in train_items]
        
        assert len(food_items) == 1
        assert "お弁当" in [item["japanese"] for item in food_items]


class TestGrammarTemplateManager:
    """Tests for the GrammarTemplateManager class."""
    
    @pytest.fixture
    def grammar_manager(self):
        """Create a GrammarTemplateManager instance for testing."""
        return GrammarTemplateManager()
    
    def test_initialization(self, grammar_manager):
        """Test that the GrammarTemplateManager initializes correctly."""
        assert grammar_manager is not None
        assert hasattr(grammar_manager, 'grammar_templates')
        assert hasattr(grammar_manager, 'player_grammar_history')
    
    def test_get_grammar_template(self, grammar_manager):
        """Test getting a grammar template."""
        template = grammar_manager.get_grammar_template("は vs が")
        
        assert template is not None
        assert "は" in template
        assert "が" in template
        assert "subject marker" in template.lower()
    
    def test_get_unknown_grammar_template(self, grammar_manager):
        """Test getting a template for unknown grammar."""
        template = grammar_manager.get_grammar_template("unknown_grammar")
        
        # Should return a generic message
        assert template is not None
        assert "I don't have specific information" in template
    
    def test_record_grammar_explanation(self, grammar_manager):
        """Test recording a grammar explanation."""
        grammar_manager.record_grammar_explanation("は vs が")
        
        # Check that it was recorded
        assert "は vs が" in grammar_manager.player_grammar_history
        assert grammar_manager.player_grammar_history["は vs が"]["explanation_count"] == 1
        
        # Record again
        grammar_manager.record_grammar_explanation("は vs が")
        
        # Check that count increased
        assert grammar_manager.player_grammar_history["は vs が"]["explanation_count"] == 2
    
    def test_get_grammar_examples(self, grammar_manager):
        """Test getting examples for a grammar point."""
        examples = grammar_manager.get_grammar_examples("は vs が")
        
        assert examples is not None
        assert len(examples) > 0
        assert all(isinstance(example, dict) for example in examples)
        assert all("japanese" in example for example in examples)
        assert all("english" in example for example in examples)
    
    def test_add_custom_grammar_template(self, grammar_manager):
        """Test adding a custom grammar template."""
        custom_template = {
            "explanation": "This is a custom grammar explanation.",
            "examples": [
                {"japanese": "カスタム例文", "english": "Custom example sentence."}
            ],
            "common_mistakes": ["This is a common mistake."],
            "practice_suggestions": ["Try using this grammar in a sentence."]
        }
        
        grammar_manager.add_custom_grammar_template("custom_grammar", custom_template)
        
        # Check that it was added
        template = grammar_manager.get_grammar_template("custom_grammar")
        assert "custom grammar explanation" in template.lower()
        
        # Check examples
        examples = grammar_manager.get_grammar_examples("custom_grammar")
        assert len(examples) == 1
        assert examples[0]["japanese"] == "カスタム例文"


class TestLearningPaceAdapter:
    """Tests for the LearningPaceAdapter class."""
    
    @pytest.fixture
    def pace_adapter(self):
        """Create a LearningPaceAdapter instance for testing."""
        return LearningPaceAdapter()
    
    @pytest.fixture
    def vocab_tracker(self):
        """Create a VocabularyTracker instance for testing."""
        tracker = VocabularyTracker()
        
        # Add some vocabulary items
        tracker.add_vocabulary_item(
            japanese="切符",
            romaji="kippu",
            english="ticket",
            jlpt_level="N5",
            tags=["train", "station"]
        )
        tracker.add_vocabulary_item(
            japanese="電車",
            romaji="densha",
            english="train",
            jlpt_level="N5",
            tags=["train", "transportation"]
        )
        
        # Record some encounters
        tracker.record_player_encounter("切符", understood=True)
        tracker.record_player_encounter("切符", understood=True)
        tracker.record_player_encounter("電車", understood=False)
        
        return tracker
    
    def test_initialization(self, pace_adapter):
        """Test that the LearningPaceAdapter initializes correctly."""
        assert pace_adapter is not None
        assert hasattr(pace_adapter, 'player_metrics')
        assert hasattr(pace_adapter, 'adaptation_settings')
    
    def test_update_player_metrics(self, pace_adapter):
        """Test updating player metrics."""
        pace_adapter.update_player_metrics(
            correct_responses=3,
            total_responses=5,
            time_spent=120,
            complexity_level=ComplexityLevel.SIMPLE
        )
        
        # Check that metrics were updated
        assert pace_adapter.player_metrics["correct_responses"] == 3
        assert pace_adapter.player_metrics["total_responses"] == 5
        assert pace_adapter.player_metrics["time_spent"] == 120
        assert pace_adapter.player_metrics["complexity_level"] == ComplexityLevel.SIMPLE
    
    def test_get_adapted_complexity(self, pace_adapter):
        """Test getting adapted complexity level."""
        # Set up some metrics
        pace_adapter.update_player_metrics(
            correct_responses=8,
            total_responses=10,
            time_spent=120,
            complexity_level=ComplexityLevel.SIMPLE
        )
        
        # Get adapted complexity
        complexity = pace_adapter.get_adapted_complexity()
        
        # With high success rate, should recommend higher complexity
        assert complexity == ComplexityLevel.MODERATE
        
        # Update with lower success rate
        pace_adapter.update_player_metrics(
            correct_responses=3,
            total_responses=10,
            time_spent=120,
            complexity_level=ComplexityLevel.MODERATE
        )
        
        # Get adapted complexity again
        complexity = pace_adapter.get_adapted_complexity()
        
        # With lower success rate, should recommend lower complexity
        assert complexity == ComplexityLevel.SIMPLE
    
    def test_get_vocabulary_recommendations(self, pace_adapter, vocab_tracker):
        """Test getting vocabulary recommendations based on learning pace."""
        recommendations = pace_adapter.get_vocabulary_recommendations(
            vocab_tracker,
            max_items=3
        )
        
        # Should get recommendations
        assert recommendations is not None
        assert len(recommendations) <= 3
        
        # Should prioritize items with low mastery
        assert "電車" in [item["japanese"] for item in recommendations]
    
    def test_adjust_hint_frequency(self, pace_adapter):
        """Test adjusting hint frequency based on learning pace."""
        # Set up some metrics indicating struggle
        pace_adapter.update_player_metrics(
            correct_responses=2,
            total_responses=10,
            time_spent=300,
            complexity_level=ComplexityLevel.SIMPLE
        )
        
        # Get hint frequency
        frequency = pace_adapter.get_hint_frequency()
        
        # With low success rate, should recommend higher frequency
        assert frequency > 0.5
        
        # Update with higher success rate
        pace_adapter.update_player_metrics(
            correct_responses=9,
            total_responses=10,
            time_spent=120,
            complexity_level=ComplexityLevel.SIMPLE
        )
        
        # Get hint frequency again
        frequency = pace_adapter.get_hint_frequency()
        
        # With higher success rate, should recommend lower frequency
        assert frequency < 0.5
    
    def test_get_learning_pace_summary(self, pace_adapter):
        """Test getting a summary of the player's learning pace."""
        # Set up some metrics
        pace_adapter.update_player_metrics(
            correct_responses=7,
            total_responses=10,
            time_spent=180,
            complexity_level=ComplexityLevel.SIMPLE
        )
        
        # Get summary
        summary = pace_adapter.get_learning_pace_summary()
        
        # Check summary
        assert summary is not None
        assert "success rate" in summary.lower()
        assert "70%" in summary  # 7/10 = 70%
        assert "complexity" in summary.lower()
    
    def test_adapt_to_player_performance(self, pace_adapter):
        """Test adapting to player performance over time."""
        # Simulate several updates with improving performance
        pace_adapter.update_player_metrics(
            correct_responses=5,
            total_responses=10,
            time_spent=200,
            complexity_level=ComplexityLevel.SIMPLE
        )
        
        pace_adapter.update_player_metrics(
            correct_responses=7,
            total_responses=10,
            time_spent=180,
            complexity_level=ComplexityLevel.SIMPLE
        )
        
        pace_adapter.update_player_metrics(
            correct_responses=9,
            total_responses=10,
            time_spent=150,
            complexity_level=ComplexityLevel.SIMPLE
        )
        
        # Adapt to performance
        adaptation = pace_adapter.adapt_to_player_performance()
        
        # Check adaptation recommendations
        assert adaptation is not None
        assert "complexity_level" in adaptation
        assert adaptation["complexity_level"] == ComplexityLevel.MODERATE
        assert "hint_frequency" in adaptation
        assert adaptation["hint_frequency"] < 0.5  # Should be low with good performance 