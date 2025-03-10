"""
Tokyo Train Station Adventure - Companion AI Configuration

This module contains configuration settings for the companion AI system.
"""

import os
import yaml
from typing import Dict, Any, Optional

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

def get_config(section: Optional[str] = None, default: Any = None) -> Any:
    """
    Get configuration values from the config file or default values.
    
    Args:
        section: The configuration section to retrieve (e.g., 'tier3.bedrock')
        default: The default value to return if the section is not found
        
    Returns:
        The configuration value for the specified section, or the default value
    """
    # Try to load from the config file
    config_path = os.environ.get('COMPANION_CONFIG', 'config/companion.yaml')
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        else:
            # Use default configuration
            config = {
                "tier1": {"enabled": True},
                "tier2": {
                    "enabled": True,
                    "ollama": {
                        "base_url": "http://localhost:11434",
                        "default_model": "llama3",
                        "complex_model": "llama3:16b",
                        "max_tokens": 500,
                        "temperature": 0.7,
                        "cache_enabled": True,
                        "cache_dir": None,
                        "cache_ttl": 86400,
                        "max_cache_entries": 1000,
                        "max_cache_size_mb": 100,
                        "log_interval": 100
                    }
                },
                "tier3": {
                    "enabled": True,
                    "bedrock": {
                        "region_name": "us-east-1",
                        "default_model": "amazon.nova-micro-v1:0",
                        "models": {
                            "default": "amazon.nova-micro-v1:0",
                            "complex": "amazon.titan-text-express-v1"
                        },
                        "max_tokens": 1000,
                        "temperature": 0.7,
                        "timeout": 30
                    },
                    "prompt_optimizer": {
                        "enabled": True,
                        "max_prompt_tokens": 800,
                        "avg_chars_per_token": 4,
                        "system_prompts": {
                            "low": "You are a helpful bilingual dog companion in a Japanese train station. Provide simple language help.",
                            "medium": "You are a helpful bilingual dog companion in a Japanese train station. Assist with language help, directions, and basic cultural information.",
                            "high": "You are a helpful bilingual dog companion in a Japanese train station. Your role is to assist the player with language help, directions, and cultural information. Provide detailed explanations when appropriate."
                        }
                    },
                    "usage_tracker": {
                        "enabled": True,
                        "storage_path": "data/usage/bedrock_usage.json",
                        "auto_save": True,
                        "daily_token_limit": 100000,
                        "hourly_request_limit": 100,
                        "monthly_cost_limit": 50.0,
                        "cost_per_1k_input_tokens": {
                            "default": 0.001,
                            "amazon.nova-micro-v1:0": 0.0003,
                            "amazon.titan-text-express-v1": 0.0008,
                            "anthropic.claude-3-haiku-20240307-v1:0": 0.00025,
                            "anthropic.claude-3-sonnet-20240229-v1:0": 0.003
                        },
                        "cost_per_1k_output_tokens": {
                            "default": 0.002,
                            "amazon.nova-micro-v1:0": 0.0006,
                            "amazon.titan-text-express-v1": 0.0016,
                            "anthropic.claude-3-haiku-20240307-v1:0": 0.00125,
                            "anthropic.claude-3-sonnet-20240229-v1:0": 0.015
                        }
                    }
                },
                "general": {
                    "log_level": "INFO",
                    "data_dir": "data"
                },
                "retry": {
                    "max_retries": 3,
                    "base_delay": 1.0,
                    "backoff_factor": 2.0,
                    "jitter": True,
                    "jitter_factor": 0.25,
                    "max_delay": 60.0
                }
            }
            
        # If no section is specified, return the entire config
        if section is None:
            return config
            
        # Navigate to the specified section
        parts = section.split('.')
        value = config
        for part in parts:
            if part in value:
                value = value[part]
            else:
                return default
                
        return value
        
    except Exception as e:
        # Log the error and return the default value
        print(f"Error loading configuration: {e}")
        return default 