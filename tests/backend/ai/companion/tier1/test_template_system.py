"""
Tests for the Template System component.

This module contains tests for the template system used by the Tier 1 processor
to generate responses based on templates with variable substitution.
"""

import pytest
import os
import json
from unittest.mock import patch, mock_open
from enum import Enum

from src.ai.companion.core.models import (
    ClassifiedRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)


@pytest.fixture
def sample_classified_request():
    """Create a sample classified request for vocabulary help."""
    return ClassifiedRequest(
        request_id="test-123",
        player_input="What does 'kippu' mean?",
        request_type="vocabulary",
        intent=IntentCategory.VOCABULARY_HELP,
        complexity=ComplexityLevel.SIMPLE,
        processing_tier=ProcessingTier.TIER_1,
        confidence=0.9,
        extracted_entities={"word": "kippu", "meaning": "ticket"}
    )


@pytest.fixture
def sample_templates():
    """Create a sample set of templates for testing."""
    return {
        "vocabulary_help": [
            "{word} means {meaning} in Japanese.",
            "The Japanese word '{word}' translates to '{meaning}' in English.",
            "'{word}' is the Japanese word for '{meaning}'."
        ],
        "grammar_explanation": [
            "The pattern {pattern} is used to {usage}.",
            "When you want to {usage}, you can use the pattern {pattern}.",
            "In Japanese, {pattern} is a grammar pattern for {usage}."
        ],
        "direction_guidance": [
            "To get to {destination}, you need to {directions}.",
            "Follow these directions to {destination}: {directions}",
            "Here's how to reach {destination}: {directions}"
        ],
        "translation_confirmation": [
            "'{original}' in Japanese is '{translation}'.",
            "The phrase '{original}' translates to '{translation}' in Japanese.",
            "'{translation}' is how you say '{original}' in Japanese."
        ],
        "general_hint": [
            "Here's a hint: {hint}",
            "Let me give you a tip: {hint}",
            "This might help: {hint}"
        ],
        "fallback": [
            "I'm not sure I understand. Could you rephrase that?",
            "I don't have information about that. Can I help with something else?",
            "I'm still learning and don't know about that yet."
        ]
    }


