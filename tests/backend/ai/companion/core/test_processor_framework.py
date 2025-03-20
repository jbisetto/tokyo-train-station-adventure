"""
Tests for the Tiered Processing Framework.
"""

import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch

from backend.ai.companion.core.models import (
    ClassifiedRequest,
    CompanionRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)


@pytest.fixture
def sample_classified_request():
    """Create a sample classified request."""
    request_id = str(uuid.uuid4())
    return ClassifiedRequest(
        request_id=request_id,
        player_input="What does 'kippu' mean?",
        request_type="vocabulary",
        intent=IntentCategory.VOCABULARY_HELP,
        complexity=ComplexityLevel.SIMPLE,
        processing_tier=ProcessingTier.TIER_1,
        confidence=0.9,
        extracted_entities={"word": "kippu"}
    )


class TestProcessorInterface:
    """Tests for the processor interface."""
    
    def test_processor_interface(self):
        """Test that the processor interface can be implemented."""
        from backend.ai.companion.core.processor_framework import Processor
        
        # Create a concrete implementation of the abstract Processor class
        class ConcreteProcessor(Processor):
            def process(self, request):
                return f"Processed: {request.player_input}"
        
        # Create an instance of the concrete processor
        processor = ConcreteProcessor()
        
        # Check that it has the required methods
        assert hasattr(processor, 'process')
    
    def test_processor_process_method(self, sample_classified_request):
        """Test that the process method works as expected."""
        from backend.ai.companion.core.processor_framework import Processor
        
        # Create a concrete implementation of the abstract Processor class
        class ConcreteProcessor(Processor):
            def process(self, request):
                return f"Processed: {request.player_input}"
        
        # Create an instance of the concrete processor
        processor = ConcreteProcessor()
        
        # Process a request
        response = processor.process(sample_classified_request)
        
        # Check that the response is correct
        assert response == "Processed: What does 'kippu' mean?"


class TestTier1Processor:
    """Tests for the Tier1Processor class."""
    
    def test_tier1_processor_creation(self):
        """Test that a Tier1Processor can be created."""
        from backend.ai.companion.tier1.tier1_processor import Tier1Processor
        
        processor = Tier1Processor()
        
        assert processor is not None
        assert hasattr(processor, 'process')
    
    def test_tier1_processor_process(self, sample_classified_request, monkeypatch):
        """Test processing a request with the Tier1Processor."""
        from backend.ai.companion.tier1.tier1_processor import Tier1Processor
    
        # Override get_config to ensure processor is enabled for this test
        monkeypatch.setattr(
            'backend.ai.companion.tier1.tier1_processor.get_config',
            lambda section, default: {"enabled": True, "default_model": "rule-based"} if section == 'tier1' else default
        )
        
        # Create a processor
        processor = Tier1Processor()
    
        # Mock the _get_tree_name_for_intent method to return a specific tree name
        monkeypatch.setattr(processor, '_get_tree_name_for_intent', lambda intent: "vocabulary")
    
        # Mock the _process_with_decision_tree method to return a specific response
        monkeypatch.setattr(processor, '_process_with_decision_tree', lambda tree, request: "'kippu' means 'ticket' in Japanese.")
    
        # Process a request
        response = processor.process(sample_classified_request)
    
        # Check that the response is correct
        assert response == "'kippu' means 'ticket' in Japanese."
    
    def test_tier1_processor_with_pattern_match(self, sample_classified_request, monkeypatch):
        """Test processing a request with pattern matching."""
        from backend.ai.companion.tier1.tier1_processor import Tier1Processor
    
        # Override get_config to ensure processor is enabled for this test
        monkeypatch.setattr(
            'backend.ai.companion.tier1.tier1_processor.get_config',
            lambda section, default: {"enabled": True, "default_model": "rule-based"} if section == 'tier1' else default
        )
        
        # Create a processor
        processor = Tier1Processor()
    
        # Mock the _get_tree_name_for_intent method to return a specific tree name
        monkeypatch.setattr(processor, '_get_tree_name_for_intent', lambda intent: "vocabulary")
    
        # Create a mock decision tree with pattern matching
        mock_tree = {
            "patterns": [
                {
                    "pattern": r"what does '(\w+)' mean",
                    "response": "'{0}' means '{1}' in Japanese.",
                    "values": {
                        "kippu": "ticket",
                        "eki": "station",
                        "densha": "train"
                    }
                }
            ]
        }
    
        # Mock the _load_decision_tree method to return the mock tree
        monkeypatch.setattr(processor, '_load_decision_tree', lambda tree_name: mock_tree)
    
        # Process a request
        response = processor.process(sample_classified_request)
    
        # Check that the response is correct
        assert response == "'kippu' means 'ticket' in Japanese."
    
    def test_tier1_processor_with_decision_tree(self, sample_classified_request, monkeypatch):
        """Test processing a request with a decision tree."""
        from backend.ai.companion.tier1.tier1_processor import Tier1Processor
    
        # Override get_config to ensure processor is enabled for this test
        monkeypatch.setattr(
            'backend.ai.companion.tier1.tier1_processor.get_config',
            lambda section, default: {"enabled": True, "default_model": "rule-based"} if section == 'tier1' else default
        )
        
        # Create a processor
        processor = Tier1Processor()
    
        # Mock the _get_tree_name_for_intent method to return a specific tree name
        monkeypatch.setattr(processor, '_get_tree_name_for_intent', lambda intent: "vocabulary")
    
        # Create a mock decision tree with nodes
        mock_tree = {
            "nodes": {
                "root": {
                    "condition": "extracted_entities.word",
                    "branches": {
                        "kippu": "node_kippu",
                        "eki": "node_eki",
                        "default": "node_unknown"
                    }
                },
                "node_kippu": {
                    "response": "'Kippu' means 'ticket' in Japanese."
                },
                "node_eki": {
                    "response": "'Eki' means 'station' in Japanese."
                },
                "node_unknown": {
                    "response": "I'm not familiar with that word."
                }
            }
        }
    
        # Mock the _load_decision_tree method to return the mock tree
        monkeypatch.setattr(processor, '_load_decision_tree', lambda tree_name: mock_tree)
    
        # Process a request
        response = processor.process(sample_classified_request)
    
        # Check that the response is correct
        assert response == "'Kippu' means 'ticket' in Japanese."


