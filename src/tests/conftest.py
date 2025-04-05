"""
Tokyo Train Station Adventure - Test Configuration

This module contains pytest fixtures and configuration for testing.
"""

import pytest
import sys
import os
import yaml
from pathlib import Path

# Add the project root to the Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Fixtures that can be used across all tests
@pytest.fixture
def sample_game_context():
    """Provide a sample game context for testing."""
    from src.ai.companion.core.models import GameContext
    
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
    from src.ai.companion.core.models import CompanionRequest
    import uuid
    
    return CompanionRequest(
        request_id=str(uuid.uuid4()),
        player_input="Where is the ticket machine?",
        request_type="assistance"
    )

@pytest.fixture(autouse=True)
def mock_config_path():
    """Override the configuration path for tests.
    
    This fixture runs automatically for all tests and sets the COMPANION_CONFIG
    environment variable to point to our test configuration file.
    """
    original_path = os.environ.get('COMPANION_CONFIG')
    test_config_path = str(Path(__file__).parent / 'fixtures' / 'test_companion.yaml')
    
    # Make sure the test config file exists
    if not os.path.exists(test_config_path):
        raise FileNotFoundError(f"Test configuration file not found at {test_config_path}")
    
    # Set the environment variable to use our test configuration
    os.environ['COMPANION_CONFIG'] = test_config_path
    
    # Run the test
    yield
    
    # Restore the original environment
    if original_path:
        os.environ['COMPANION_CONFIG'] = original_path
    else:
        os.environ.pop('COMPANION_CONFIG', None) 