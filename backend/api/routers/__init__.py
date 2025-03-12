"""
API routers package.
"""

from fastapi import APIRouter
from backend.api.routers.companion import router as companion_router
from backend.api.routers.dialogue import router as dialogue_router

# Create the main API router
api_router = APIRouter(
    prefix="/api",
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

# Include the companion router
api_router.include_router(companion_router)

# Include the dialogue router
api_router.include_router(dialogue_router)

# Add a root endpoint
@api_router.get("/")
async def api_root():
    """
    Root endpoint for the API.
    
    Returns:
        Basic API information
    """
    return {
        "name": "Tokyo Train Station Adventure API",
        "version": "0.1.0",
        "description": "API for the Tokyo Train Station Adventure game"
    } 