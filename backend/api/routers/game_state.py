"""
Router for game state endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Optional

from backend.api.adapters.base import AdapterFactory
from backend.api.models.game_state import (
    SaveGameStateRequest,
    SaveGameStateResponse,
    LoadGameStateResponse,
    ListSavedGamesResponse,
    ErrorResponse
)
from backend.data.game_state import (
    save_game_state,
    load_game_state,
    list_saved_games,
    InvalidPlayerIdError,
    PlayerNotFoundError,
    SaveNotFoundError
)

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/game/state",
    tags=["game-state"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)


@router.post(
    "",
    response_model=SaveGameStateResponse,
    summary="Save the current game state",
    description="Save the current game state for a player"
)
async def save_game(
    request: SaveGameStateRequest
) -> SaveGameStateResponse:
    """
    Save the current game state.
    
    Args:
        request: The save game state request.
        
    Returns:
        A response containing the save ID and timestamp.
        
    Raises:
        HTTPException: If an error occurs while saving the game state.
    """
    try:
        logger.info(f"Saving game state for player {request.playerId}")
        
        # Get the request adapter
        request_adapter = AdapterFactory.get_request_adapter("save_game_state")
        
        # Transform request to internal format
        internal_request = request_adapter.adapt(request.dict())
        
        # Save the game state
        result = save_game_state(internal_request)
        
        # Get the response adapter
        response_adapter = AdapterFactory.get_response_adapter("save_game_state")
        
        # Transform result to API format
        response_data = response_adapter.adapt(result)
        
        logger.info(f"Game state saved successfully with save ID {response_data['saveId']}")
        
        return response_data
        
    except InvalidPlayerIdError as e:
        logger.error(f"Invalid player ID: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid player ID format: {request.playerId}"
        )
    except Exception as e:
        logger.error(f"Error saving game state: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while saving the game state"
        )


@router.get(
    "/{player_id}",
    response_model=LoadGameStateResponse,
    summary="Load a saved game state",
    description="Load a saved game state for a player"
)
async def load_game(
    player_id: str = Path(..., description="The ID of the player"),
    save_id: Optional[str] = Query(None, description="The ID of the save to load")
) -> LoadGameStateResponse:
    """
    Load a saved game state.
    
    Args:
        player_id: The ID of the player.
        save_id: The ID of the save to load. If not provided, the most recent save is loaded.
        
    Returns:
        The loaded game state.
        
    Raises:
        HTTPException: If an error occurs while loading the game state.
    """
    try:
        logger.info(f"Loading game state for player {player_id}" + 
                   (f" with save ID {save_id}" if save_id else " (most recent)"))
        
        # Load the game state
        result = load_game_state(player_id, save_id)
        
        # Get the response adapter
        response_adapter = AdapterFactory.get_response_adapter("load_game_state")
        
        # Transform result to API format
        response_data = response_adapter.adapt(result)
        
        logger.info(f"Game state loaded successfully for player {player_id}")
        
        return response_data
        
    except InvalidPlayerIdError as e:
        logger.error(f"Invalid player ID: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid player ID format: {player_id}"
        )
    except PlayerNotFoundError as e:
        logger.error(f"Player not found: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Player with ID {player_id} not found"
        )
    except SaveNotFoundError as e:
        logger.error(f"Save not found: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Save not found for player {player_id}" + 
                  (f" with save ID {save_id}" if save_id else "")
        )
    except Exception as e:
        logger.error(f"Error loading game state: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while loading the game state"
        )


@router.get(
    "/saves/{player_id}",
    response_model=ListSavedGamesResponse,
    summary="List saved games",
    description="List all saved games for a player"
)
async def list_saves(
    player_id: str = Path(..., description="The ID of the player")
) -> ListSavedGamesResponse:
    """
    List all saved games for a player.
    
    Args:
        player_id: The ID of the player.
        
    Returns:
        A list of saved games for the player.
        
    Raises:
        HTTPException: If an error occurs while listing the saved games.
    """
    try:
        logger.info(f"Listing saved games for player {player_id}")
        
        # List saved games
        result = list_saved_games(player_id)
        
        # Get the response adapter
        response_adapter = AdapterFactory.get_response_adapter("list_saved_games")
        
        # Transform result to API format
        response_data = response_adapter.adapt(result)
        
        logger.info(f"Listed {len(response_data['saves'])} saved games for player {player_id}")
        
        return response_data
        
    except InvalidPlayerIdError as e:
        logger.error(f"Invalid player ID: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid player ID format: {player_id}"
        )
    except PlayerNotFoundError as e:
        logger.error(f"Player not found: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Player with ID {player_id} not found"
        )
    except Exception as e:
        logger.error(f"Error listing saved games: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while listing saved games"
        ) 