import logging
from unittest.mock import Mock, patch

import pytest

from backend.ai.companion.core.models import (
    CompanionRequest, 
    ProcessingTier,
    IntentCategory,
    ComplexityLevel
)
from backend.ai.companion.core.processor_framework import ProcessorFactory
from backend.ai.companion.core.request_handler import RequestHandler


@pytest.fixture
def mock_components():
    """Create mock components for the tests."""
    intent_classifier = Mock()
    response_formatter = Mock()
    response_formatter.format_response.return_value = "Formatted response"
    
    # Configure the intent classifier to return a specific classification
    intent_classifier.classify.return_value = (
        IntentCategory.GENERAL_HINT,
        ComplexityLevel.MODERATE,
        ProcessingTier.TIER_2,
        0.85,
        {}
    )
    
    return {
        'intent_classifier': intent_classifier,
        'response_formatter': response_formatter
    }


@pytest.fixture
def sample_request():
    """Create a sample request for testing."""
    return CompanionRequest(
        request_id="test-id",
        player_input="Help me with directions",
        request_type="general_query"
    )


@pytest.fixture
def config_patch():
    """Patch the config module."""
    with patch('backend.ai.companion.config.get_config') as mock_get_config:
        # Set default config values
        mock_get_config.return_value = {
            'enabled': True
        }
        yield mock_get_config


@pytest.mark.asyncio
async def test_current_behavior_attempts_disabled_tier(mock_components, sample_request, config_patch):
    """Test current behavior that attempts to use disabled tiers."""
    # Configure tier2 as disabled in config
    def config_side_effect(section, default=None):
        if section == 'tier2':
            return {'enabled': False}
        return {'enabled': True}
    
    config_patch.side_effect = config_side_effect
    
    # Create mock processors
    mock_tier2_processor = Mock()
    mock_tier2_processor.process.return_value = "Tier 2 response"
    
    # The current implementation tries to get all processors in the cascade
    # Patching get_processor to return the mock_tier2_processor regardless of tier
    with patch.object(ProcessorFactory, 'get_processor', return_value=mock_tier2_processor) as mock_get_processor:
        # Create request handler
        handler = RequestHandler(
            intent_classifier=mock_components['intent_classifier'],
            processor_factory=ProcessorFactory(),
            response_formatter=mock_components['response_formatter']
        )
        
        # Process request
        await handler.handle_request(sample_request)
        
        # The implementation can call get_processor multiple times, check that at minimum
        # it was called once for the preferred tier (TIER_2)
        assert mock_get_processor.call_args_list[0][0][0] == ProcessingTier.TIER_2
        
        # The processor is used once to generate a response
        assert mock_tier2_processor.process.called


@pytest.mark.asyncio
async def test_expected_cascade_behavior(mock_components, sample_request, config_patch):
    """Test the expected cascade behavior when a tier is disabled."""
    # Configure tier2 as disabled in config
    def config_side_effect(section, default=None):
        if section == 'tier2':
            return {'enabled': False}
        return {'enabled': True}
    
    config_patch.side_effect = config_side_effect
    
    # Create mock processors
    mock_tier3_processor = Mock()
    mock_tier3_processor.process.return_value = "Tier 3 response"
    
    # Set up the get_processor method to raise an exception for tier2
    # and return the tier3 processor for tier3
    def get_processor_side_effect(tier):
        if tier == ProcessingTier.TIER_2:
            raise ValueError("Tier 2 is disabled")
        elif tier == ProcessingTier.TIER_3:
            return mock_tier3_processor
        return Mock()
    
    # Set up the patch correctly
    with patch.object(ProcessorFactory, 'get_processor', side_effect=get_processor_side_effect) as mock_get_processor:
        # Create request handler with cascade behavior
        handler = RequestHandler(
            intent_classifier=mock_components['intent_classifier'],
            processor_factory=ProcessorFactory(),
            response_formatter=mock_components['response_formatter']
        )
        
        # Process request
        await handler.handle_request(sample_request)
        
        # Should have tried to get tier2 processor first
        assert mock_get_processor.call_args_list[0][0][0] == ProcessingTier.TIER_2
        
        # Should have then cascaded to tier3
        assert mock_get_processor.call_args_list[1][0][0] == ProcessingTier.TIER_3
        
        # Should have used the tier3 processor
        mock_tier3_processor.process.assert_called_once()


@pytest.mark.asyncio
async def test_all_tiers_disabled(mock_components, sample_request, config_patch):
    """Test handling when all tiers are disabled."""
    # Configure all tiers as disabled in config
    def config_side_effect(section, default=None):
        return {'enabled': False}
    
    config_patch.side_effect = config_side_effect
    
    # Configure the response formatter to indicate services disabled
    mock_components['response_formatter'].format_response.return_value = "All AI services are currently disabled. Please check your configuration."
    
    # Set up the patch correctly
    with patch.object(ProcessorFactory, 'get_processor', side_effect=ValueError("Tier is disabled in configuration")) as mock_get_processor:
        # Create request handler with cascade behavior
        handler = RequestHandler(
            intent_classifier=mock_components['intent_classifier'],
            processor_factory=ProcessorFactory(),
            response_formatter=mock_components['response_formatter']
        )
        
        # Process request
        response = await handler.handle_request(sample_request)
        
        # Should have tried all tiers
        assert mock_get_processor.call_count == 3
        
        # Should return a response indicating that services are disabled
        assert "disabled" in response.lower() 