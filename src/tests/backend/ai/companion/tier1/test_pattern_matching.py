"""
Tests for the Pattern Matching component.

This module contains tests for the pattern matching engine used by the Tier 1 processor
to recognize patterns in player inputs, including vocabulary, grammar, and fuzzy matching.
"""

import pytest
import os
import json
from unittest.mock import patch, mock_open
from enum import Enum

from src.ai.companion.core.models import (
    ClassifiedRequest,
    CompanionRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)


@pytest.fixture
def sample_patterns():
    """Create a sample set of patterns for testing."""
    return {
        "vocabulary": {
            "station": [
                "駅",
                "えき",
                "eki"
            ],
            "ticket": [
                "切符",
                "きっぷ",
                "kippu"
            ],
            "train": [
                "電車",
                "でんしゃ",
                "densha"
            ],
            "platform": [
                "ホーム",
                "プラットホーム",
                "houmu",
                "purattohoomu"
            ],
            "exit": [
                "出口",
                "でぐち",
                "deguchi"
            ]
        },
        "grammar": {
            "want_to": {
                "patterns": [
                    "～たい",
                    "～がほしい",
                    "want to",
                    "would like to"
                ],
                "usage": "express desire or wish to do something"
            },
            "must": {
                "patterns": [
                    "～なければならない",
                    "～ないといけない",
                    "must",
                    "have to"
                ],
                "usage": "express obligation or necessity"
            },
            "can": {
                "patterns": [
                    "～ことができる",
                    "～られる",
                    "can",
                    "able to"
                ],
                "usage": "express ability or possibility"
            }
        },
        "phrases": {
            "where_is": [
                "どこ",
                "どこですか",
                "where is",
                "where can I find"
            ],
            "how_to": [
                "どうやって",
                "どのように",
                "how do I",
                "how to"
            ],
            "what_is": [
                "何",
                "なん",
                "what is",
                "what does"
            ]
        }
    }


@pytest.fixture
def sample_jlpt_n5_vocab():
    """Create a sample set of JLPT N5 vocabulary for testing."""
    return {
        "駅": {"reading": "えき", "romaji": "eki", "meaning": "station"},
        "切符": {"reading": "きっぷ", "romaji": "kippu", "meaning": "ticket"},
        "電車": {"reading": "でんしゃ", "romaji": "densha", "meaning": "train"},
        "出口": {"reading": "でぐち", "romaji": "deguchi", "meaning": "exit"},
        "入口": {"reading": "いりぐち", "romaji": "iriguchi", "meaning": "entrance"},
        "人": {"reading": "ひと", "romaji": "hito", "meaning": "person"},
        "時間": {"reading": "じかん", "romaji": "jikan", "meaning": "time"},
        "今": {"reading": "いま", "romaji": "ima", "meaning": "now"},
        "行く": {"reading": "いく", "romaji": "iku", "meaning": "to go"},
        "来る": {"reading": "くる", "romaji": "kuru", "meaning": "to come"}
    }


