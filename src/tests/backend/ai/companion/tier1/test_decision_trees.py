"""
Tests for the Decision Trees component.

This module contains tests for the decision tree system used by the Tier 1 processor
to handle multi-turn interactions and structured decision making.
"""

import pytest
import os
import json
from unittest.mock import patch, mock_open

from src.ai.companion.core.models import (
    ClassifiedRequest,
    CompanionRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)


@pytest.fixture
def sample_decision_tree():
    """Create a sample decision tree for testing."""
    return {
        "id": "vocabulary_help",
        "name": "Vocabulary Help",
        "description": "Helps the player with vocabulary",
        "root_node": "ask_word",
        "nodes": {
            "ask_word": {
                "type": "question",
                "message": "Which word would you like to know about?",
                "transitions": {
                    "word_provided": "provide_meaning",
                    "no_word": "ask_for_context",
                    "default": "fallback"
                }
            },
            "provide_meaning": {
                "type": "response",
                "message": "'{word}' means '{meaning}' in Japanese.",
                "transitions": {
                    "ask_for_example": "provide_example",
                    "ask_for_kanji": "provide_kanji",
                    "default": "ask_if_helpful"
                }
            },
            "provide_example": {
                "type": "response",
                "message": "Here's an example: {example}",
                "transitions": {
                    "ask_for_kanji": "provide_kanji",
                    "default": "ask_if_helpful"
                }
            },
            "provide_kanji": {
                "type": "response",
                "message": "The kanji for '{word}' is '{kanji}'.",
                "transitions": {
                    "ask_for_example": "provide_example",
                    "default": "ask_if_helpful"
                }
            },
            "ask_for_context": {
                "type": "question",
                "message": "Could you provide some context or a sentence where you heard this word?",
                "transitions": {
                    "context_provided": "analyze_context",
                    "default": "fallback"
                }
            },
            "analyze_context": {
                "type": "process",
                "action": "analyze_context",
                "transitions": {
                    "word_found": "provide_meaning",
                    "default": "fallback"
                }
            },
            "ask_if_helpful": {
                "type": "question",
                "message": "Was that helpful?",
                "transitions": {
                    "yes": "end_conversation",
                    "no": "ask_for_clarification",
                    "default": "end_conversation"
                }
            },
            "ask_for_clarification": {
                "type": "question",
                "message": "What else would you like to know about '{word}'?",
                "transitions": {
                    "ask_for_example": "provide_example",
                    "ask_for_kanji": "provide_kanji",
                    "default": "fallback"
                }
            },
            "fallback": {
                "type": "response",
                "message": "I'm sorry, I don't understand. Let's try a different approach.",
                "transitions": {
                    "default": "ask_word"
                }
            },
            "end_conversation": {
                "type": "response",
                "message": "Great! Let me know if you need help with any other words.",
                "transitions": {
                    "default": "exit"
                }
            },
            "exit": {
                "type": "exit",
                "message": "Conversation ended."
            }
        }
    }


@pytest.fixture
def sample_conversation_state():
    """Create a sample conversation state for testing."""
    return {
        "tree_id": "vocabulary_help",
        "current_node": "ask_word",
        "variables": {
            "word": "kippu",
            "meaning": "ticket",
            "kanji": "切符",
            "example": "Kippu wa doko desu ka? (Where is the ticket?)"
        },
        "history": [
            {
                "node_id": "ask_word",
                "message": "Which word would you like to know about?",
                "response": "kippu"
            }
        ]
    }


@pytest.fixture
def followup_conversation_state():
    """Create a sample conversation state for testing follow-up requests."""
    return {
        "tree_id": "vocabulary_help",
        "current_node": "provide_meaning",
        "variables": {
            "word": "kippu",
            "meaning": "ticket",
            "kanji": "切符",
            "example": "Kippu wa doko desu ka? (Where is the ticket?)"
        },
        "history": [
            {
                "node_id": "ask_word",
                "message": "Which word would you like to know about?",
                "response": "kippu"
            },
            {
                "node_id": "provide_meaning",
                "message": "'kippu' means 'ticket' in Japanese.",
                "transition": "word_provided"
            }
        ]
    }


