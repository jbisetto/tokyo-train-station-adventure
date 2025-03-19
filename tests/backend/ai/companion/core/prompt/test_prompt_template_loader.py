"""
Test module for the PromptTemplateLoader class.
"""

import os
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock

# Import the class we will implement
from backend.ai.companion.core.prompt.prompt_template_loader import PromptTemplateLoader
from backend.ai.companion.core.models import IntentCategory

# Define test data paths
TEST_TEMPLATES_DIR = os.path.join(os.getcwd(), "prompt_templates")

class TestPromptTemplateLoader:
    """Test the PromptTemplateLoader class."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create the loader but patch _load_all_templates to prevent real template loading
        with patch.object(PromptTemplateLoader, '_load_all_templates'):
            self.loader = PromptTemplateLoader(TEST_TEMPLATES_DIR)
            # Ensure we start with empty dictionaries for tests
            self.loader.templates = {}
    
    def test_init_creates_empty_dictionary(self):
        """Test that the constructor creates an empty templates dictionary."""
        assert self.loader.templates == {}
    
    def test_load_all_templates_populates_dictionary(self):
        """Test that load_all_templates populates the templates dictionary."""
        # Run the load method
        self.loader._load_all_templates()
        
        # Verify templates were loaded
        assert "default_prompts" in self.loader.templates
        assert "language_instructor_prompts" in self.loader.templates
    
    def test_load_template_adds_to_templates_dict(self):
        """Test that _load_template adds a template to templates."""
        # Mock file path
        file_path = os.path.join(TEST_TEMPLATES_DIR, "test_template.json")
        
        # Test template data
        test_template_data = {
            "template_id": "test_template",
            "intent_prompts": {
                "VOCABULARY_HELP": "Test vocab prompt",
                "DEFAULT": "Test default prompt"
            }
        }
        
        # Mock open and file read
        with patch("builtins.open", mock_open(read_data=json.dumps(test_template_data))) as mock_file:
            self.loader._load_template(file_path)
            
            # Verify file was read
            mock_file.assert_called_with(file_path, 'r', encoding='utf-8')
            
            # Verify template was added to templates
            assert "test_template" in self.loader.templates
            assert self.loader.templates["test_template"]["intent_prompts"]["VOCABULARY_HELP"] == "Test vocab prompt"
    
    def test_get_intent_prompt_returns_correct_prompt(self):
        """Test that get_intent_prompt returns the prompt for the specified intent."""
        # Add a test template
        self.loader.templates = {
            "default_prompts": {
                "template_id": "default_prompts",
                "intent_prompts": {
                    "VOCABULARY_HELP": "Test vocab prompt",
                    "DEFAULT": "Test default prompt"
                }
            }
        }
        
        # Get a prompt for an existing intent
        result = self.loader.get_intent_prompt(IntentCategory.VOCABULARY_HELP)
        
        # Verify correct prompt was returned
        assert result == "Test vocab prompt"
    
    def test_get_intent_prompt_returns_default_for_missing_intent(self):
        """Test that get_intent_prompt returns the DEFAULT prompt for a missing intent."""
        # Add a test template with no GRAMMAR_EXPLANATION prompt
        self.loader.templates = {
            "default_prompts": {
                "template_id": "default_prompts",
                "intent_prompts": {
                    "VOCABULARY_HELP": "Test vocab prompt",
                    "DEFAULT": "Test default prompt"
                }
            }
        }
        
        # Get a prompt for a missing intent
        result = self.loader.get_intent_prompt(IntentCategory.GRAMMAR_EXPLANATION)
        
        # Verify DEFAULT prompt was returned
        assert result == "Test default prompt"
    
    def test_get_intent_prompt_returns_empty_string_for_missing_default(self):
        """Test that get_intent_prompt returns empty string when no DEFAULT is defined."""
        # Add a test template with no DEFAULT prompt
        self.loader.templates = {
            "default_prompts": {
                "template_id": "default_prompts",
                "intent_prompts": {
                    "VOCABULARY_HELP": "Test vocab prompt"
                    # No DEFAULT
                }
            }
        }
        
        # Get a prompt for a missing intent
        result = self.loader.get_intent_prompt(IntentCategory.GRAMMAR_EXPLANATION)
        
        # Verify empty string was returned
        assert result == ""
    
    def test_get_intent_prompt_with_profile_id_returns_profile_specific_prompt(self):
        """Test that get_intent_prompt with profile_id returns a profile-specific prompt."""
        # Add a test template with profile-specific prompts
        self.loader.templates = {
            "language_instructor_prompts": {
                "template_id": "language_instructor_prompts",
                "intent_prompts": {
                    "VOCABULARY_HELP": "General vocab prompt",
                    "DEFAULT": "General default prompt"
                },
                "npc_specific_instructions": {
                    "companion_dog": "Special dog instructions"
                }
            }
        }
        
        # Configure the active template
        self.loader.active_template_id = "language_instructor_prompts"
        
        # Get a prompt for a specific profile
        prompt = self.loader.get_intent_prompt(IntentCategory.VOCABULARY_HELP, profile_id="companion_dog")
        
        # Verify prompt includes profile-specific instructions
        assert "General vocab prompt" in prompt
        assert "Special dog instructions" in prompt
    
    def test_get_intent_prompt_without_profile_id_returns_general_prompt(self):
        """Test that get_intent_prompt without profile_id returns a general prompt."""
        # Add a test template with profile-specific prompts
        self.loader.templates = {
            "language_instructor_prompts": {
                "template_id": "language_instructor_prompts",
                "intent_prompts": {
                    "VOCABULARY_HELP": "General vocab prompt",
                    "DEFAULT": "General default prompt"
                },
                "npc_specific_instructions": {
                    "companion_dog": "Special dog instructions"
                }
            }
        }
        
        # Configure the active template
        self.loader.active_template_id = "language_instructor_prompts"
        
        # Get a prompt without specifying a profile
        prompt = self.loader.get_intent_prompt(IntentCategory.VOCABULARY_HELP)
        
        # Verify prompt does not include profile-specific instructions
        assert "General vocab prompt" in prompt
        assert "Special dog instructions" not in prompt
    
    def test_get_intent_prompt_includes_response_instructions(self):
        """Test that get_intent_prompt includes response instructions if available."""
        # Add a test template with response instructions
        self.loader.templates = {
            "default_prompts": {
                "template_id": "default_prompts",
                "intent_prompts": {
                    "VOCABULARY_HELP": "Test vocab prompt",
                    "DEFAULT": "Test default prompt"
                },
                "response_instructions": "General response instructions"
            }
        }
        
        # Configure the active template
        self.loader.active_template_id = "default_prompts"
        
        # Get a prompt
        prompt = self.loader.get_intent_prompt(IntentCategory.VOCABULARY_HELP)
        
        # Verify prompt includes response instructions
        assert "Test vocab prompt" in prompt
        assert "General response instructions" in prompt
    
    def test_get_intent_prompt_with_unknown_template_id_returns_empty_string(self):
        """Test that get_intent_prompt with unknown template_id returns empty string."""
        # Set an unknown active template
        self.loader.active_template_id = "non_existent_template"
        
        # Get a prompt
        result = self.loader.get_intent_prompt(IntentCategory.VOCABULARY_HELP)
        
        # Verify empty string was returned
        assert result == ""
    
    def test_set_active_template_changes_active_template_id(self):
        """Test that set_active_template changes the active_template_id."""
        # Add test templates
        self.loader.templates = {
            "default_prompts": {"template_id": "default_prompts"},
            "language_instructor_prompts": {"template_id": "language_instructor_prompts"}
        }
        
        # Set active template
        self.loader.set_active_template("language_instructor_prompts")
        
        # Verify active template was changed
        assert self.loader.active_template_id == "language_instructor_prompts"
    
    def test_set_active_template_with_unknown_id_logs_warning(self):
        """Test that set_active_template with unknown id logs a warning."""
        # Mock the logger
        with patch("logging.Logger.warning") as mock_warning:
            # Set unknown active template
            self.loader.set_active_template("non_existent_template")
            
            # Verify warning was logged
            mock_warning.assert_called_once()
            
            # Verify active template was not changed
            assert self.loader.active_template_id == "default_prompts"  # Default value 