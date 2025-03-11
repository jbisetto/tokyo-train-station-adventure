"""
Tests for the GrammarTemplateManager class.

This module contains tests for the GrammarTemplateManager class, which is responsible
for managing grammar explanation templates and tracking player interactions with
grammar points.
"""

import pytest
import os
import json
import time
from unittest.mock import patch, MagicMock
from backend.ai.companion.learning.grammar_templates import GrammarTemplateManager, DEFAULT_GRAMMAR_TEMPLATES


@pytest.fixture
def grammar_manager():
    """Create a GrammarTemplateManager instance for testing."""
    return GrammarTemplateManager()


@pytest.fixture
def temp_data_file(tmp_path):
    """Create a temporary file for testing data saving/loading."""
    data_file = tmp_path / "grammar_data_test.json"
    return str(data_file)


class TestGrammarTemplateManager:
    """Tests for the GrammarTemplateManager class."""

    def test_initialization(self, grammar_manager):
        """Test that the manager initializes with default templates."""
        assert grammar_manager.grammar_templates == DEFAULT_GRAMMAR_TEMPLATES
        assert grammar_manager.player_grammar_history == {}
        assert grammar_manager.data_path is None

    def test_get_grammar_template(self, grammar_manager):
        """Test retrieving a grammar template."""
        # Test getting an existing template
        explanation = grammar_manager.get_grammar_template("は vs が")
        assert "は (wa) and が (ga) are both subject markers" in explanation
        assert "Examples:" in explanation
        assert "Common mistakes to avoid:" in explanation
        assert "Practice suggestions:" in explanation

        # Test getting a non-existent template
        explanation = grammar_manager.get_grammar_template("non-existent")
        assert "I don't have specific information about 'non-existent'" in explanation

    def test_get_grammar_examples(self, grammar_manager):
        """Test retrieving examples for a grammar point."""
        # Test getting examples for an existing grammar point
        examples = grammar_manager.get_grammar_examples("は vs が")
        assert len(examples) > 0
        assert "japanese" in examples[0]
        assert "romaji" in examples[0]
        assert "english" in examples[0]

        # Test getting examples for a non-existent grammar point
        examples = grammar_manager.get_grammar_examples("non-existent")
        assert examples == []

    def test_record_grammar_explanation(self, grammar_manager):
        """Test recording that a grammar point was explained."""
        grammar_point = "は vs が"
        
        # Record an explanation
        grammar_manager.record_grammar_explanation(grammar_point)
        
        # Check that the history was updated
        assert grammar_point in grammar_manager.player_grammar_history
        assert grammar_manager.player_grammar_history[grammar_point]["explanation_count"] == 1
        
        # Record another explanation
        grammar_manager.record_grammar_explanation(grammar_point)
        
        # Check that the count was incremented
        assert grammar_manager.player_grammar_history[grammar_point]["explanation_count"] == 2

    def test_add_custom_grammar_template(self, grammar_manager):
        """Test adding a custom grammar template."""
        grammar_point = "custom-grammar"
        template = {
            "explanation": "This is a custom grammar explanation.",
            "examples": [
                {
                    "japanese": "カスタム例文",
                    "romaji": "Kasutamu reibun",
                    "english": "Custom example sentence"
                }
            ]
        }
        
        # Add the custom template
        grammar_manager.add_custom_grammar_template(grammar_point, template)
        
        # Check that the template was added
        assert grammar_point in grammar_manager.grammar_templates
        assert grammar_manager.grammar_templates[grammar_point] == template
        
        # Test that adding a template without an explanation fails
        grammar_manager.add_custom_grammar_template("invalid", {})
        assert "invalid" not in grammar_manager.grammar_templates

    def test_get_all_grammar_points(self, grammar_manager):
        """Test getting a list of all available grammar points."""
        grammar_points = grammar_manager.get_all_grammar_points()
        
        # Check that all default grammar points are included
        for point in DEFAULT_GRAMMAR_TEMPLATES:
            assert point in grammar_points
        
        # Add a custom point and check that it's included
        grammar_manager.add_custom_grammar_template("custom", {"explanation": "test"})
        grammar_points = grammar_manager.get_all_grammar_points()
        assert "custom" in grammar_points

    def test_get_grammar_history(self, grammar_manager):
        """Test getting the player's history with a grammar point."""
        grammar_point = "は vs が"
        
        # Test getting history for a point that hasn't been explained
        history = grammar_manager.get_grammar_history(grammar_point)
        assert history["grammar_point"] == grammar_point
        assert history["explanation_count"] == 0
        assert history["has_template"] is True
        
        # Record an explanation and check the history
        grammar_manager.record_grammar_explanation(grammar_point)
        history = grammar_manager.get_grammar_history(grammar_point)
        assert history["grammar_point"] == grammar_point
        assert history["explanation_count"] == 1
        assert history["has_template"] is True
        assert "first_explained_at" in history
        assert "last_explained_at" in history

    def test_get_frequently_explained_grammar(self, grammar_manager):
        """Test getting the most frequently explained grammar points."""
        # Record explanations with different counts
        grammar_manager.record_grammar_explanation("は vs が")
        grammar_manager.record_grammar_explanation("は vs が")
        grammar_manager.record_grammar_explanation("です/ます form")
        grammar_manager.record_grammar_explanation("て form")
        grammar_manager.record_grammar_explanation("て form")
        grammar_manager.record_grammar_explanation("て form")
        
        # Get the top 2 most frequently explained points
        frequent = grammar_manager.get_frequently_explained_grammar(limit=2)
        assert len(frequent) == 2
        assert frequent[0]["grammar_point"] == "て form"
        assert frequent[0]["explanation_count"] == 3
        assert frequent[1]["grammar_point"] == "は vs が"
        assert frequent[1]["explanation_count"] == 2

    def test_save_and_load_data(self, grammar_manager, temp_data_file):
        """Test saving and loading grammar data."""
        # Record some explanations
        grammar_manager.record_grammar_explanation("は vs が")
        grammar_manager.record_grammar_explanation("て form")
        
        # Add a custom template
        grammar_manager.add_custom_grammar_template("custom", {"explanation": "test"})
        
        # Save the data
        result = grammar_manager.save_data(temp_data_file)
        assert result is True
        assert os.path.exists(temp_data_file)
        
        # Create a new manager and load the data
        new_manager = GrammarTemplateManager()
        result = new_manager.load_data(temp_data_file)
        assert result is True
        
        # Check that the data was loaded correctly
        assert "は vs が" in new_manager.player_grammar_history
        assert "て form" in new_manager.player_grammar_history
        assert "custom" in new_manager.grammar_templates
        
        # Check that the explanation counts match
        assert new_manager.player_grammar_history["は vs が"]["explanation_count"] == 1
        assert new_manager.player_grammar_history["て form"]["explanation_count"] == 1

    def test_save_data_no_path(self, grammar_manager):
        """Test that saving fails when no path is provided."""
        result = grammar_manager.save_data()
        assert result is False

    def test_load_data_no_path(self, grammar_manager):
        """Test that loading fails when no path is provided."""
        result = grammar_manager.load_data()
        assert result is False

    def test_load_data_file_not_found(self, grammar_manager, temp_data_file):
        """Test that loading fails when the file doesn't exist."""
        result = grammar_manager.load_data(temp_data_file + ".nonexistent")
        assert result is False

    @patch("json.load")
    def test_load_data_exception(self, mock_json_load, grammar_manager, temp_data_file):
        """Test that loading handles exceptions gracefully."""
        # Create an empty file
        with open(temp_data_file, 'w') as f:
            f.write("")
        
        # Make json.load raise an exception
        mock_json_load.side_effect = Exception("Test exception")
        
        # Try to load the data
        result = grammar_manager.load_data(temp_data_file)
        assert result is False

    @patch("json.dump")
    def test_save_data_exception(self, mock_json_dump, grammar_manager, temp_data_file):
        """Test that saving handles exceptions gracefully."""
        # Make json.dump raise an exception
        mock_json_dump.side_effect = Exception("Test exception")
        
        # Try to save the data
        result = grammar_manager.save_data(temp_data_file)
        assert result is False 