class TestDecisionTree:
    """Tests for the DecisionTree class."""
    
    def test_initialization(self, sample_decision_tree):
        """Test that the DecisionTree can be initialized."""
        from src.ai.companion.tier1.decision_trees import DecisionTree
        
        tree = DecisionTree(sample_decision_tree)
        
        assert tree is not None
        assert tree.id == "vocabulary_help"
        assert tree.name == "Vocabulary Help"
        assert tree.root_node == "ask_word"
        assert len(tree.nodes) == 11
    
    def test_get_node(self, sample_decision_tree):
        """Test getting a node from the tree."""
        from src.ai.companion.tier1.decision_trees import DecisionTree
        
        tree = DecisionTree(sample_decision_tree)
        
        # Get a node
        node = tree.get_node("ask_word")
        
        # Check that the node was returned
        assert node is not None
        assert node["type"] == "question"
        assert "message" in node
        assert "transitions" in node
    
    def test_get_nonexistent_node(self, sample_decision_tree):
        """Test getting a nonexistent node from the tree."""
        from src.ai.companion.tier1.decision_trees import DecisionTree
        
        tree = DecisionTree(sample_decision_tree)
        
        # Get a nonexistent node
        with pytest.raises(KeyError):
            tree.get_node("nonexistent_node")
    
    def test_render_message(self, sample_decision_tree):
        """Test rendering a message with variables."""
        from src.ai.companion.tier1.decision_trees import DecisionTree
        
        tree = DecisionTree(sample_decision_tree)
        
        # Render a message
        variables = {"word": "kippu", "meaning": "ticket"}
        message = tree.render_message("'{word}' means '{meaning}' in Japanese.", variables)
        
        # Check that the message was rendered correctly
        assert message == "'kippu' means 'ticket' in Japanese."
    
    def test_get_transition(self, sample_decision_tree):
        """Test getting a transition from a node."""
        from src.ai.companion.tier1.decision_trees import DecisionTree
        
        tree = DecisionTree(sample_decision_tree)
        
        # Get a transition
        next_node = tree.get_transition("ask_word", "word_provided")
        
        # Check that the transition was returned
        assert next_node == "provide_meaning"
    
    def test_get_default_transition(self, sample_decision_tree):
        """Test getting the default transition from a node."""
        from src.ai.companion.tier1.decision_trees import DecisionTree
        
        tree = DecisionTree(sample_decision_tree)
        
        # Get the default transition
        next_node = tree.get_transition("ask_word", "unknown_transition")
        
        # Check that the default transition was returned
        assert next_node == "fallback"
    
    def test_is_exit_node(self, sample_decision_tree):
        """Test checking if a node is an exit node."""
        from src.ai.companion.tier1.decision_trees import DecisionTree
        
        tree = DecisionTree(sample_decision_tree)
        
        # Check exit node
        assert tree.is_exit_node("exit") is True
        
        # Check non-exit node
        assert tree.is_exit_node("ask_word") is False


