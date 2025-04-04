"""
Test module for validating JSON schemas and sample data.
"""

import os
import json
import pytest
import jsonschema
from jsonschema import validate

# Define paths
SCHEMA_DIR = os.path.join(os.getcwd(), "schemas")
PROFILES_DIR = os.path.join(os.getcwd(), "src/data/profiles")
TEMPLATES_DIR = os.path.join(os.getcwd(), "src/data/prompt_templates")

# Load schemas
def load_schema(schema_name):
    """Load a schema file."""
    schema_path = os.path.join(SCHEMA_DIR, schema_name)
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Load profile data
def load_profile(profile_name):
    """Load a profile JSON file."""
    profile_path = os.path.join(PROFILES_DIR, profile_name)
    with open(profile_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Load template data
def load_template(template_name):
    """Load a template JSON file."""
    template_path = os.path.join(TEMPLATES_DIR, template_name)
    with open(template_path, 'r', encoding='utf-8') as f:
        return json.load(f)

class TestSchemaValidation:
    """Test the JSON schemas and sample data."""
    
    def test_profile_schema_is_valid(self):
        """Test that the profile schema is valid JSON Schema."""
        schema = load_schema("profile_schema.json")
        # This will raise an exception if the schema is invalid
        jsonschema.Draft7Validator.check_schema(schema)
    
    def test_prompt_template_schema_is_valid(self):
        """Test that the prompt template schema is valid JSON Schema."""
        schema = load_schema("prompt_template_schema.json")
        # This will raise an exception if the schema is invalid
        jsonschema.Draft7Validator.check_schema(schema)
    
    def test_base_japanese_npc_profile_is_valid(self):
        """Test that the base Japanese NPC profile is valid."""
        schema = load_schema("profile_schema.json")
        profile = load_profile("base_japanese_npc.json")
        validate(instance=profile, schema=schema)
    
    def test_base_language_instructor_profile_is_valid(self):
        """Test that the base language instructor profile is valid."""
        schema = load_schema("profile_schema.json")
        profile = load_profile("base_language_instructor.json")
        validate(instance=profile, schema=schema)
    
    def test_base_station_staff_profile_is_valid(self):
        """Test that the base station staff profile is valid."""
        schema = load_schema("profile_schema.json")
        profile = load_profile("base_station_staff.json")
        validate(instance=profile, schema=schema)
    
    def test_hachiko_profile_is_valid(self):
        """Test that the Hachiko profile is valid."""
        schema = load_schema("profile_schema.json")
        profile = load_profile("hachiko.json")
        validate(instance=profile, schema=schema)
    
    def test_station_attendant_profile_is_valid(self):
        """Test that the station attendant profile is valid."""
        schema = load_schema("profile_schema.json")
        profile = load_profile("station_attendant.json")
        validate(instance=profile, schema=schema)
    
    def test_default_prompts_template_is_valid(self):
        """Test that the default prompts template is valid."""
        schema = load_schema("prompt_template_schema.json")
        template = load_template("default_prompts.json")
        validate(instance=template, schema=schema)
    
    def test_language_instructor_prompts_template_is_valid(self):
        """Test that the language instructor prompts template is valid."""
        schema = load_schema("prompt_template_schema.json")
        template = load_template("language_instructor_prompts.json")
        validate(instance=template, schema=schema)
    
    def test_invalid_profile_raises_error(self):
        """Test that an invalid profile raises a validation error."""
        schema = load_schema("profile_schema.json")
        # Create an invalid profile (missing required fields)
        invalid_profile = {
            "name": "Invalid Profile"
            # Missing profile_id and role which are required
        }
        with pytest.raises(jsonschema.exceptions.ValidationError):
            validate(instance=invalid_profile, schema=schema)
    
    def test_invalid_template_raises_error(self):
        """Test that an invalid template raises a validation error."""
        schema = load_schema("prompt_template_schema.json")
        # Create an invalid template (missing required fields)
        invalid_template = {
            "response_instructions": "Some instructions"
            # Missing template_id and intent_prompts which are required
        }
        with pytest.raises(jsonschema.exceptions.ValidationError):
            validate(instance=invalid_template, schema=schema) 