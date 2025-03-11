"""
Tests for the LearningPaceAdapter class.

This module contains tests for the LearningPaceAdapter class, which is responsible
for adapting the learning pace based on player performance, preferences, and
interaction patterns.
"""

import pytest
import os
import json
import time
from unittest.mock import patch, MagicMock
from backend.ai.companion.learning.learning_pace import LearningPaceAdapter, DEFAULT_LEARNING_PACE


@pytest.fixture
def pace_adapter():
    """Create a LearningPaceAdapter instance for testing."""
    return LearningPaceAdapter()


@pytest.fixture
def temp_data_file(tmp_path):
    """Create a temporary file for testing data saving/loading."""
    data_file = tmp_path / "learning_pace_test.json"
    return str(data_file)


@pytest.fixture
def sample_session_data():
    """Create sample session data for testing."""
    return {
        "vocabulary_correct": 8,
        "vocabulary_total": 10,
        "grammar_correct": 3,
        "grammar_total": 5,
        "challenges_completed": 2,
        "challenges_attempted": 3,
        "hints_used": 4,
        "hints_available": 10,
        "response_times": [2.5, 3.0, 1.5, 2.0]
    }


class TestLearningPaceAdapter:
    """Tests for the LearningPaceAdapter class."""

    def test_initialization(self, pace_adapter):
        """Test that the adapter initializes with default settings."""
        assert pace_adapter.learning_pace == DEFAULT_LEARNING_PACE
        assert pace_adapter.performance_metrics["vocabulary_mastery_rate"] == 0.0
        assert pace_adapter.performance_metrics["grammar_understanding_rate"] == 0.0
        assert pace_adapter.performance_metrics["challenge_success_rate"] == 0.0
        assert pace_adapter.performance_metrics["hint_usage_rate"] == 0.0
        assert pace_adapter.session_history == []
        assert pace_adapter.data_path is None

    def test_update_performance_metric(self, pace_adapter):
        """Test updating a performance metric."""
        # Test updating a valid metric
        pace_adapter.update_performance_metric("vocabulary_mastery_rate", 0.8)
        assert pace_adapter.performance_metrics["vocabulary_mastery_rate"] == 0.8
        
        # Test updating with a value outside the valid range (should be clamped)
        pace_adapter.update_performance_metric("grammar_understanding_rate", 1.5)
        assert pace_adapter.performance_metrics["grammar_understanding_rate"] == 1.0
        
        pace_adapter.update_performance_metric("challenge_success_rate", -0.5)
        assert pace_adapter.performance_metrics["challenge_success_rate"] == 0.0
        
        # Test updating a non-rate metric
        pace_adapter.update_performance_metric("average_response_time", 3.5)
        assert pace_adapter.performance_metrics["average_response_time"] == 3.5
        
        # Test updating an invalid metric (should not add a new metric)
        pace_adapter.update_performance_metric("invalid_metric", 0.5)
        assert "invalid_metric" not in pace_adapter.performance_metrics

    def test_record_session_performance(self, pace_adapter, sample_session_data):
        """Test recording session performance data."""
        # Record session performance
        pace_adapter.record_session_performance(sample_session_data)
        
        # Check that session was added to history
        assert len(pace_adapter.session_history) == 1
        assert "timestamp" in pace_adapter.session_history[0]
        
        # Check that performance metrics were updated
        assert pace_adapter.performance_metrics["vocabulary_mastery_rate"] == 0.8  # 8/10
        assert pace_adapter.performance_metrics["grammar_understanding_rate"] == 0.6  # 3/5
        assert pace_adapter.performance_metrics["challenge_success_rate"] == 2/3  # 2/3
        assert pace_adapter.performance_metrics["hint_usage_rate"] == 0.4  # 4/10
        assert pace_adapter.performance_metrics["average_response_time"] == 2.25  # (2.5+3.0+1.5+2.0)/4

    def test_adapt_learning_pace(self, pace_adapter):
        """Test that learning pace adapts based on performance metrics."""
        # Set up performance metrics
        pace_adapter.update_performance_metric("vocabulary_mastery_rate", 0.9)  # High mastery
        pace_adapter.update_performance_metric("grammar_understanding_rate", 0.3)  # Low understanding
        pace_adapter.update_performance_metric("challenge_success_rate", 0.8)  # High success
        pace_adapter.update_performance_metric("hint_usage_rate", 0.2)  # Low hint usage
        
        # Add enough session history to trigger adaptation
        for i in range(3):
            pace_adapter.session_history.append({"timestamp": time.time()})
        
        # Manually trigger adaptation
        pace_adapter._adapt_learning_pace()
        
        # Check that pace was adapted correctly
        assert pace_adapter.learning_pace["vocabulary_per_session"] > DEFAULT_LEARNING_PACE["vocabulary_per_session"]
        assert pace_adapter.learning_pace["grammar_points_per_session"] < DEFAULT_LEARNING_PACE["grammar_points_per_session"]
        assert pace_adapter.learning_pace["difficulty_level"] > DEFAULT_LEARNING_PACE["difficulty_level"]
        assert pace_adapter.learning_pace["hint_progression_speed"] > DEFAULT_LEARNING_PACE["hint_progression_speed"]

    def test_get_learning_pace(self, pace_adapter):
        """Test getting the current learning pace settings."""
        # Get the learning pace
        pace = pace_adapter.get_learning_pace()
        
        # Check that it matches the default
        assert pace == DEFAULT_LEARNING_PACE
        
        # Check that it's a copy (modifying it doesn't affect the original)
        pace["vocabulary_per_session"] = 10
        assert pace_adapter.learning_pace["vocabulary_per_session"] == DEFAULT_LEARNING_PACE["vocabulary_per_session"]

    def test_set_learning_pace_parameter(self, pace_adapter):
        """Test setting a specific learning pace parameter."""
        # Test setting a valid integer parameter
        result = pace_adapter.set_learning_pace_parameter("vocabulary_per_session", 8)
        assert result is True
        assert pace_adapter.learning_pace["vocabulary_per_session"] == 8
        
        # Test setting a valid float parameter
        result = pace_adapter.set_learning_pace_parameter("difficulty_level", 0.75)
        assert result is True
        assert pace_adapter.learning_pace["difficulty_level"] == 0.75
        
        # Test setting an invalid parameter (non-existent)
        result = pace_adapter.set_learning_pace_parameter("non_existent", 5)
        assert result is False
        
        # Test setting an invalid value for an integer parameter
        result = pace_adapter.set_learning_pace_parameter("vocabulary_per_session", -1)
        assert result is False
        assert pace_adapter.learning_pace["vocabulary_per_session"] == 8  # Unchanged
        
        # Test setting an invalid value for a float parameter
        result = pace_adapter.set_learning_pace_parameter("difficulty_level", 1.5)
        assert result is False
        assert pace_adapter.learning_pace["difficulty_level"] == 0.75  # Unchanged

    def test_get_recommended_content(self, pace_adapter):
        """Test getting recommended learning content."""
        # Get recommendations
        recommendations = pace_adapter.get_recommended_content()
        
        # Check that recommendations include expected keys
        assert "vocabulary_count" in recommendations
        assert "grammar_points_count" in recommendations
        assert "should_review" in recommendations
        assert "difficulty_level" in recommendations
        assert "explanation_detail" in recommendations
        assert "include_challenge" in recommendations
        assert "hint_level" in recommendations
        
        # Check that values match expectations
        assert recommendations["vocabulary_count"] == pace_adapter.learning_pace["vocabulary_per_session"]
        assert recommendations["grammar_points_count"] == pace_adapter.learning_pace["grammar_points_per_session"]
        assert recommendations["difficulty_level"] == pace_adapter.learning_pace["difficulty_level"]
        assert recommendations["explanation_detail"] == pace_adapter.learning_pace["explanation_detail"]
        
        # Check that hint level is between 1 and 3
        assert 1 <= recommendations["hint_level"] <= 3

    @patch("random.random")
    def test_should_include_challenge(self, mock_random, pace_adapter):
        """Test determining if a challenge should be included."""
        # Add a session to history
        pace_adapter.session_history.append({"timestamp": time.time()})
        
        # Set challenge frequency
        pace_adapter.learning_pace["challenge_frequency"] = 0.7  # High frequency
        
        # Test when random value is below threshold (should include challenge)
        mock_random.return_value = 0.2
        assert pace_adapter._should_include_challenge() is True
        
        # Test when random value is above threshold (should not include challenge)
        mock_random.return_value = 0.4
        assert pace_adapter._should_include_challenge() is False
        
        # Test with no session history (should always return False)
        pace_adapter.session_history = []
        assert pace_adapter._should_include_challenge() is False

    def test_calculate_hint_level(self, pace_adapter):
        """Test calculating the appropriate hint level."""
        # Test with high hint usage and slow progression (should return level 1)
        pace_adapter.performance_metrics["hint_usage_rate"] = 0.8
        pace_adapter.learning_pace["hint_progression_speed"] = 0.2
        assert pace_adapter._calculate_hint_level() == 1
        
        # Test with medium hint usage and medium progression (should return level 2)
        pace_adapter.performance_metrics["hint_usage_rate"] = 0.5
        pace_adapter.learning_pace["hint_progression_speed"] = 0.5
        assert pace_adapter._calculate_hint_level() == 2
        
        # Test with low hint usage and fast progression (should return level 3)
        pace_adapter.performance_metrics["hint_usage_rate"] = 0.3
        pace_adapter.learning_pace["hint_progression_speed"] = 0.8
        assert pace_adapter._calculate_hint_level() == 3

    def test_get_performance_summary(self, pace_adapter):
        """Test getting a summary of player performance."""
        # Test with no session history
        summary = pace_adapter.get_performance_summary()
        assert summary["sessions_completed"] == 0
        assert summary["overall_performance"] == 0.0
        assert summary["strengths"] == []
        assert summary["areas_for_improvement"] == []
        
        # Add session history and set performance metrics
        pace_adapter.session_history.append({"timestamp": time.time()})
        pace_adapter.update_performance_metric("vocabulary_mastery_rate", 0.8)  # Strength
        pace_adapter.update_performance_metric("grammar_understanding_rate", 0.4)  # Area for improvement
        pace_adapter.update_performance_metric("challenge_success_rate", 0.6)  # Neither
        
        # Get summary again
        summary = pace_adapter.get_performance_summary()
        assert summary["sessions_completed"] == 1
        assert summary["overall_performance"] == (0.8 + 0.4 + 0.6) / 3
        assert "vocabulary" in summary["strengths"]
        assert "grammar" in summary["areas_for_improvement"]
        assert "challenges" not in summary["strengths"]
        assert "challenges" not in summary["areas_for_improvement"]
        assert "current_pace" in summary

    def test_reset_to_defaults(self, pace_adapter):
        """Test resetting learning pace to default settings."""
        # Change some settings
        pace_adapter.learning_pace["vocabulary_per_session"] = 10
        pace_adapter.learning_pace["difficulty_level"] = 0.9
        
        # Reset to defaults
        pace_adapter.reset_to_defaults()
        
        # Check that settings were reset
        assert pace_adapter.learning_pace == DEFAULT_LEARNING_PACE

    def test_save_and_load_data(self, pace_adapter, temp_data_file, sample_session_data):
        """Test saving and loading learning pace data."""
        # Set up some data
        pace_adapter.record_session_performance(sample_session_data)
        pace_adapter.learning_pace["vocabulary_per_session"] = 7
        
        # Save the data
        result = pace_adapter.save_data(temp_data_file)
        assert result is True
        assert os.path.exists(temp_data_file)
        
        # Create a new adapter and load the data
        new_adapter = LearningPaceAdapter()
        result = new_adapter.load_data(temp_data_file)
        assert result is True
        
        # Check that the data was loaded correctly
        assert new_adapter.learning_pace["vocabulary_per_session"] == 7
        assert len(new_adapter.session_history) == 1
        assert new_adapter.performance_metrics["vocabulary_mastery_rate"] == 0.8

    def test_save_data_no_path(self, pace_adapter):
        """Test that saving fails when no path is provided."""
        result = pace_adapter.save_data()
        assert result is False

    def test_load_data_no_path(self, pace_adapter):
        """Test that loading fails when no path is provided."""
        result = pace_adapter.load_data()
        assert result is False

    def test_load_data_file_not_found(self, pace_adapter, temp_data_file):
        """Test that loading fails when the file doesn't exist."""
        result = pace_adapter.load_data(temp_data_file + ".nonexistent")
        assert result is False

    @patch("json.load")
    def test_load_data_exception(self, mock_json_load, pace_adapter, temp_data_file):
        """Test that loading handles exceptions gracefully."""
        # Create an empty file
        with open(temp_data_file, 'w') as f:
            f.write("")
        
        # Make json.load raise an exception
        mock_json_load.side_effect = Exception("Test exception")
        
        # Try to load the data
        result = pace_adapter.load_data(temp_data_file)
        assert result is False

    @patch("json.dump")
    def test_save_data_exception(self, mock_json_dump, pace_adapter, temp_data_file):
        """Test that saving handles exceptions gracefully."""
        # Make json.dump raise an exception
        mock_json_dump.side_effect = Exception("Test exception")
        
        # Try to save the data
        result = pace_adapter.save_data(temp_data_file)
        assert result is False 