class TestDecisionTreeNavigator:
    """Tests for the DecisionTreeNavigator class."""
    
    def test_initialization(self, sample_decision_tree, sample_conversation_state):
        """Test that the DecisionTreeNavigator can be initialized."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeNavigator, DecisionTree
        
        tree = DecisionTree(sample_decision_tree)
        navigator = DecisionTreeNavigator(tree, sample_conversation_state)
        
        assert navigator is not None
        assert navigator.tree.id == "vocabulary_help"
        assert navigator.state["current_node"] == "ask_word"
        assert "word" in navigator.state["variables"]
    
    def test_get_current_node(self, sample_decision_tree, sample_conversation_state):
        """Test getting the current node."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeNavigator, DecisionTree
        
        tree = DecisionTree(sample_decision_tree)
        navigator = DecisionTreeNavigator(tree, sample_conversation_state)
        
        # Get the current node
        node = navigator.get_current_node()
        
        # Check that the node was returned
        assert node is not None
        assert node["type"] == "question"
        assert node["message"] == "Which word would you like to know about?"
    
    def test_get_current_message(self, sample_decision_tree, sample_conversation_state):
        """Test getting the current message."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeNavigator, DecisionTree
        
        tree = DecisionTree(sample_decision_tree)
        navigator = DecisionTreeNavigator(tree, sample_conversation_state)
        
        # Get the current message
        message = navigator.get_current_message()
        
        # Check that the message was returned
        assert message == "Which word would you like to know about?"
    
    def test_transition(self, sample_decision_tree, sample_conversation_state):
        """Test transitioning to the next node."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeNavigator, DecisionTree
        
        tree = DecisionTree(sample_decision_tree)
        navigator = DecisionTreeNavigator(tree, sample_conversation_state)
        
        # Transition to the next node
        navigator.transition("word_provided")
        
        # Check that the transition was made
        assert navigator.state["current_node"] == "provide_meaning"
        assert len(navigator.state["history"]) == 2
    
    def test_transition_with_response(self, sample_decision_tree, sample_conversation_state):
        """Test transitioning to the next node with a response."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeNavigator, DecisionTree
        
        tree = DecisionTree(sample_decision_tree)
        navigator = DecisionTreeNavigator(tree, sample_conversation_state)
        
        # Transition to the next node with a response
        navigator.transition("word_provided", "kippu")
        
        # Check that the transition was made and the response was recorded
        assert navigator.state["current_node"] == "provide_meaning"
        assert len(navigator.state["history"]) == 2
        assert navigator.state["history"][1]["response"] == "kippu"
    
    def test_update_variables(self, sample_decision_tree, sample_conversation_state):
        """Test updating variables in the state."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeNavigator, DecisionTree
        
        tree = DecisionTree(sample_decision_tree)
        navigator = DecisionTreeNavigator(tree, sample_conversation_state)
        
        # Update variables
        navigator.update_variables({"word": "densha", "meaning": "train"})
        
        # Check that the variables were updated
        assert navigator.state["variables"]["word"] == "densha"
        assert navigator.state["variables"]["meaning"] == "train"
        assert navigator.state["variables"]["kanji"] == "切符"  # Unchanged
    
    def test_is_conversation_ended(self, sample_decision_tree, sample_conversation_state):
        """Test checking if the conversation has ended."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeNavigator, DecisionTree
        
        tree = DecisionTree(sample_decision_tree)
        navigator = DecisionTreeNavigator(tree, sample_conversation_state)
        
        # Check that the conversation has not ended
        assert navigator.is_conversation_ended() is False
        
        # Transition to the exit node
        navigator.state["current_node"] = "exit"
        
        # Check that the conversation has ended
        assert navigator.is_conversation_ended() is True
    
    def test_get_conversation_history(self, sample_decision_tree, sample_conversation_state):
        """Test getting the conversation history."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeNavigator, DecisionTree
        
        tree = DecisionTree(sample_decision_tree)
        navigator = DecisionTreeNavigator(tree, sample_conversation_state)
        
        # Get the conversation history
        history = navigator.get_conversation_history()
        
        # Check that the history was returned
        assert history is not None
        assert len(history) == 1
        assert history[0]["node_id"] == "ask_word"
        assert history[0]["response"] == "kippu"


