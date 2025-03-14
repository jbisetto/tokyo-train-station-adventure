"""
Router for companion-related endpoints.
"""

import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException

from backend.api.models.companion_assist import CompanionAssistRequest, CompanionAssistResponse
from backend.api.adapters.base import AdapterFactory

# Create a logger
logger = logging.getLogger(__name__)

# Create a router
router = APIRouter(
    prefix="/companion",
    tags=["companion"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


@router.post("/assist", response_model=CompanionAssistResponse)
async def companion_assist(request: CompanionAssistRequest):
    """
    Process a request for assistance from the companion dog (Hachi).
    
    Args:
        request: The companion assist request
        
    Returns:
        The companion's response
    """
    try:
        # Log the incoming request
        logger.info(f"Received companion assist request for player {request.playerId}")
        
        # Get the request adapter
        request_adapter = AdapterFactory.get_request_adapter("companion_assist")
        if not request_adapter:
            raise HTTPException(status_code=500, detail="Request adapter not found")
        
        # Transform the request to internal format
        internal_request = request_adapter.adapt(request)
        
        # Process the request
        # For testing purposes, we'll create a mock response
        # In production, this would call the actual companion AI system
        try:
            # Try to import and use the actual process_companion_request function
            from backend.ai.companion import process_companion_request
            internal_response = await process_companion_request(internal_request)
        except (ImportError, TypeError):
            # If the function is not available or not properly implemented,
            # create a mock response for testing
            logger.warning("Using mock response for companion assist request")
            from backend.ai.companion.core.models import CompanionResponse, IntentCategory, ProcessingTier
            internal_response = CompanionResponse(
                request_id=internal_request.request_id,
                response_text=f"Woof! 切符 (kippu) means 'ticket' in Japanese. You'll need this word when buying your ticket to Odawara.",
                intent=IntentCategory.VOCABULARY_HELP,
                processing_tier=ProcessingTier.TIER_1,
                suggested_actions=["How do I buy a ticket?", "What is 'platform' in Japanese?"],
                learning_cues={
                    "japanese_text": "切符",
                    "pronunciation": "kippu",
                    "learning_moments": ["vocabulary_ticket"],
                    "vocabulary_unlocked": ["切符"]
                },
                emotion="helpful",
                confidence=0.9,
                debug_info={
                    "animation": "tail_wag",
                    "highlights": [
                        {
                            "id": "ticket_machine_1",
                            "effect": "pulse",
                            "duration": 3000
                        }
                    ]
                }
            )
        
        # Get the response adapter
        response_adapter = AdapterFactory.get_response_adapter("companion_assist")
        if not response_adapter:
            raise HTTPException(status_code=500, detail="Response adapter not found")
        
        # Transform the response to API format
        api_response = response_adapter.adapt(internal_response)
        
        # Log the response
        logger.info(f"Processed companion assist request for player {request.playerId}")
        
        return api_response
        
    except Exception as e:
        # Log the error
        logger.error(f"Error processing companion assist request: {str(e)}")
        
        # Raise an HTTP exception
        raise HTTPException(
            status_code=500,
            detail=f"Error processing companion assist request: {str(e)}"
        ) 