class TestPatternMatcher:
    """Tests for the PatternMatcher class."""
    
    def test_initialization(self):
        """Test that the PatternMatcher can be initialized."""
        from src.ai.companion.tier1.pattern_matching import PatternMatcher
        
        matcher = PatternMatcher()
        
        assert matcher is not None
        assert hasattr(matcher, 'match')
        assert hasattr(matcher, 'load_patterns')
    
    def test_load_patterns_from_file(self):
        """Test loading patterns from a file."""
        from src.ai.companion.tier1.pattern_matching import PatternMatcher
        
        # Mock the open function to return a sample patterns file
        mock_patterns = json.dumps({
            "vocabulary": {
                "station": ["駅", "えき", "eki"]
            }
        })
        
        with patch("builtins.open", mock_open(read_data=mock_patterns)):
            matcher = PatternMatcher(patterns_file="mock_path.json")
            
            # Check that patterns were loaded
            assert matcher.patterns is not None
            assert "vocabulary" in matcher.patterns
            assert "station" in matcher.patterns["vocabulary"]
            assert len(matcher.patterns["vocabulary"]["station"]) == 3
    
    def test_load_patterns_from_dict(self, sample_patterns):
        """Test loading patterns from a dictionary."""
        from src.ai.companion.tier1.pattern_matching import PatternMatcher
        
        matcher = PatternMatcher(patterns=sample_patterns)
        
        # Check that patterns were loaded
        assert matcher.patterns is not None
        assert "vocabulary" in matcher.patterns
        assert "grammar" in matcher.patterns
        assert "phrases" in matcher.patterns
    
    def test_match_exact_vocabulary(self, sample_patterns):
        """Test matching exact vocabulary."""
        from src.ai.companion.tier1.pattern_matching import PatternMatcher
        
        matcher = PatternMatcher(patterns=sample_patterns)
        
        # Test exact matches
        result = matcher.match("What does 駅 mean?")
        assert result is not None
        assert "matches" in result
        assert "station" in result["matches"]["vocabulary"]
        
        result = matcher.match("How do I say ticket in Japanese?")
        assert result is not None
        assert "matches" in result
        assert "ticket" not in result["matches"].get("vocabulary", {})
        
        result = matcher.match("kippu means ticket in Japanese")
        assert result is not None
        assert "matches" in result
        assert "ticket" in result["matches"]["vocabulary"]
    
    def test_match_grammar_patterns(self, sample_patterns):
        """Test matching grammar patterns."""
        from src.ai.companion.tier1.pattern_matching import PatternMatcher
        
        matcher = PatternMatcher(patterns=sample_patterns)
        
        # Test grammar pattern matches
        result = matcher.match("I want to go to Tokyo Station")
        assert result is not None
        assert "matches" in result
        assert "want_to" in result["matches"].get("grammar", {})
        
        result = matcher.match("You must buy a ticket before boarding the train")
        assert result is not None
        assert "matches" in result
        assert "must" in result["matches"].get("grammar", {})
    
    def test_match_phrases(self, sample_patterns):
        """Test matching common phrases."""
        from src.ai.companion.tier1.pattern_matching import PatternMatcher
        
        matcher = PatternMatcher(patterns=sample_patterns)
        
        # Test phrase matches
        result = matcher.match("Where is the exit?")
        assert result is not None
        assert "matches" in result
        assert "where_is" in result["matches"].get("phrases", {})
        assert "exit" in result["matches"].get("vocabulary", {})
        
        result = matcher.match("How do I get to the platform?")
        assert result is not None
        assert "matches" in result
        assert "how_to" in result["matches"].get("phrases", {})
        assert "platform" in result["matches"].get("vocabulary", {})
    
    def test_match_with_context(self, sample_patterns):
        """Test matching with context."""
        from src.ai.companion.tier1.pattern_matching import PatternMatcher
        
        matcher = PatternMatcher(patterns=sample_patterns)
        
        # Create a context
        context = {
            "location": "station",
            "previous_topic": "tickets"
        }
        
        # Test matching with context
        result = matcher.match("Where can I buy one?", context=context)
        assert result is not None
        assert "matches" in result
        assert "context" in result
        assert result["context"]["previous_topic"] == "tickets"
    
    def test_fuzzy_matching(self, sample_patterns):
        """Test fuzzy matching for typos and variations."""
        from src.ai.companion.tier1.pattern_matching import PatternMatcher
        
        matcher = PatternMatcher(patterns=sample_patterns)
        
        # Test fuzzy matches
        result = matcher.match("What does kipu mean?")  # Missing 'p' in kippu
        assert result is not None
        assert "matches" in result
        assert "ticket" in result["matches"].get("vocabulary", {})
        assert result["matches"]["vocabulary"]["ticket"]["fuzzy"] is True
        
        result = matcher.match("Where is the ekii?")  # Extra 'i' in eki
        assert result is not None
        assert "matches" in result
        assert "station" in result["matches"].get("vocabulary", {})
        assert result["matches"]["vocabulary"]["station"]["fuzzy"] is True
    
    def test_match_multiple_patterns(self, sample_patterns):
        """Test matching multiple patterns in a single input."""
        from src.ai.companion.tier1.pattern_matching import PatternMatcher
        
        matcher = PatternMatcher(patterns=sample_patterns)
        
        # Test multiple matches
        result = matcher.match("I want to know how to get to the station exit")
        assert result is not None
        assert "matches" in result
        assert "want_to" in result["matches"].get("grammar", {})
        assert "how_to" in result["matches"].get("phrases", {})
        assert "station" in result["matches"].get("vocabulary", {})
        assert "exit" in result["matches"].get("vocabulary", {})
    
    def test_match_with_confidence(self, sample_patterns):
        """Test that matches include confidence scores."""
        from src.ai.companion.tier1.pattern_matching import PatternMatcher
        
        matcher = PatternMatcher(patterns=sample_patterns)
        
        # Test confidence scores
        result = matcher.match("Where is the station?")
        assert result is not None
        assert "matches" in result
        assert "station" in result["matches"].get("vocabulary", {})
        assert "confidence" in result["matches"]["vocabulary"]["station"]
        assert 0 <= result["matches"]["vocabulary"]["station"]["confidence"] <= 1
    
    def test_no_matches(self, sample_patterns):
        """Test behavior when no patterns match."""
        from src.ai.companion.tier1.pattern_matching import PatternMatcher
        
        matcher = PatternMatcher(patterns=sample_patterns)
        
        # Test no matches
        result = matcher.match("The weather is nice today")
        assert result is not None
        assert "matches" in result
        assert len(result["matches"].get("vocabulary", {})) == 0
        assert len(result["matches"].get("grammar", {})) == 0
        assert len(result["matches"].get("phrases", {})) == 0
    
    def test_extract_entities(self, sample_patterns):
        """Test extracting entities from matches."""
        from src.ai.companion.tier1.pattern_matching import PatternMatcher
        
        matcher = PatternMatcher(patterns=sample_patterns)
        
        # Test entity extraction
        result = matcher.match("How do I get to Tokyo Station?")
        entities = matcher.extract_entities(result)
        
        assert entities is not None
        assert "location" in entities
        assert entities["location"] == "Tokyo Station"
        
        # Test with a different input
        result = matcher.match("What does densha mean in Japanese?")
        entities = matcher.extract_entities(result)
        
        assert entities is not None
        assert "word" in entities
        assert entities["word"] == "densha"
        assert "meaning" in entities
        assert entities["meaning"] == "train"
    
    def test_jlpt_n5_vocabulary_recognition(self, sample_jlpt_n5_vocab):
        """Test recognition of JLPT N5 vocabulary."""
        from src.ai.companion.tier1.pattern_matching import PatternMatcher
        
        matcher = PatternMatcher(jlpt_n5_vocab=sample_jlpt_n5_vocab)
        
        # Test JLPT N5 vocabulary recognition
        result = matcher.match("What does 駅 mean?")
        assert result is not None
        assert "matches" in result
        assert "vocabulary" in result["matches"]
        assert "station" in result["matches"]["vocabulary"]
        assert "jlpt_level" in result["matches"]["vocabulary"]["station"]
        assert result["matches"]["vocabulary"]["station"]["jlpt_level"] == "N5"
        
        # Test with romaji
        result = matcher.match("What does densha mean?")
        assert result is not None
        assert "matches" in result
        assert "vocabulary" in result["matches"]
        assert "train" in result["matches"]["vocabulary"]
        assert "jlpt_level" in result["matches"]["vocabulary"]["train"]
        assert result["matches"]["vocabulary"]["train"]["jlpt_level"] == "N5"
    
    def test_save_patterns(self, sample_patterns, tmp_path):
        """Test saving patterns to a file."""
        from src.ai.companion.tier1.pattern_matching import PatternMatcher
        
        matcher = PatternMatcher(patterns=sample_patterns)
        
        # Create a temporary file path
        temp_file = tmp_path / "test_patterns.json"
        
        # Save the patterns
        matcher.save_patterns(str(temp_file))
        
        # Check that the file was created
        assert os.path.exists(temp_file)
        
        # Load the file and check contents
        with open(temp_file, 'r') as f:
            saved_patterns = json.load(f)
        
        # Check that the saved patterns match the original
        assert saved_patterns == sample_patterns
    
    def test_add_pattern(self, sample_patterns):
        """Test adding a new pattern."""
        from src.ai.companion.tier1.pattern_matching import PatternMatcher
        
        matcher = PatternMatcher(patterns=sample_patterns)
        
        # Add a new vocabulary pattern
        matcher.add_pattern("vocabulary", "bathroom", ["トイレ", "おてあらい", "toire", "otearai"])
        
        # Check that the pattern was added
        assert "bathroom" in matcher.patterns["vocabulary"]
        assert "トイレ" in matcher.patterns["vocabulary"]["bathroom"]
        
        # Test matching with the new pattern
        result = matcher.match("Where is the toire?")
        assert result is not None
        assert "matches" in result
        assert "bathroom" in result["matches"].get("vocabulary", {})
    
    def test_remove_pattern(self, sample_patterns):
        """Test removing a pattern."""
        from src.ai.companion.tier1.pattern_matching import PatternMatcher
        
        matcher = PatternMatcher(patterns=sample_patterns)
        
        # Remove a vocabulary pattern
        matcher.remove_pattern("vocabulary", "station")
        
        # Check that the pattern was removed
        assert "station" not in matcher.patterns["vocabulary"]
        
        # Test matching without the removed pattern
        result = matcher.match("Where is the eki?")
        assert result is not None
        assert "matches" in result
        assert "station" not in result["matches"].get("vocabulary", {})


