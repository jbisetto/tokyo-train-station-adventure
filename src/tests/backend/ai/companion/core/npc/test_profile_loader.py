"""
Test module for the ProfileLoader class.
"""

import os
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock

# Import the class we will implement
from src.ai.companion.core.npc.profile_loader import ProfileLoader

# Define test data paths
TEST_PROFILES_DIR = os.path.join(os.getcwd(), "src/data/profiles")

class TestProfileLoader:
    """Test the ProfileLoader class."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create the loader but patch _load_all_profiles to prevent real profile loading
        with patch.object(ProfileLoader, '_load_all_profiles'):
            self.loader = ProfileLoader(TEST_PROFILES_DIR)
            # Ensure we start with empty dictionaries for tests
            self.loader.profiles = {}
            self.loader.base_profiles = {}
    
    def test_init_creates_empty_dictionaries(self):
        """Test that the constructor creates empty profile dictionaries."""
        assert self.loader.profiles == {}
        assert self.loader.base_profiles == {}
    
    def test_load_all_profiles_populates_dictionaries(self):
        """Test that load_all_profiles populates both dictionaries."""
        # Run the load method
        self.loader._load_all_profiles()
        
        # Verify base profiles were loaded
        assert "base_japanese_npc" in self.loader.base_profiles
        assert "base_language_instructor" in self.loader.base_profiles
        assert "base_station_staff" in self.loader.base_profiles
        
        # Verify specific profiles were loaded
        assert "companion_dog" in self.loader.profiles
        assert "station_attendant" in self.loader.profiles
    
    def test_load_base_profile_adds_to_base_profiles_dict(self):
        """Test that _load_base_profile adds a profile to base_profiles."""
        # Mock file path
        file_path = os.path.join(TEST_PROFILES_DIR, "base_japanese_npc.json")
        
        # Test profile data
        test_profile_data = {
            "profile_id": "base_test",
            "name": "Base Test",
            "role": "Test Role",
            "backstory": "Test backstory"
        }
        
        # Mock open and file read
        with patch("builtins.open", mock_open(read_data=json.dumps(test_profile_data))) as mock_file:
            self.loader._load_base_profile(file_path)
            
            # Verify file was read
            mock_file.assert_called_with(file_path, 'r', encoding='utf-8')
            
            # Verify profile was added to base_profiles
            assert "base_test" in self.loader.base_profiles
            assert self.loader.base_profiles["base_test"]["name"] == "Base Test"
    
    def test_load_profile_adds_to_profiles_dict(self):
        """Test that _load_profile adds a profile to profiles."""
        # Mock file path
        file_path = os.path.join(TEST_PROFILES_DIR, "hachiko.json")
        
        # Test profile data
        test_profile_data = {
            "profile_id": "test_profile",
            "name": "Test Profile",
            "role": "Test Role",
            "backstory": "Test backstory"
        }
        
        # Mock open and file read
        with patch("builtins.open", mock_open(read_data=json.dumps(test_profile_data))) as mock_file:
            self.loader._load_profile(file_path)
            
            # Verify file was read
            mock_file.assert_called_with(file_path, 'r', encoding='utf-8')
            
            # Verify profile was added to profiles
            assert "test_profile" in self.loader.profiles
            assert self.loader.profiles["test_profile"]["name"] == "Test Profile"
    
    def test_profile_inheritance_applies_base_profiles(self):
        """Test that profile inheritance applies base profile attributes."""
        # Set up base profile
        base_profile = {
            "profile_id": "base_test",
            "name": "Base Test",
            "role": "Base Role",
            "personality_traits": {
                "trait1": 0.5,
                "trait2": 0.7
            },
            "knowledge_areas": ["area1", "area2"]
        }
        
        # Set up child profile that extends the base
        child_profile = {
            "profile_id": "child_test",
            "name": "Child Test",
            "role": "Child Role",
            "extends": ["base_test"],
            "personality_traits": {
                "trait1": 0.8,  # Overrides trait1
                "trait3": 0.9    # Adds trait3
            }
        }
        
        # Add the base profile to base_profiles
        self.loader.base_profiles = {"base_test": base_profile}
        
        # Process inheritance
        result = self.loader._apply_inheritance(child_profile)
        
        # Verify inherited and overridden fields
        assert result["profile_id"] == "child_test"  # Not inherited
        assert result["name"] == "Child Test"  # Not inherited
        assert result["role"] == "Child Role"  # Not inherited
        assert result["personality_traits"]["trait1"] == 0.8  # Overridden
        assert result["personality_traits"]["trait2"] == 0.7  # Inherited
        assert result["personality_traits"]["trait3"] == 0.9  # Added
        assert "area1" in result["knowledge_areas"]  # Inherited
        assert "area2" in result["knowledge_areas"]  # Inherited
    
    def test_multiple_inheritance_applies_in_order(self):
        """Test that multiple inheritance applies base profiles in order."""
        # Set up first base profile
        base1 = {
            "profile_id": "base1",
            "name": "Base One",
            "role": "Base Role",
            "personality_traits": {
                "trait1": 0.5,
                "trait2": 0.7
            },
            "knowledge_areas": ["area1"]
        }
        
        # Set up second base profile
        base2 = {
            "profile_id": "base2",
            "name": "Base Two",
            "role": "Base Role Two",
            "personality_traits": {
                "trait2": 0.9,  # Will NOT override base1's trait2 in current implementation
                "trait3": 0.6
            },
            "knowledge_areas": ["area2"]
        }
        
        # Set up child profile that extends both bases
        child_profile = {
            "profile_id": "child_test",
            "name": "Child Test",
            "role": "Child Role",
            "extends": ["base1", "base2"],  # base1 is applied first, then base2
            "personality_traits": {
                "trait3": 0.8  # Overrides base2's trait3
            }
        }
        
        # Add the base profiles
        self.loader.base_profiles = {"base1": base1, "base2": base2}
        
        # Process inheritance
        result = self.loader._apply_inheritance(child_profile)
        
        # Verify inherited and overridden fields
        assert result["personality_traits"]["trait1"] == 0.5  # From base1
        assert result["personality_traits"]["trait2"] == 0.7  # From base1 (NOT overridden by base2)
        assert result["personality_traits"]["trait3"] == 0.8  # From child (overrides base2)
        assert set(result["knowledge_areas"]) == {"area1", "area2"}  # Combined from both bases
    
    def test_circular_inheritance_raises_error(self):
        """Test that circular inheritance is detected and raises an error."""
        # Create a circular inheritance situation
        self.loader.base_profiles = {
            "base_a": {"profile_id": "base_a", "name": "Base A", "role": "Role A", "extends": ["base_b"]},
            "base_b": {"profile_id": "base_b", "name": "Base B", "role": "Role B", "extends": ["base_a"]}
        }
        
        # Mock profile that extends base_a
        profile = {"profile_id": "test", "name": "Test", "role": "Test", "extends": ["base_a"]}
        
        # Processing should raise RecursionError
        with pytest.raises(RecursionError):
            self.loader._apply_inheritance(profile)
    
    def test_missing_base_profile_logs_warning(self):
        """Test that referencing a missing base profile logs a warning."""
        # Create a profile that extends a non-existent base
        profile = {
            "profile_id": "test",
            "name": "Test",
            "role": "Test Role",
            "extends": ["non_existent_base"]
        }
        
        # Mock the logger
        with patch("logging.Logger.warning") as mock_warning:
            # Process inheritance
            result = self.loader._apply_inheritance(profile)
            
            # Verify warning was logged
            mock_warning.assert_called_once()
            
            # Verify profile wasn't changed (no inheritance was applied)
            assert result == profile
    
    def test_get_profile_returns_profile(self):
        """Test that get_profile returns the requested profile."""
        # Add a test profile
        self.loader.profiles = {
            "test_profile": {
                "profile_id": "test_profile",
                "name": "Test Profile",
                "role": "Test Role"
            }
        }
        
        # Get the profile
        result = self.loader.get_profile("test_profile")
        
        # Verify correct profile was returned
        assert result["profile_id"] == "test_profile"
        assert result["name"] == "Test Profile"
    
    def test_get_profile_returns_none_for_missing_profile(self):
        """Test that get_profile returns None for a missing profile."""
        # Get a non-existent profile
        result = self.loader.get_profile("non_existent")
        
        # Verify None was returned
        assert result is None
    
    def test_get_profile_converts_to_npcprofile_object(self):
        """Test that get_profile converts the profile to an NPCProfile object."""
        # Mock the NPCProfile.from_dict method specifically
        with patch("src.ai.companion.core.npc.profile.NPCProfile.from_dict") as mock_from_dict:
            # Create a mock return value
            mock_profile = MagicMock()
            mock_from_dict.return_value = mock_profile
            
            # Add a test profile with all required fields
            self.loader.profiles = {
                "test_profile": {
                    "profile_id": "test_profile",
                    "name": "Test Profile",
                    "role": "Test Role",
                    "personality_traits": {"friendly": 0.8},
                    "speech_patterns": {"formal": True},
                    "knowledge_areas": ["test"],
                    "backstory": "A test profile",
                    "visual_traits": {"appearance": "test"},
                    "emotion_expressions": {"happy": ["smiles"]},
                    "response_format": {}
                }
            }
            
            # Request conversion to NPCProfile
            result = self.loader.get_profile("test_profile", as_object=True)
            
            # Verify from_dict was called with the profile data
            mock_from_dict.assert_called_once()
            
            # Verify the result is our mock profile
            assert result is mock_profile 