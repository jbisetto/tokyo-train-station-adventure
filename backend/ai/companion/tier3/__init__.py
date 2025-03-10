"""
Tokyo Train Station Adventure - Tier 3 Module

This module provides integration with cloud-based language models for the companion AI system.
It includes clients for Amazon Bedrock and other cloud APIs.
"""

from backend.ai.companion.tier3.bedrock_client import BedrockClient, BedrockError

__all__ = ['BedrockClient', 'BedrockError'] 