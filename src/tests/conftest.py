"""
Tokyo Train Station Adventure - Test Configuration

This module contains pytest fixtures and configuration for testing.
"""

import pytest
import sys
import os
import yaml
import shutil
from pathlib import Path
import logging

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

@pytest.fixture(autouse=True)
def cleanup_player_history():
    """Clean up player history files created during tests.
    
    This fixture runs automatically for all tests and cleans up any player
    history files that were created during testing.
    """
    logger = logging.getLogger("test.cleanup")
    
    # Define the test player history directory
    player_history_dir = "src/data/player_history"
    
    # Get list of files before the test
    existing_files = set()
    if os.path.exists(player_history_dir):
        existing_files = set(f for f in os.listdir(player_history_dir) if f.endswith('.json'))
    
    # Run the test
    yield
    
    # After the test, clean up any new files that were created
    if os.path.exists(player_history_dir):
        # Find new files created during the test
        current_files = set(f for f in os.listdir(player_history_dir) if f.endswith('.json'))
        new_files = current_files - existing_files
        
        # Remove new files
        for file_name in new_files:
            file_path = os.path.join(player_history_dir, file_name)
            try:
                os.remove(file_path)
                logger.info(f"Removed test player history file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to remove {file_path}: {e}") 