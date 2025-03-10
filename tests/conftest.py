"""
Tokyo Train Station Adventure - Test Configuration

This module contains pytest fixtures and configuration for testing.
"""

import pytest
import sys
import os

# Add the project root to the Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Fixtures that can be used across all tests
@pytest.fixture
def sample_game_context():
    """Provide a sample game context for testing."""
    from backend.ai.companion.core.models import GameContext
    
    return GameContext(
        player_location="main_concourse",
        current_objective="find_ticket_machine",
        nearby_npcs=["station_attendant", "tourist"],
        nearby_objects=["information_board", "ticket_machine"],
        player_inventory=["wallet", "phone"],
        language_proficiency={"vocabulary": 0.4, "grammar": 0.3, "reading": 0.5},
        game_progress={"tutorial_completed": True, "tickets_purchased": 0}
    )

@pytest.fixture
def sample_companion_request():
    """Provide a sample companion request for testing."""
    from backend.ai.companion.core.models import CompanionRequest
    import uuid
    
    return CompanionRequest(
        request_id=str(uuid.uuid4()),
        player_input="Where is the ticket machine?",
        request_type="assistance"
    ) 