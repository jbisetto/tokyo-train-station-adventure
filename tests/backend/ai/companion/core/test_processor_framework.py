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
        """Test that the processor process method works as expected."""
        from backend.ai.companion.core.processor_framework import Processor
        
        # Create a concrete implementation of the abstract Processor class
        class ConcreteProcessor(Processor):
            def process(self, request):
                return f"Processed: {request.player_input}"
        
        # Create an instance of the concrete processor
        processor = ConcreteProcessor()
        
        # Process a request
        result = processor.process(sample_classified_request)
        
        # Check the result
        assert result == f"Processed: {sample_classified_request.player_input}"


class TestTier1Processor:
    """Tests for the Tier 1 (rule-based) processor."""
    
    def test_tier1_processor_creation(self):
        """Test that the Tier 1 processor can be created."""
        from backend.ai.companion.core.processor_framework import Tier1Processor
        
        processor = Tier1Processor()
        
        assert processor is not None
        assert hasattr(processor, 'process')
    
    def test_tier1_processor_process(self, sample_classified_request, monkeypatch):
        """Test that the Tier 1 processor can process a request."""
        from backend.ai.companion.core.processor_framework import Tier1Processor
        from unittest.mock import MagicMock
        
        # Create mocks for the components
        mock_template_system = MagicMock()
        mock_template_system.process_request.return_value = "Response from template system"
        
        mock_pattern_matcher = MagicMock()
        mock_pattern_matcher.match.return_value = {"matched": False}
        
        mock_tree_processor = MagicMock()
        mock_tree_processor.process_request.return_value = (None, {})
        
        # Create a processor with mocked components
        processor = Tier1Processor()
        
        # Replace the components with mocks
        processor.template_system = mock_template_system
        processor.pattern_matcher = mock_pattern_matcher
        processor.tree_processor = mock_tree_processor
        
        # Process a request
        result = processor.process(sample_classified_request)
        
        # Check that the result is a string
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Verify that the pattern matcher was called
        mock_pattern_matcher.match.assert_called_once_with(sample_classified_request.player_input)
    
    def test_tier1_processor_with_pattern_match(self, sample_classified_request, monkeypatch):
        """Test that the Tier 1 processor can process a request with a pattern match."""
        from backend.ai.companion.core.processor_framework import Tier1Processor
        from unittest.mock import MagicMock
        
        # Create mocks for the components
        mock_template_system = MagicMock()
        mock_template_system.process_request.return_value = "Response from template system"
        
        mock_pattern_matcher = MagicMock()
        mock_pattern_matcher.match.return_value = {"matched": True}
        mock_pattern_matcher.extract_entities.return_value = {"word": "kippu"}
        
        mock_tree_processor = MagicMock()
        mock_tree_processor.process_request.return_value = (None, {})
        
        # Create a processor with mocked components
        processor = Tier1Processor()
        
        # Replace the components with mocks
        processor.template_system = mock_template_system
        processor.pattern_matcher = mock_pattern_matcher
        processor.tree_processor = mock_tree_processor
        
        # Process a request
        result = processor.process(sample_classified_request)
        
        # Check that the result is a string
        assert isinstance(result, str)
        assert result == "Response from template system"
        
        # Verify that the pattern matcher was called
        mock_pattern_matcher.match.assert_called_once_with(sample_classified_request.player_input)
        mock_pattern_matcher.extract_entities.assert_called_once()
        mock_template_system.process_request.assert_called_once_with(sample_classified_request)
    
    def test_tier1_processor_with_decision_tree(self, sample_classified_request, monkeypatch):
        """Test that the Tier 1 processor can process a request with a decision tree."""
        from backend.ai.companion.core.processor_framework import Tier1Processor
        from unittest.mock import MagicMock
        
        # Create mocks for the components
        mock_template_system = MagicMock()
        
        mock_pattern_matcher = MagicMock()
        
        mock_tree_processor = MagicMock()
        mock_tree_processor.process_request.return_value = ("Response from decision tree", {"state": "updated"})
        
        # Create a processor with mocked components
        processor = Tier1Processor()
        
        # Replace the components with mocks
        processor.template_system = mock_template_system
        processor.pattern_matcher = mock_pattern_matcher
        processor.tree_processor = mock_tree_processor
        
        # Add conversation state to the request
        sample_classified_request.additional_params["conversation_state"] = {"state": "initial"}
        
        # Process a request
        result = processor.process(sample_classified_request)
        
        # Check that the result is a string
        assert isinstance(result, str)
        assert result == "Response from decision tree"
        
        # Verify that the tree processor was called
        mock_tree_processor.process_request.assert_called_once()
        
        # Verify that the state was updated
        assert sample_classified_request.additional_params["conversation_state"] == {"state": "updated"}


