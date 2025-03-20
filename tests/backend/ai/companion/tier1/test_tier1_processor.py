import unittest
from unittest.mock import patch, MagicMock

from backend.ai.companion.tier1.tier1_processor import Tier1Processor
from backend.ai.companion.core.models import ClassifiedRequest, IntentCategory, ComplexityLevel, ProcessingTier


class TestTier1Processor(unittest.TestCase):
    """Test the Tier1Processor class."""

    def setUp(self):
        # Create a mock for get_config
        self.get_config_patcher = patch('backend.ai.companion.tier1.tier1_processor.get_config')
        self.mock_get_config = self.get_config_patcher.start()
        
        # Mock config
        self.mock_config = {
            "enabled": True,
            "default_model": "test_model"
        }
        self.mock_get_config.return_value = self.mock_config
        
    def tearDown(self):
        self.get_config_patcher.stop()
        
    def test_tier1_processor_init_uses_config(self):
        """Test that Tier1Processor uses configuration in initialization."""
        processor = Tier1Processor()
        
        # Check that get_config was called with the expected arguments
        self.mock_get_config.assert_called_with('tier1', {})
        
        # Check that the processor is using the config values
        self.assertEqual(processor.enabled, self.mock_config["enabled"])
        self.assertEqual(processor.default_model, self.mock_config["default_model"])
    
    def test_tier1_processor_respects_enabled_flag(self):
        """Test that Tier1Processor respects the enabled flag from configuration."""
        # Set enabled to False
        self.mock_get_config.return_value = {"enabled": False}
        
        processor = Tier1Processor()
        
        # Create a proper mock request with all required attributes
        request = MagicMock(spec=ClassifiedRequest)
        request.intent = IntentCategory.VOCABULARY_HELP
        request.complexity = ComplexityLevel.SIMPLE
        request.processing_tier = ProcessingTier.TIER_1
        request.request_id = "test_request"
        request.player_input = "What is the Japanese word for ticket?"
        request.request_type = "text"
        request.additional_params = {}
        request.game_context = None
        request.extracted_entities = {}
        
        # Check that processing is skipped when disabled
        response = processor.process(request)
        self.assertIn("disabled", response.lower())
        
        # Set enabled to True and check that processing happens
        self.mock_get_config.return_value = {"enabled": True}
        processor = Tier1Processor()
        
        # Set up mocks for the methods called by process
        mock_tree = {"patterns": ["test pattern"]}
        
        with patch.object(processor, '_get_tree_name_for_intent', return_value="test_tree"), \
             patch.object(processor, '_load_decision_tree', return_value=mock_tree), \
             patch.object(processor, '_process_with_patterns', return_value="Test response"):
            
            # Process the request
            response = processor.process(request)
            
            # Verify that the processor attempted to process the request
            processor._get_tree_name_for_intent.assert_called_once_with(request.intent)
            processor._load_decision_tree.assert_called_once()
            processor._process_with_patterns.assert_called_once()
            self.assertEqual(response, "Test response")
    
    def test_tier1_processor_uses_configured_model(self):
        """Test that Tier1Processor uses the configured model name."""
        # Set default_model to a custom value
        self.mock_get_config.return_value = {"enabled": True, "default_model": "custom_model"}
        
        processor = Tier1Processor()
        
        # Check that the processor is using the custom model
        self.assertEqual(processor.default_model, "custom_model")
        
        # Test with a different model
        self.mock_get_config.return_value = {"enabled": True, "default_model": "another_model"}
        processor = Tier1Processor()
        self.assertEqual(processor.default_model, "another_model")
    
    def test_tier1_processor_falls_back_to_defaults(self):
        """Test that Tier1Processor falls back to defaults if config is missing."""
        # Return None to simulate missing config
        self.mock_get_config.return_value = None
        
        # Should use defaults
        processor = Tier1Processor()
        self.assertTrue(processor.enabled)  # Default should be True
        self.assertEqual(processor.default_model, "rule-based")  # Default model


if __name__ == '__main__':
    unittest.main() 