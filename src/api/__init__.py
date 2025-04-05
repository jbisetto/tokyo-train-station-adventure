"""
API package for the Tokyo Train Station Adventure game.
"""

from fastapi import FastAPI
from src.api.routers import api_router
from src.api.middleware import setup_middleware


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        The configured FastAPI application
    """
    # Create the application
    app = FastAPI(
        title="Tokyo Train Station Adventure API",
        description="API for the Tokyo Train Station Adventure game",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )
    
    # Set up middleware
    setup_middleware(app)
    
    # Include the API router
    app.include_router(api_router)
    
    # Add a health check endpoint
    @app.get("/health")
    async def health_check():
        """
        Health check endpoint.
        
        Returns:
            A simple status message
        """
        return {"status": "ok"}
    
    return app 