class TestDecisionTreeManager:
    """Tests for the DecisionTreeManager class."""
    
    def test_initialization(self, sample_decision_tree):
        """Test that the DecisionTreeManager can be initialized."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeManager
        
        manager = DecisionTreeManager()
        
        assert manager is not None
        assert hasattr(manager, 'load_tree')
        assert hasattr(manager, 'get_tree')
        assert hasattr(manager, 'create_navigator')
    
    def test_load_tree_from_dict(self, sample_decision_tree):
        """Test loading a tree from a dictionary."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeManager
        
        manager = DecisionTreeManager()
        
        # Load a tree from a dictionary
        manager.load_tree(sample_decision_tree)
        
        # Check that the tree was loaded
        assert "vocabulary_help" in manager.trees
        assert manager.trees["vocabulary_help"].name == "Vocabulary Help"
    
    def test_load_tree_from_file(self, sample_decision_tree):
        """Test loading a tree from a file."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeManager
        
        manager = DecisionTreeManager()
        
        # Mock the open function to return a sample tree file
        mock_tree = json.dumps(sample_decision_tree)
        
        with patch("builtins.open", mock_open(read_data=mock_tree)):
            # Load a tree from a file
            manager.load_tree_from_file("mock_path.json")
            
            # Check that the tree was loaded
            assert "vocabulary_help" in manager.trees
            assert manager.trees["vocabulary_help"].name == "Vocabulary Help"
    
    def test_get_tree(self, sample_decision_tree):
        """Test getting a tree by ID."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeManager
        
        manager = DecisionTreeManager()
        
        # Load a tree
        manager.load_tree(sample_decision_tree)
        
        # Get the tree
        tree = manager.get_tree("vocabulary_help")
        
        # Check that the tree was returned
        assert tree is not None
        assert tree.id == "vocabulary_help"
        assert tree.name == "Vocabulary Help"
    
    def test_get_nonexistent_tree(self):
        """Test getting a nonexistent tree."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeManager
        
        manager = DecisionTreeManager()
        
        # Get a nonexistent tree
        with pytest.raises(KeyError):
            manager.get_tree("nonexistent_tree")
    
    def test_create_navigator(self, sample_decision_tree):
        """Test creating a navigator for a tree."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeManager
        
        manager = DecisionTreeManager()
        
        # Load a tree
        manager.load_tree(sample_decision_tree)
        
        # Create a navigator
        navigator = manager.create_navigator("vocabulary_help")
        
        # Check that the navigator was created
        assert navigator is not None
        assert navigator.tree.id == "vocabulary_help"
        assert navigator.state["current_node"] == "ask_word"
    
    def test_create_navigator_with_state(self, sample_decision_tree, sample_conversation_state):
        """Test creating a navigator with an existing state."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeManager
        
        manager = DecisionTreeManager()
        
        # Load a tree
        manager.load_tree(sample_decision_tree)
        
        # Create a navigator with an existing state
        navigator = manager.create_navigator("vocabulary_help", sample_conversation_state)
        
        # Check that the navigator was created with the state
        assert navigator is not None
        assert navigator.tree.id == "vocabulary_help"
        assert navigator.state["current_node"] == "ask_word"
        assert navigator.state["variables"]["word"] == "kippu"
    
    def test_save_state(self, sample_decision_tree, sample_conversation_state, tmp_path):
        """Test saving a conversation state to a file."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeManager
        
        manager = DecisionTreeManager()
        
        # Load a tree
        manager.load_tree(sample_decision_tree)
        
        # Create a navigator
        navigator = manager.create_navigator("vocabulary_help", sample_conversation_state)
        
        # Create a temporary file path
        temp_file = tmp_path / "test_state.json"
        
        # Save the state
        manager.save_state(navigator.state, str(temp_file))
        
        # Check that the file was created
        assert os.path.exists(temp_file)
        
        # Load the file and check contents
        with open(temp_file, 'r') as f:
            saved_state = json.load(f)
        
        # Check that the saved state matches the original
        assert saved_state["tree_id"] == sample_conversation_state["tree_id"]
        assert saved_state["current_node"] == sample_conversation_state["current_node"]
        assert saved_state["variables"]["word"] == sample_conversation_state["variables"]["word"]
    
    def test_load_state(self, sample_conversation_state):
        """Test loading a conversation state from a file."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeManager
        
        manager = DecisionTreeManager()
        
        # Mock the open function to return a sample state file
        mock_state = json.dumps(sample_conversation_state)
        
        with patch("builtins.open", mock_open(read_data=mock_state)):
            # Load a state from a file
            state = manager.load_state("mock_path.json")
            
            # Check that the state was loaded
            assert state is not None
            assert state["tree_id"] == "vocabulary_help"
            assert state["current_node"] == "ask_word"
            assert state["variables"]["word"] == "kippu"


class TestDecisionTreeProcessor:
    """Tests for the DecisionTreeProcessor class."""
    
    def test_initialization(self, sample_decision_tree):
        """Test that the DecisionTreeProcessor can be initialized."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeProcessor, DecisionTreeManager
        
        manager = DecisionTreeManager()
        manager.load_tree(sample_decision_tree)
        
        processor = DecisionTreeProcessor(manager)
        
        assert processor is not None
        assert processor.manager is manager
        assert hasattr(processor, 'process_request')
    
    def test_process_initial_request(self, sample_decision_tree):
        """Test processing an initial request."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeProcessor, DecisionTreeManager
        
        manager = DecisionTreeManager()
        manager.load_tree(sample_decision_tree)
        
        processor = DecisionTreeProcessor(manager)
        
        # Create a request
        request = CompanionRequest(
            request_id="test-123",
            player_input="What does kippu mean?",
            request_type="vocabulary"
        )
        
        # Process the request
        response, state = processor.process_request(request)
        
        # Check that a response was generated
        assert response is not None
        assert "kippu" in response
        assert "ticket" in response
        
        # Check that a state was created
        assert state is not None
        assert state["tree_id"] == "vocabulary_help"
        assert state["current_node"] == "provide_meaning"
        assert state["variables"]["word"] == "kippu"
    
    def test_process_followup_request(self, sample_decision_tree, followup_conversation_state):
        """Test processing a followup request."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeProcessor, DecisionTreeManager
        
        manager = DecisionTreeManager()
        manager.load_tree(sample_decision_tree)
        
        processor = DecisionTreeProcessor(manager)
        
        # Create a request
        request = CompanionRequest(
            request_id="test-123",
            player_input="Can you show me the kanji?",
            request_type="vocabulary"
        )
        
        # Store the initial history length
        initial_history_length = len(followup_conversation_state["history"])
        
        # Process the request with an existing state
        response, state = processor.process_request(request, followup_conversation_state)
        
        # Check that a response was generated
        assert response is not None
        assert "kanji" in response
        assert "切符" in response
        
        # Check that the state was updated
        assert state is not None
        assert state["current_node"] == "provide_kanji"
        assert len(state["history"]) >= initial_history_length
    
    def test_determine_intent_from_request(self, sample_decision_tree):
        """Test determining the intent from a request."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeProcessor, DecisionTreeManager
        
        manager = DecisionTreeManager()
        manager.load_tree(sample_decision_tree)
        
        processor = DecisionTreeProcessor(manager)
        
        # Create a request
        request = CompanionRequest(
            request_id="test-123",
            player_input="Can you show me an example?",
            request_type="vocabulary"
        )
        
        # Determine the intent
        intent = processor._determine_intent_from_request(request)
        
        # Check that the intent was determined
        assert intent is not None
        assert intent == "ask_for_example"
    
    def test_extract_entities_from_request(self, sample_decision_tree):
        """Test extracting entities from a request."""
        from src.ai.companion.tier1.decision_trees import DecisionTreeProcessor, DecisionTreeManager
        
        manager = DecisionTreeManager()
        manager.load_tree(sample_decision_tree)
        
        processor = DecisionTreeProcessor(manager)
        
        # Create a request
        request = CompanionRequest(
            request_id="test-123",
            player_input="What does densha mean?",
            request_type="vocabulary"
        )
        
        # Extract entities
        entities = processor._extract_entities_from_request(request)
        
        # Check that entities were extracted
        assert entities is not None
        assert "word" in entities
        assert entities["word"] == "densha" 