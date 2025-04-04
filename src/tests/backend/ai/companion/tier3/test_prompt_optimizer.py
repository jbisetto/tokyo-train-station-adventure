"""
Tests for the prompt optimizer module.

This module contains tests for the prompt optimizer, which is used
to create cost-effective prompts for Amazon Bedrock.
"""

import pytest
from unittest.mock import patch

from src.ai.companion.core.models import CompanionRequest
from src.ai.companion.tier3.prompt_optimizer import (
    PromptOptimizer, 
    get_system_prompt, 
    create_optimized_prompt,
    SYSTEM_PROMPTS
)


@pytest.fixture
def sample_request():
    """Create a sample request for testing."""
    return CompanionRequest(
        request_id="test-123",
        player_input="How do I say 'I want to go to Tokyo' in Japanese?",
        request_type="language_help",
        timestamp="2025-03-10T18:35:30.927478",
        additional_params={"complexity": "high"}
    )


@pytest.fixture
def long_request():
    """Create a sample request with a long input for testing."""
    long_input = "I'm trying to find my way to the Tokyo Tower, but I'm lost. " * 20
    return CompanionRequest(
        request_id="test-456",
        player_input=long_input,
        request_type="directions",
        timestamp="2025-03-10T18:35:30.927478",
        additional_params={"complexity": "medium"}
    )


class TestPromptOptimizer:
    """Tests for the PromptOptimizer class."""
    
    def test_initialization(self):
        """Test initialization of the PromptOptimizer."""
        optimizer = PromptOptimizer()
        
        # Check default values
        assert optimizer.max_prompt_tokens == 800
        
        # Test with custom values
        custom_optimizer = PromptOptimizer(max_prompt_tokens=500)
        assert custom_optimizer.max_prompt_tokens == 500
    
    def test_estimate_tokens(self):
        """Test token estimation."""
        optimizer = PromptOptimizer()
        
        # Test with various text lengths
        assert optimizer.estimate_tokens("") == 1  # Minimum is 1
        assert optimizer.estimate_tokens("Hello") == 1  # Short text
        
        # Test with longer text
        long_text = "This is a longer text that should be more than 4 tokens." * 10
        estimated = optimizer.estimate_tokens(long_text)
        assert estimated > 10  # Should be significantly more than 10 tokens
        
        # Check that estimation is based on character count
        text_20_chars = "a" * 20
        assert optimizer.estimate_tokens(text_20_chars) == 5  # 20 / 4 = 5
    
    def test_optimize_prompt_short_input(self, sample_request):
        """Test optimizing a prompt with short input."""
        optimizer = PromptOptimizer()
        system_prompt = "You are a helpful assistant."
        
        # With short input, should use full prompt
        optimized = optimizer.optimize_prompt(sample_request, system_prompt)
        
        # Check that the optimized prompt contains both system prompt and input
        assert system_prompt in optimized
        assert sample_request.player_input in optimized
        assert "The player has asked:" in optimized
    
    def test_optimize_prompt_long_input(self, long_request):
        """Test optimizing a prompt with long input."""
        optimizer = PromptOptimizer(max_prompt_tokens=50)  # Small limit to force compression
        system_prompt = "You are a helpful assistant. " * 10  # Make it longer
        
        # With long input and small token limit, should compress
        optimized = optimizer.optimize_prompt(long_request, system_prompt)
        
        # Check that the optimized prompt is compressed
        assert len(optimized) < len(system_prompt) + len(long_request.player_input) + 50
        assert long_request.player_input in optimized
        assert "Query:" in optimized
    
    def test_compress_text(self):
        """Test text compression."""
        optimizer = PromptOptimizer()
        
        # Test with filler words
        text_with_fillers = "This is very really quite just simply basically actually important."
        compressed = optimizer._compress_text(text_with_fillers)
        
        # Check that filler words are removed
        assert "very" not in compressed
        assert "really" not in compressed
        assert "quite" not in compressed
        assert "just" not in compressed
        assert "simply" not in compressed
        assert "basically" not in compressed
        assert "actually" not in compressed
        
        # Test with common phrases
        text_with_phrases = "In order to succeed, due to the fact that effort is required."
        compressed = optimizer._compress_text(text_with_phrases)
        
        # Check that phrases are simplified
        assert "due to the fact that" not in compressed
        assert "because" in compressed
    
    def test_truncate_to_tokens(self):
        """Test truncation to token limit."""
        optimizer = PromptOptimizer()
        
        # Create a text with multiple sentences
        text = "This is the first sentence. This is the second sentence. This is the third sentence."
        
        # Truncate to a small number of tokens
        truncated = optimizer._truncate_to_tokens(text, 5)
        
        # Should truncate based on token limit
        assert len(truncated) <= 5 * 4  # 5 tokens * 4 chars per token
        
        # Test with very small limit that can't fit a sentence
        very_truncated = optimizer._truncate_to_tokens(text, 2)
        assert len(very_truncated) <= 2 * 4  # 2 tokens * 4 chars per token
    
    def test_create_full_prompt(self):
        """Test creating a full prompt."""
        optimizer = PromptOptimizer()
        system_prompt = "You are a helpful assistant."
        player_input = "How do I get to Tokyo Tower?"
        
        prompt = optimizer._create_full_prompt(system_prompt, player_input)
        
        # Check format
        assert prompt == f"{system_prompt} The player has asked: \"{player_input}\""
    
    def test_create_compressed_prompt(self):
        """Test creating a compressed prompt."""
        optimizer = PromptOptimizer()
        system_prompt = "You are a helpful assistant."
        player_input = "How do I get to Tokyo Tower?"
        
        prompt = optimizer._create_compressed_prompt(system_prompt, player_input)
        
        # Check format
        assert "Query:" in prompt
        assert player_input in prompt


def test_get_system_prompt(sample_request):
    """Test getting a system prompt based on complexity."""
    # Test with high complexity
    high_prompt = get_system_prompt(sample_request)
    assert high_prompt == SYSTEM_PROMPTS["high"]
    
    # Test with medium complexity
    sample_request.additional_params["complexity"] = "medium"
    medium_prompt = get_system_prompt(sample_request)
    assert medium_prompt == SYSTEM_PROMPTS["medium"]
    
    # Test with low complexity
    sample_request.additional_params["complexity"] = "low"
    low_prompt = get_system_prompt(sample_request)
    assert low_prompt == SYSTEM_PROMPTS["low"]
    
    # Test with invalid complexity (should default to medium)
    sample_request.additional_params["complexity"] = "invalid"
    default_prompt = get_system_prompt(sample_request)
    assert default_prompt == SYSTEM_PROMPTS["medium"]


def test_create_optimized_prompt(sample_request):
    """Test creating an optimized prompt."""
    # Test with default parameters
    prompt = create_optimized_prompt(sample_request)
    
    # Should contain the player input
    assert sample_request.player_input in prompt
    
    # Should use the high complexity prompt (from the request)
    assert "detailed explanations" in prompt
    
    # Test with custom max tokens
    custom_prompt = create_optimized_prompt(sample_request, max_tokens=100)
    assert sample_request.player_input in custom_prompt 