class TestTier2Processor:
    """Tests for the Tier 2 (local LLM) processor."""
    
    def test_tier2_processor_creation(self):
        """Test that the Tier 2 processor can be created."""
        from backend.ai.companion.core.processor_framework import Tier2Processor
        
        processor = Tier2Processor()
        
        assert processor is not None
        assert hasattr(processor, 'process')
    
    def test_tier2_processor_process(self, sample_classified_request, monkeypatch):
        """Test that the Tier 2 processor can process a request."""
        from backend.ai.companion.core.processor_framework import Tier2Processor
        
        # Mock the Ollama client
        mock_ollama_client = MagicMock()
        mock_ollama_client.generate.return_value = "This is a response from the local LLM."
        
        # Patch the Ollama client creation
        monkeypatch.setattr(
            "backend.ai.companion.core.processor_framework.Tier2Processor._create_ollama_client",
            lambda self: mock_ollama_client
        )
        
        processor = Tier2Processor()
        
        # Process a request
        result = processor.process(sample_classified_request)
        
        # Check that the result is a string
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Check that the Ollama client was called
        mock_ollama_client.generate.assert_called_once()


class TestTier3Processor:
    """Tests for the Tier 3 (cloud API) processor."""
    
    def test_tier3_processor_creation(self):
        """Test that the Tier 3 processor can be created."""
        from backend.ai.companion.tier3.tier3_processor import Tier3Processor
        
        processor = Tier3Processor()
        
        assert processor is not None
        assert hasattr(processor, 'process')
    
    def test_tier3_processor_process(self, sample_classified_request, monkeypatch):
        """Test that the Tier 3 processor can process a request."""
        from backend.ai.companion.tier3.tier3_processor import Tier3Processor
        
        # Mock the Bedrock client
        mock_bedrock_client = MagicMock()
        mock_bedrock_client.generate = AsyncMock(return_value="This is a response from the cloud API.")
        
        # Patch the Bedrock client creation
        monkeypatch.setattr(
            "backend.ai.companion.tier3.tier3_processor.BedrockClient",
            lambda **kwargs: mock_bedrock_client
        )
        
        processor = Tier3Processor()
        
        # Process a request
        result = processor.process(sample_classified_request)
        
        # Check that the result is a string
        assert isinstance(result, str)
        assert len(result) > 0


class TestProcessorFactory:
    """Tests for the processor factory."""
    
    def test_processor_factory_creation(self):
        """Test that the processor factory can be created."""
        from backend.ai.companion.core.processor_framework import ProcessorFactory
        
        factory = ProcessorFactory()
        
        assert factory is not None
        assert hasattr(factory, 'get_processor')
    
    def test_get_processor_tier1(self):
        """Test that the factory returns a Tier 1 processor for TIER_1."""
        from backend.ai.companion.core.processor_framework import ProcessorFactory, Tier1Processor
        
        factory = ProcessorFactory()
        
        processor = factory.get_processor(ProcessingTier.TIER_1)
        
        assert isinstance(processor, Tier1Processor)
    
    def test_get_processor_tier2(self):
        """Test that the factory returns a Tier 2 processor for TIER_2."""
        from backend.ai.companion.core.processor_framework import ProcessorFactory
        from backend.ai.companion.tier2.tier2_processor import Tier2Processor
        
        factory = ProcessorFactory()
        
        processor = factory.get_processor(ProcessingTier.TIER_2)
        
        assert isinstance(processor, Tier2Processor)
    
    def test_get_processor_tier3(self):
        """Test that the factory returns a Tier 3 processor for TIER_3."""
        from backend.ai.companion.core.processor_framework import ProcessorFactory
        from backend.ai.companion.tier3.tier3_processor import Tier3Processor
        
        factory = ProcessorFactory()
        
        processor = factory.get_processor(ProcessingTier.TIER_3)
        
        assert isinstance(processor, Tier3Processor)
    
    def test_get_processor_invalid_tier(self):
        """Test that the factory raises an error for an invalid tier."""
        from backend.ai.companion.core.processor_framework import ProcessorFactory
        
        factory = ProcessorFactory()
        
        # Create a mock tier that's not in the enum
        mock_tier = MagicMock()
        mock_tier.name = "INVALID_TIER"
        
        # Check that it raises a ValueError
        with pytest.raises(ValueError, match=f"Unsupported processing tier: {mock_tier.name}"):
            factory.get_processor(mock_tier)
    
    def test_processor_factory_singleton(self):
        """Test that the processor factory is a singleton."""
        from backend.ai.companion.core.processor_framework import ProcessorFactory
        
        factory1 = ProcessorFactory()
        factory2 = ProcessorFactory()
        
        assert factory1 is factory2 