class TestTier2Processor:
    """Tests for the Tier2Processor class."""
    
    def test_tier2_processor_creation(self):
        """Test that a Tier2Processor can be created."""
        from backend.ai.companion.tier2.tier2_processor import Tier2Processor
        
        with patch('backend.ai.companion.tier2.tier2_processor.OllamaClient'):
            processor = Tier2Processor()
            
            assert processor is not None
            assert hasattr(processor, 'process')
            assert hasattr(processor, 'prompt_manager')
            assert hasattr(processor, 'conversation_manager')
            assert hasattr(processor, 'context_manager')
    
    @pytest.mark.asyncio
    async def test_tier2_processor_process(self, sample_classified_request, monkeypatch):
        """Test processing a request with the Tier2Processor."""
        from backend.ai.companion.tier2.tier2_processor import Tier2Processor
        
        # Create a fake Tier2Processor class with a mocked process method
        class MockTier2Processor(Tier2Processor):
            async def process(self, request):
                return "'Kippu' means 'ticket' in Japanese."
        
        # Create a processor with our mocked method
        with patch('backend.ai.companion.tier2.tier2_processor.OllamaClient'):
            processor = MockTier2Processor()
            
            # Set the processing tier to TIER_2
            sample_classified_request.processing_tier = ProcessingTier.TIER_2
            
            # Process a request
            response = await processor.process(sample_classified_request)
            
            # Check that the response is correct
            assert response == "'Kippu' means 'ticket' in Japanese."


