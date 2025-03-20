import unittest
import os
import tempfile
import yaml
from unittest.mock import patch, mock_open

from backend.ai.companion.config import get_config


class TestConfig(unittest.TestCase):
    """Test the configuration loading system."""

    def setUp(self):
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()
        
    def test_get_config_loads_from_file(self):
        """Test that get_config correctly loads values from companion.yaml."""
        # Create a temporary config file
        config_content = {
            "tier1": {"enabled": True, "default_model": "test_model"},
            "tier2": {
                "enabled": False,
                "base_url": "http://test:9999",
                "default_model": "test_model",
                "cache_enabled": False
            },
            "tier3": {"enabled": True, "default_model": "test-bedrock"}
        }
        
        # Mock the open function to return our config
        with patch("builtins.open", mock_open(read_data=yaml.dump(config_content))):
            with patch("os.path.exists", return_value=True):
                # Get sections
                tier1_config = get_config("tier1")
                tier2_config = get_config("tier2")
                tier3_config = get_config("tier3")
                
                # Check that values are loaded correctly
                self.assertEqual(tier1_config["enabled"], True)
                self.assertEqual(tier1_config["default_model"], "test_model")
                self.assertEqual(tier2_config["enabled"], False)
                self.assertEqual(tier2_config["default_model"], "test_model")
                self.assertEqual(tier3_config["enabled"], True)
                self.assertEqual(tier3_config["default_model"], "test-bedrock")
    
    def test_get_config_returns_default_if_missing(self):
        """Test that get_config returns the default value if the section is missing."""
        # Create a config with missing sections
        config_content = {
            "tier1": {"enabled": True},
            "tier3": {"enabled": True}
        }
        
        # Mock the open function to return our config
        with patch("builtins.open", mock_open(read_data=yaml.dump(config_content))):
            with patch("os.path.exists", return_value=True):
                # Get a missing section with a default
                default_value = {"enabled": False}
                result = get_config("tier2", default=default_value)
                self.assertEqual(result, default_value)
                
                # Test with a different default
                different_default = {"enabled": True, "default_model": "fallback_model"}
                result = get_config("nonexistent", default=different_default)
                self.assertEqual(result, different_default)
    
    def test_get_config_returns_default_if_file_not_found(self):
        """Test that get_config returns default values if the config file is not found."""
        # Mock os.path.exists to return False (file doesn't exist)
        with patch("os.path.exists", return_value=False):
            # Get a section that would be in the default config
            default_value = {"enabled": True}
            result = get_config("tier1", default=default_value)
            self.assertEqual(result, default_value)
            
            # Default for missing section
            result = get_config("nonexistent", default="default_value")
            self.assertEqual(result, "default_value")
    
    def test_get_config_logs_loading_info(self):
        """Test that get_config logs information about loading the configuration."""
        config_content = {"test": "value"}
        
        # Mock the open function and os.path.exists
        with patch("builtins.open", mock_open(read_data=yaml.dump(config_content))):
            with patch("os.path.exists", return_value=True):
                with patch("backend.ai.companion.config.logger.info") as mock_info:
                    with patch("backend.ai.companion.config.logger.debug") as mock_debug:
                        # Call get_config
                        get_config("test")
                        
                        # Check that logging was called with the expected messages
                        mock_info.assert_any_call("Loaded configuration from config/companion.yaml")
                        mock_debug.assert_any_call("Found configuration for section 'test'")


if __name__ == '__main__':
    unittest.main() 