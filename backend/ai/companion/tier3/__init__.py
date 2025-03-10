"""
Tokyo Train Station Adventure - Tier 3 Module

This module provides integration with cloud-based language models for the companion AI system.
It includes clients for Amazon Bedrock and other cloud APIs.
"""

from backend.ai.companion.tier3.bedrock_client import BedrockClient, BedrockError
from backend.ai.companion.tier3.tier3_processor import Tier3Processor
from backend.ai.companion.tier3.usage_tracker import UsageTracker, default_tracker
from backend.ai.companion.tier3.prompt_optimizer import PromptOptimizer, create_optimized_prompt

__all__ = [
    'BedrockClient', 
    'BedrockError', 
    'Tier3Processor',
    'UsageTracker',
    'default_tracker',
    'PromptOptimizer',
    'create_optimized_prompt'
] 