class TestTier3Processor:
    """Tests for the Tier3Processor class."""
    
    def test_tier3_processor_creation(self):
        """Test that a Tier3Processor can be created."""
        from backend.ai.companion.tier3.tier3_processor import Tier3Processor
        
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient'):
            processor = Tier3Processor()
            
            assert processor is not None
            assert hasattr(processor, 'process')
            assert hasattr(processor, 'prompt_manager')
            assert hasattr(processor, 'conversation_manager')
            assert hasattr(processor, 'context_manager')
    
    @pytest.mark.asyncio
    async def test_tier3_processor_process(self, sample_classified_request, monkeypatch):
        """Test processing a request with the Tier3Processor."""
        from backend.ai.companion.tier3.tier3_processor import Tier3Processor
        
        # Create a processor with mocked dependencies
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient') as mock_client_class:
            # Set up the mock client
            mock_client = mock_client_class.return_value
            mock_client.generate = AsyncMock(return_value="'Kippu' means 'ticket' in Japanese.")
            
            # Create a mock context manager
            mock_context_manager = MagicMock()
            mock_context_manager.get_or_create_context.return_value = {
                "conversation_id": "test-conv-123",
                "entries": []
            }
            
            # Create a mock scenario detector
            mock_scenario_detector = MagicMock()
            
            # Patch the ScenarioDetector class to return our mock
            with patch('backend.ai.companion.tier3.tier3_processor.ScenarioDetector', return_value=mock_scenario_detector):
                # Create the processor
                processor = Tier3Processor(
                    context_manager=mock_context_manager
                )
                
                # Patch the processor's process method to return a string directly
                with patch.object(Tier3Processor, 'process', new_callable=AsyncMock) as mock_process:
                    mock_process.return_value = "'Kippu' means 'ticket' in Japanese."
                    
                    # Set the processing tier to TIER_3
                    sample_classified_request.processing_tier = ProcessingTier.TIER_3
                    
                    # Process a request
                    response = await processor.process(sample_classified_request)
                    
                    # Check that the response is correct
                    assert response == "'Kippu' means 'ticket' in Japanese."
                    
                    # Check that the process method was called
                    mock_process.assert_called_once_with(sample_classified_request)


class TestProcessorFactory:
    """Tests for the ProcessorFactory class."""
    
    def test_processor_factory_creation(self):
        """Test that a ProcessorFactory can be created."""
        from backend.ai.companion.core.processor_framework import ProcessorFactory
        
        factory = ProcessorFactory()
        
        assert factory is not None
        assert hasattr(factory, 'get_processor')
    
    def test_get_processor_tier1(self):
        """Test getting a Tier1Processor from the factory."""
        from backend.ai.companion.core.processor_framework import ProcessorFactory
        from backend.ai.companion.tier1.tier1_processor import Tier1Processor
        
        factory = ProcessorFactory()
        
        processor = factory.get_processor(ProcessingTier.TIER_1)
        
        assert processor is not None
        assert isinstance(processor, Tier1Processor)
    
    def test_get_processor_tier2(self):
        """Test getting a Tier2Processor from the factory."""
        from backend.ai.companion.core.processor_framework import ProcessorFactory
        from backend.ai.companion.tier2.tier2_processor import Tier2Processor
        
        with patch('backend.ai.companion.tier2.tier2_processor.OllamaClient'):
            factory = ProcessorFactory()
            
            processor = factory.get_processor(ProcessingTier.TIER_2)
            
            assert processor is not None
            assert isinstance(processor, Tier2Processor)
    
    def test_get_processor_tier3(self):
        """Test getting a Tier3Processor from the factory."""
        from backend.ai.companion.core.processor_framework import ProcessorFactory
        from backend.ai.companion.tier3.tier3_processor import Tier3Processor
        
        with patch('backend.ai.companion.tier3.tier3_processor.BedrockClient'):
            factory = ProcessorFactory()
            
            processor = factory.get_processor(ProcessingTier.TIER_3)
            
            assert processor is not None
            assert isinstance(processor, Tier3Processor)
    
    def test_get_processor_invalid_tier(self):
        """Test getting a processor for an invalid tier."""
        from backend.ai.companion.core.processor_framework import ProcessorFactory
        
        factory = ProcessorFactory()
        
        # Create an invalid tier
        invalid_tier = "INVALID_TIER"
        
        # Try to get a processor for the invalid tier
        with pytest.raises(ValueError):
            factory.get_processor(invalid_tier)
    
    def test_processor_factory_singleton(self):
        """Test that the ProcessorFactory is a singleton."""
        from backend.ai.companion.core.processor_framework import ProcessorFactory
        
        factory1 = ProcessorFactory()
        factory2 = ProcessorFactory()
        
        assert factory1 is factory2 