class TestPatternMatchingIntegration:
    """Integration tests for pattern matching with other components."""
    
    def test_integration_with_intent_classifier(self, sample_patterns):
        """Test integration with the intent classifier."""
        from src.ai.companion.tier1.pattern_matching import PatternMatcher
        from src.ai.companion.core.intent_classifier import IntentClassifier
        from src.ai.companion.core.models import ClassifiedRequest
        
        matcher = PatternMatcher(patterns=sample_patterns)
        classifier = IntentClassifier()
        
        # Create a request
        request = CompanionRequest(
            request_id="test-123",
            player_input="What does kippu mean?",
            request_type="vocabulary"
        )
        
        # Match patterns
        match_result = matcher.match(request.player_input)
        
        # Extract entities
        entities = matcher.extract_entities(match_result)
        
        # Manually create a classified request for testing
        # In a real scenario, we would use the classifier's output
        classified_request = ClassifiedRequest(
            request_id=request.request_id,
            player_input=request.player_input,
            request_type=request.request_type,
            intent=IntentCategory.VOCABULARY_HELP,
            complexity=ComplexityLevel.SIMPLE,
            processing_tier=ProcessingTier.TIER_1,
            confidence=0.9,
            extracted_entities=entities
        )
        
        # Check that the entities were extracted correctly
        assert "word" in classified_request.extracted_entities
        assert classified_request.extracted_entities["word"] == "kippu"
        assert "meaning" in classified_request.extracted_entities
        assert classified_request.extracted_entities["meaning"] == "ticket"
    
    def test_integration_with_template_system(self, sample_patterns):
        """Test integration with the template system."""
        from src.ai.companion.tier1.pattern_matching import PatternMatcher
        from src.ai.companion.tier1.template_system import TemplateSystem
        
        matcher = PatternMatcher(patterns=sample_patterns)
        template_system = TemplateSystem()
        
        # Match patterns
        match_result = matcher.match("What does kippu mean?")
        
        # Extract entities
        entities = matcher.extract_entities(match_result)
        
        # Get a template
        template = template_system.get_template(IntentCategory.VOCABULARY_HELP)
        
        # Render the template with extracted entities
        response = template_system.render_template(template, entities)
        
        # Check that the response contains the extracted entities
        assert "kippu" in response
        assert "ticket" in response 