class TestTemplateSystem:
    """Tests for the TemplateSystem class."""
    
    def test_initialization(self):
        """Test that the TemplateSystem can be initialized."""
        from src.ai.companion.tier1.template_system import TemplateSystem
        
        template_system = TemplateSystem()
        
        assert template_system is not None
        assert hasattr(template_system, 'get_template')
        assert hasattr(template_system, 'render_template')
    
    def test_load_templates_from_file(self):
        """Test loading templates from a file."""
        from src.ai.companion.tier1.template_system import TemplateSystem
        
        # Mock the open function to return a sample templates file
        mock_templates = json.dumps({
            "vocabulary_help": [
                "{word} means {meaning} in Japanese."
            ]
        })
        
        with patch("builtins.open", mock_open(read_data=mock_templates)):
            template_system = TemplateSystem(template_file="mock_path.json")
            
            # Check that templates were loaded
            assert template_system.templates is not None
            assert "vocabulary_help" in template_system.templates
            assert len(template_system.templates["vocabulary_help"]) == 1
    
    def test_load_templates_from_dict(self, sample_templates):
        """Test loading templates from a dictionary."""
        from src.ai.companion.tier1.template_system import TemplateSystem
        
        template_system = TemplateSystem(templates=sample_templates)
        
        # Check that templates were loaded
        assert template_system.templates is not None
        assert "vocabulary_help" in template_system.templates
        assert len(template_system.templates["vocabulary_help"]) == 3
    
    def test_get_template_by_intent(self, sample_templates):
        """Test getting a template by intent."""
        from src.ai.companion.tier1.template_system import TemplateSystem
        
        template_system = TemplateSystem(templates=sample_templates)
        
        # Get a template for vocabulary help
        template = template_system.get_template(IntentCategory.VOCABULARY_HELP)
        
        # Check that a template was returned
        assert template is not None
        assert isinstance(template, str)
        assert template in sample_templates["vocabulary_help"]
    
    def test_get_template_with_context(self, sample_templates):
        """Test getting a template with context consideration."""
        from src.ai.companion.tier1.template_system import TemplateSystem
        
        template_system = TemplateSystem(templates=sample_templates)
        
        # Define a context that should influence template selection
        context = {
            "formality": "high",
            "player_proficiency": "beginner"
        }
        
        # Get a template with context
        template = template_system.get_template(
            IntentCategory.VOCABULARY_HELP,
            context=context
        )
        
        # Check that a template was returned
        assert template is not None
        assert isinstance(template, str)
    
    def test_get_template_fallback(self, sample_templates):
        """Test getting a fallback template for unknown intent."""
        from src.ai.companion.tier1.template_system import TemplateSystem
        
        template_system = TemplateSystem(templates=sample_templates)
        
        # Create a mock intent that doesn't exist in templates
        class MockIntent(str, Enum):
            UNKNOWN = "unknown"
        
        # Get a template for an unknown intent
        template = template_system.get_template(MockIntent.UNKNOWN)
        
        # Check that a fallback template was returned
        assert template is not None
        assert isinstance(template, str)
        assert template in sample_templates["fallback"]
    
    def test_render_template(self, sample_templates):
        """Test rendering a template with variables."""
        from src.ai.companion.tier1.template_system import TemplateSystem
        
        template_system = TemplateSystem(templates=sample_templates)
        
        # Get a template
        template = "{word} means {meaning} in Japanese."
        
        # Render the template with variables
        variables = {"word": "kippu", "meaning": "ticket"}
        rendered = template_system.render_template(template, variables)
        
        # Check that the template was rendered correctly
        assert rendered == "kippu means ticket in Japanese."
    
    def test_render_template_with_missing_variables(self, sample_templates):
        """Test rendering a template with missing variables."""
        from src.ai.companion.tier1.template_system import TemplateSystem
        
        template_system = TemplateSystem(templates=sample_templates)
        
        # Get a template
        template = "{word} means {meaning} in Japanese."
        
        # Render the template with missing variables
        variables = {"word": "kippu"}
        rendered = template_system.render_template(template, variables)
        
        # Check that the template was rendered with placeholders
        assert rendered == "kippu means {meaning} in Japanese."
    
    def test_render_template_with_extra_variables(self, sample_templates):
        """Test rendering a template with extra variables."""
        from src.ai.companion.tier1.template_system import TemplateSystem
        
        template_system = TemplateSystem(templates=sample_templates)
        
        # Get a template
        template = "{word} means {meaning} in Japanese."
        
        # Render the template with extra variables
        variables = {"word": "kippu", "meaning": "ticket", "extra": "unused"}
        rendered = template_system.render_template(template, variables)
        
        # Check that the template was rendered correctly
        assert rendered == "kippu means ticket in Japanese."
    
    def test_process_request(self, sample_classified_request, sample_templates):
        """Test processing a request with the template system."""
        from src.ai.companion.tier1.template_system import TemplateSystem
        
        template_system = TemplateSystem(templates=sample_templates)
        
        # Process the request
        response = template_system.process_request(sample_classified_request)
        
        # Check that a response was generated
        assert response is not None
        assert isinstance(response, str)
        assert "kippu" in response
        assert "ticket" in response
    
    def test_process_request_with_context(self, sample_classified_request, sample_templates):
        """Test processing a request with context."""
        from src.ai.companion.tier1.template_system import TemplateSystem
        
        template_system = TemplateSystem(templates=sample_templates)
        
        # Define a context
        context = {
            "formality": "high",
            "player_proficiency": "beginner"
        }
        
        # Process the request with context
        response = template_system.process_request(
            sample_classified_request,
            context=context
        )
        
        # Check that a response was generated
        assert response is not None
        assert isinstance(response, str)
        assert "kippu" in response
        assert "ticket" in response
    
    def test_add_template(self, sample_templates):
        """Test adding a new template."""
        from src.ai.companion.tier1.template_system import TemplateSystem
        
        template_system = TemplateSystem(templates=sample_templates)
        
        # Add a new template
        template_system.add_template(
            IntentCategory.VOCABULARY_HELP,
            "The word '{word}' is '{meaning}' in English."
        )
        
        # Check that the template was added
        assert "The word '{word}' is '{meaning}' in English." in template_system.templates["vocabulary_help"]
    
    def test_remove_template(self, sample_templates):
        """Test removing a template."""
        from src.ai.companion.tier1.template_system import TemplateSystem
        
        template_system = TemplateSystem(templates=sample_templates)
        
        # Get the initial count
        initial_count = len(template_system.templates["vocabulary_help"])
        
        # Remove a template
        template_to_remove = sample_templates["vocabulary_help"][0]
        template_system.remove_template(
            IntentCategory.VOCABULARY_HELP,
            template_to_remove
        )
        
        # Check that the template was removed
        assert template_to_remove not in template_system.templates["vocabulary_help"]
        assert len(template_system.templates["vocabulary_help"]) == initial_count - 1
    
    def test_save_templates(self, sample_templates, tmp_path):
        """Test saving templates to a file."""
        from src.ai.companion.tier1.template_system import TemplateSystem
        
        template_system = TemplateSystem(templates=sample_templates)
        
        # Create a temporary file path
        temp_file = tmp_path / "test_templates.json"
        
        # Save the templates
        template_system.save_templates(str(temp_file))
        
        # Check that the file was created
        assert os.path.exists(temp_file)
        
        # Load the file and check contents
        with open(temp_file, 'r') as f:
            saved_templates = json.load(f)
        
        # Check that the saved templates match the original
        assert saved_templates == sample_templates 