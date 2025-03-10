"""
Tokyo Train Station Adventure - Companion AI Configuration

This module contains configuration settings for the companion AI system.
"""

# Tiered processing configuration
TIER_CONFIG = {
    "tier1_threshold": 0.7,  # Percentage of requests to handle with rule-based system
    "tier2_threshold": 0.2,  # Percentage of requests to handle with local LLM
    "tier3_threshold": 0.1,  # Percentage of requests to handle with cloud API
}

# Intent categories
INTENT_CATEGORIES = [
    "vocabulary_help",      # Assistance with specific words
    "grammar_explanation",  # Explanation of grammar patterns
    "direction_guidance",   # Help navigating the station
    "translation_confirmation",  # Verification of player's translation
    "general_hint",         # Suggestions on what to do next
]

# Complexity levels
COMPLEXITY_LEVELS = [
    "simple",    # Common requests with clear patterns (→ Tier 1)
    "moderate",  # Less common requests with some variation (→ Tier 2)
    "complex",   # Novel or highly specific requests (→ Tier 3)
]

# Companion personality traits
PERSONALITY_TRAITS = {
    "friendliness": 0.8,    # How friendly the companion is (0-1)
    "helpfulness": 0.9,     # How helpful the companion is (0-1)
    "patience": 0.7,        # How patient the companion is (0-1)
    "enthusiasm": 0.6,      # How enthusiastic the companion is (0-1)
}

# Local model configuration
LOCAL_MODEL_CONFIG = {
    "model_name": "deepseek-coder:7b",
    "max_tokens": 256,
    "temperature": 0.7,
    "top_p": 0.9,
    "cache_size": 100,  # Number of responses to cache
}

# Cloud API configuration
CLOUD_API_CONFIG = {
    "service": "bedrock",
    "model": "anthropic.claude-3-haiku-20240307-v1:0",
    "max_tokens": 512,
    "temperature": 0.7,
    "top_p": 0.9,
    "daily_quota": 100,  # Maximum number of API calls per day
}

# Logging configuration
LOGGING_CONFIG = {
    "log_level": "INFO",
    "log_file": "companion_ai.log",
    "enable_request_logging": True,
    "enable_response_logging": True,
} 