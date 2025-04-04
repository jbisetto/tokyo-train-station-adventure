#!/usr/bin/env python3
"""
Complete Integration Test for DeepSeek-R1 with Ollama

This test demonstrates processing a request through the entire system,
starting with request classification, tier2 processing, and API response formatting.
"""

import os
import sys
import asyncio
import logging
import json
from typing import Dict, Any

# Add the repository root to the Python path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.ai.companion.core.models import (
    CompanionRequest, 
    GameContext, 
    ProcessingTier,
    ComplexityLevel,
    IntentCategory
)
from src.ai.companion.core.request_handler import RequestHandler
from src.ai.companion.tier2.tier2_processor import Tier2Processor
from src.ai.companion.api.response_adapter import ResponseAdapter
from src.ai.companion.config import get_config


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


async def test_full_request_processing():
    """Process a request through the complete system pipeline."""
    logger.info("Starting full request processing integration test")
    
    # 1. Ensure tier2 is enabled in the configuration
    config = get_config()
    tier2_config = config.get('tier2', {})
    if not tier2_config.get('enabled', False):
        logger.warning("Tier 2 is not enabled in the configuration. Test may not use Ollama.")
    
    # 2. Create a sample game context
    game_context = GameContext(
        player_location="Tokyo Station",
        current_objective="Find the JR Yamanote Line platform",
        nearby_npcs=["Station Attendant", "Shopkeeper"],
        nearby_objects=["Train Schedule", "Ticket Gate", "Vending Machine"],
        player_inventory=["Suica Card", "Tourism Map", "Phrase Book"],
        language_proficiency={"japanese": 0.3}
    )
    
    # 3. Create a companion request
    request = CompanionRequest(
        request_id="test-integration-123",
        player_input="How do I ask where the Yamanote Line platform is in Japanese?",
        request_type="language_help",
        game_context=game_context,
        additional_params={
            "conversation_id": "test-conversation-456",
            "preferred_tier": ProcessingTier.TIER_2.value
        }
    )
    
    # 4. Create request handler
    handler = RequestHandler()
    
    logger.info(f"Processing request: {request.request_id} - '{request.player_input}'")
    
    # 5. Process the request
    try:
        response_data = await handler.process_request(request)
        
        # 6. Format API response
        adapter = ResponseAdapter()
        api_response = adapter.format_response(response_data)
        
        # 7. Log and verify results
        logger.info("Request processing succeeded")
        logger.info(f"Processing tier used: {api_response['metadata']['processing_tier']}")
        
        # 8. Display the response
        logger.info(f"Response text: {api_response['text'][:200]}...")
        
        # 9. Verify tier was properly passed through
        processing_tier = api_response['metadata'].get('processing_tier')
        
        # This is a test success if:
        # - We got a non-empty response
        # - The processing_tier is properly included in the metadata
        if api_response['text'] and processing_tier in ['TIER_1', 'TIER_2', 'TIER_3', 'RULE']:
            logger.info("✅ Integration test PASSED")
            return True
        else:
            logger.error("❌ Integration test FAILED: Invalid response format")
            return False
            
    except Exception as e:
        logger.error(f"❌ Integration test FAILED with error: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_full_request_processing()) 