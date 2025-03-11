"""
Tests for specialized handlers for complex scenarios in Tier 3.
"""

import pytest
import uuid
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from backend.ai.companion.core.models import (
    ClassifiedRequest,
    CompanionRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from backend.ai.companion.tier3.bedrock_client import BedrockClient, BedrockError


@pytest.fixture
def sample_grammar_request():
    """Create a sample grammar explanation request for testing."""
    return ClassifiedRequest(
        request_id=str(uuid.uuid4()),
        player_input="Can you explain the difference between は and が particles in Japanese?",
        request_type="grammar",
        timestamp=datetime.now(),
        intent=IntentCategory.GRAMMAR_EXPLANATION,
        complexity=ComplexityLevel.COMPLEX,
        processing_tier=ProcessingTier.TIER_3,
        confidence=0.9,
        extracted_entities={"grammar_point": "は vs が"}
    )


@pytest.fixture
def sample_translation_request():
    """Create a sample translation request for testing."""
    return ClassifiedRequest(
        request_id=str(uuid.uuid4()),
        player_input="How would I say 'I would like to buy a round-trip ticket to Kyoto' in Japanese?",
        request_type="translation",
        timestamp=datetime.now(),
        intent=IntentCategory.TRANSLATION_CONFIRMATION,
        complexity=ComplexityLevel.COMPLEX,
        processing_tier=ProcessingTier.TIER_3,
        confidence=0.85,
        extracted_entities={"destination": "Kyoto", "ticket_type": "round-trip"}
    )


@pytest.fixture
def sample_conversation_context():
    """Create a sample conversation context for testing."""
    return {
        "conversation_id": "conv-123",
        "previous_exchanges": [
            {
                "request": "What does 'kippu' mean?",
                "response": "'Kippu' means 'ticket' in Japanese."
            },
            {
                "request": "How do I ask for a ticket to Odawara?",
                "response": "You can say 'Odawara made no kippu o kudasai' which means 'Please give me a ticket to Odawara'."
            }
        ],
        "player_language_level": "N5",
        "current_location": "ticket_counter"
    }


@pytest.fixture
def mock_bedrock_client():
    """Create a mock Bedrock client for testing."""
    client = MagicMock(spec=BedrockClient)
    client.generate = AsyncMock(return_value="This is a response from the Bedrock API.")
    return client


class TestSpecializedHandlerRegistry:
    """Tests for the SpecializedHandlerRegistry class."""
    
    def test_registry_initialization(self):
        """Test that the SpecializedHandlerRegistry can be initialized."""
        from backend.ai.companion.tier3.specialized_handlers import SpecializedHandlerRegistry
        
        registry = SpecializedHandlerRegistry()
        
        assert registry is not None
        assert hasattr(registry, 'get_handler')
        assert hasattr(registry, 'register_handler')
    
    def test_register_handler(self):
        """Test registering a handler with the registry."""
        from backend.ai.companion.tier3.specialized_handlers import (
            SpecializedHandlerRegistry,
            SpecializedHandler,
            GrammarExplanationHandler
        )
        
        registry = SpecializedHandlerRegistry()
        handler = GrammarExplanationHandler()
        
        registry.register_handler(IntentCategory.GRAMMAR_EXPLANATION, handler)
        
        assert registry.get_handler(IntentCategory.GRAMMAR_EXPLANATION) == handler
    
    def test_get_handler(self):
        """Test getting a handler from the registry."""
        from backend.ai.companion.tier3.specialized_handlers import (
            SpecializedHandlerRegistry,
            SpecializedHandler,
            GrammarExplanationHandler,
            TranslationHandler
        )
        
        registry = SpecializedHandlerRegistry()
        grammar_handler = GrammarExplanationHandler()
        translation_handler = TranslationHandler()
        
        registry.register_handler(IntentCategory.GRAMMAR_EXPLANATION, grammar_handler)
        registry.register_handler(IntentCategory.TRANSLATION_CONFIRMATION, translation_handler)
        
        assert registry.get_handler(IntentCategory.GRAMMAR_EXPLANATION) == grammar_handler
        assert registry.get_handler(IntentCategory.TRANSLATION_CONFIRMATION) == translation_handler
    
    def test_get_handler_fallback(self):
        """Test getting a handler for an intent that doesn't have a specialized handler."""
        from backend.ai.companion.tier3.specialized_handlers import (
            SpecializedHandlerRegistry,
            DefaultHandler
        )
        
        registry = SpecializedHandlerRegistry()
        
        handler = registry.get_handler(IntentCategory.GENERAL_HINT)
        
        assert isinstance(handler, DefaultHandler)


class TestSpecializedHandler:
    """Tests for the SpecializedHandler base class."""
    
    def test_specialized_handler_interface(self):
        """Test that the SpecializedHandler defines the required interface."""
        from backend.ai.companion.tier3.specialized_handlers import SpecializedHandler
        
        # SpecializedHandler is an abstract base class, so we can't instantiate it directly
        # Instead, we check that it has the required methods
        assert hasattr(SpecializedHandler, 'can_handle')
        assert hasattr(SpecializedHandler, 'create_prompt')
        assert hasattr(SpecializedHandler, 'process_response')
    
    def test_default_handler(self):
        """Test the DefaultHandler implementation."""
        from backend.ai.companion.tier3.specialized_handlers import DefaultHandler
        
        handler = DefaultHandler()
        
        assert handler.can_handle(IntentCategory.GENERAL_HINT) is True
        
        # DefaultHandler should be able to handle any intent
        for intent in IntentCategory:
            assert handler.can_handle(intent) is True


class TestGrammarExplanationHandler:
    """Tests for the GrammarExplanationHandler class."""
    
    def test_can_handle(self):
        """Test that the GrammarExplanationHandler can handle grammar explanation requests."""
        from backend.ai.companion.tier3.specialized_handlers import GrammarExplanationHandler
        
        handler = GrammarExplanationHandler()
        
        assert handler.can_handle(IntentCategory.GRAMMAR_EXPLANATION) is True
        assert handler.can_handle(IntentCategory.VOCABULARY_HELP) is False
    
    def test_create_prompt(self, sample_grammar_request):
        """Test creating a prompt for a grammar explanation request."""
        from backend.ai.companion.tier3.specialized_handlers import GrammarExplanationHandler
        
        handler = GrammarExplanationHandler()
        
        prompt = handler.create_prompt(sample_grammar_request)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "grammar" in prompt.lower()
        assert "は" in prompt
        assert "が" in prompt
        assert "JLPT N5" in prompt
    
    def test_process_response(self, sample_grammar_request):
        """Test processing a response for a grammar explanation request."""
        from backend.ai.companion.tier3.specialized_handlers import GrammarExplanationHandler
        
        handler = GrammarExplanationHandler()
        
        raw_response = """
        The particles は (wa) and が (ga) are both used to mark the subject of a sentence, but they have different functions:

        は (wa):
        - Marks the topic of the sentence
        - Used for contrast or to introduce a new topic
        - Often used with general statements

        が (ga):
        - Marks the subject of the action
        - Used for specific or new information
        - Often used in questions or to emphasize the subject

        Example with は: 私は学生です (Watashi wa gakusei desu) - "I am a student" (stating a fact about the topic "I")
        Example with が: 誰が学生ですか (Dare ga gakusei desu ka) - "Who is a student?" (asking about a specific subject)
        """
        
        processed_response = handler.process_response(raw_response, sample_grammar_request)
        
        assert isinstance(processed_response, str)
        assert len(processed_response) > 0
        assert "は (wa)" in processed_response
        assert "が (ga)" in processed_response
        assert "Example" in processed_response


class TestTranslationHandler:
    """Tests for the TranslationHandler class."""
    
    def test_can_handle(self):
        """Test that the TranslationHandler can handle translation requests."""
        from backend.ai.companion.tier3.specialized_handlers import TranslationHandler
        
        handler = TranslationHandler()
        
        assert handler.can_handle(IntentCategory.TRANSLATION_CONFIRMATION) is True
        assert handler.can_handle(IntentCategory.GRAMMAR_EXPLANATION) is False
    
    def test_create_prompt(self, sample_translation_request):
        """Test creating a prompt for a translation request."""
        from backend.ai.companion.tier3.specialized_handlers import TranslationHandler
        
        handler = TranslationHandler()
        
        prompt = handler.create_prompt(sample_translation_request)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "translation" in prompt.lower()
        assert "Kyoto" in prompt
        assert "round-trip" in prompt
        assert "JLPT N5" in prompt
    
    def test_process_response(self, sample_translation_request):
        """Test processing a response for a translation request."""
        from backend.ai.companion.tier3.specialized_handlers import TranslationHandler
        
        handler = TranslationHandler()
        
        raw_response = """
        To say "I would like to buy a round-trip ticket to Kyoto" in Japanese, you would say:

        "京都まで往復切符を買いたいです。"
        (Kyōto made ōfuku kippu o kaitai desu.)

        Breaking it down:
        - 京都 (Kyōto) - Kyoto
        - まで (made) - to (destination marker)
        - 往復 (ōfuku) - round-trip
        - 切符 (kippu) - ticket
        - を (o) - object marker
        - 買いたい (kaitai) - want to buy
        - です (desu) - polite form of "is"
        """
        
        processed_response = handler.process_response(raw_response, sample_translation_request)
        
        assert isinstance(processed_response, str)
        assert len(processed_response) > 0
        assert "京都まで往復切符を買いたいです" in processed_response
        assert "Kyōto made ōfuku kippu o kaitai desu" in processed_response
        assert "Breaking it down" in processed_response


class TestConversationContextHandler:
    """Tests for the ConversationContextHandler class."""
    
    def test_can_handle_with_context(self, sample_grammar_request, sample_conversation_context):
        """Test that the ConversationContextHandler can handle requests with conversation context."""
        from backend.ai.companion.tier3.specialized_handlers import ConversationContextHandler
        
        handler = ConversationContextHandler()
        
        # Add conversation context to the request
        sample_grammar_request.additional_params = {"conversation_context": sample_conversation_context}
        
        assert handler.can_handle(sample_grammar_request.intent) is True
    
    def test_create_prompt_with_context(self, sample_grammar_request, sample_conversation_context):
        """Test creating a prompt for a request with conversation context."""
        from backend.ai.companion.tier3.specialized_handlers import ConversationContextHandler
        
        handler = ConversationContextHandler()
        
        # Add conversation context to the request
        sample_grammar_request.additional_params = {"conversation_context": sample_conversation_context}
        
        prompt = handler.create_prompt(sample_grammar_request)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Previous conversation" in prompt
        assert "kippu" in prompt
        assert "Odawara" in prompt
        assert "ticket_counter" in prompt
    
    @pytest.mark.asyncio
    async def test_handle_request_with_context(self, sample_grammar_request, sample_conversation_context, mock_bedrock_client):
        """Test handling a request with conversation context."""
        from backend.ai.companion.tier3.specialized_handlers import ConversationContextHandler
        
        handler = ConversationContextHandler(bedrock_client=mock_bedrock_client)
        
        # Add conversation context to the request
        sample_grammar_request.additional_params = {"conversation_context": sample_conversation_context}
        
        response = await handler.handle_request(sample_grammar_request)
        
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Check that the Bedrock client was called with a prompt that includes the conversation context
        mock_bedrock_client.generate.assert_called_once()
        args, kwargs = mock_bedrock_client.generate.call_args
        assert "Previous conversation" in kwargs.get("prompt", "") 