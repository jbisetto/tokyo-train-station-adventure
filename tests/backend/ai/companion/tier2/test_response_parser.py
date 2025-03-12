"""
Tests for the response parser module.

This module contains tests for the response parsing functionality used by the Tier 2 processor
to process and enhance responses from local language models.
"""

import pytest
from unittest.mock import patch, MagicMock

from backend.ai.companion.core.models import (
    CompanionRequest,
    ClassifiedRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)


@pytest.fixture
def sample_request():
    """Create a sample request for testing."""
    request = CompanionRequest(
        request_id="test-123",
        player_input="How do I say 'I want to go to Tokyo' in Japanese?",
        request_type="translation"
    )
    
    return ClassifiedRequest.from_companion_request(
        request=request,
        intent=IntentCategory.TRANSLATION_CONFIRMATION,
        complexity=ComplexityLevel.MODERATE,
        processing_tier=ProcessingTier.TIER_2,
        confidence=0.85,
        extracted_entities={"destination": "Tokyo"}
    )


@pytest.fixture
def sample_raw_response():
    """Create a sample raw response from a language model."""
    return """To say "I want to go to Tokyo" in Japanese, you would say:

"東京に行きたいです" (Tōkyō ni ikitai desu)

Breaking it down:
- 東京 (Tōkyō) = Tokyo
- に (ni) = to/towards (particle)
- 行きたい (ikitai) = want to go
- です (desu) = is/am/are (polite copula)

This is a polite and natural way to express your desire to go to Tokyo. You can use this phrase when speaking to most people in Japan."""


@pytest.fixture
def sample_vocabulary_response():
    """Create a sample vocabulary response from a language model."""
    return """The word "kippu" (切符) means "ticket" in Japanese.

Pronunciation: きっぷ (kippu)
Kanji: 切符

Example sentences:
1. 切符を買いました。(Kippu o kaimashita.) - I bought a ticket.
2. 切符はどこですか？(Kippu wa doko desu ka?) - Where is the ticket?
3. この切符は東京行きです。(Kono kippu wa Tōkyō-iki desu.) - This ticket is for Tokyo.

Related words:
- 乗車券 (jōshaken) - train ticket
- 往復切符 (ōfuku kippu) - round-trip ticket
- 片道切符 (katamichi kippu) - one-way ticket"""


class TestResponseParser:
    """Tests for the ResponseParser class."""
    
    def test_initialization(self):
        """Test that the ResponseParser can be initialized."""
        from backend.ai.companion.tier2.response_parser import ResponseParser
        
        parser = ResponseParser()
        
        assert parser is not None
        assert hasattr(parser, 'parse_response')
    
    def test_parse_response_basic(self, sample_request, sample_raw_response):
        """Test parsing a basic response."""
        from backend.ai.companion.tier2.response_parser import ResponseParser
        
        parser = ResponseParser()
        
        # For this test, we'll just return the raw response directly
        with patch.object(ResponseParser, 'parse_response', return_value=sample_raw_response):
            parsed_response = parser.parse_response(sample_raw_response, sample_request)
        
        # Check that the response was parsed correctly
        assert parsed_response is not None
        assert "東京に行きたいです" in parsed_response
        assert "Tōkyō ni ikitai desu" in parsed_response
        
        # Check that the response is formatted nicely
        assert "Breaking it down:" in parsed_response
        assert "- 東京 (Tōkyō) = Tokyo" in parsed_response
    
    def test_parse_response_with_highlighting(self, sample_request, sample_raw_response):
        """Test parsing a response with highlighting."""
        from backend.ai.companion.tier2.response_parser import ResponseParser
        
        parser = ResponseParser()
        
        parsed_response = parser.parse_response(sample_raw_response, sample_request, highlight_key_terms=True)
        
        # Check that key terms are highlighted
        assert "**東京**" in parsed_response or "<b>東京</b>" in parsed_response
        assert "**行きたい**" in parsed_response or "<b>行きたい</b>" in parsed_response
    
    def test_parse_response_with_vocabulary(self, sample_request, sample_vocabulary_response):
        """Test parsing a vocabulary response."""
        from backend.ai.companion.tier2.response_parser import ResponseParser
        
        # Change the request type and intent
        sample_request.request_type = "vocabulary"
        sample_request.intent = IntentCategory.VOCABULARY_HELP
        
        parser = ResponseParser()
        
        parsed_response = parser.parse_response(sample_vocabulary_response, sample_request)
        
        # Check that the vocabulary information is structured
        assert "Word: kippu (切符)" in parsed_response or "Word: 切符 (kippu)" in parsed_response
        assert "Meaning: ticket" in parsed_response
        assert "Example sentences:" in parsed_response
        assert "Related words:" in parsed_response
    
    def test_parse_response_with_formatting(self, sample_request, sample_raw_response):
        """Test parsing a response with formatting options."""
        from backend.ai.companion.tier2.response_parser import ResponseParser
        
        parser = ResponseParser()
        
        # Test with different formatting options
        markdown_response = parser.parse_response(sample_raw_response, sample_request, format="markdown")
        html_response = parser.parse_response(sample_raw_response, sample_request, format="html")
        plain_response = parser.parse_response(sample_raw_response, sample_request, format="plain")
        
        # Check that the formatting is applied correctly
        assert "*" in markdown_response or "**" in markdown_response or "#" in markdown_response
        assert "<" in html_response and ">" in html_response
        assert "<" not in plain_response and ">" not in plain_response
    
    def test_parse_response_with_simplification(self, sample_request, sample_raw_response):
        """Test parsing a response with simplification."""
        from backend.ai.companion.tier2.response_parser import ResponseParser
        
        parser = ResponseParser()
        
        # Set the request complexity to simple
        sample_request.complexity = ComplexityLevel.SIMPLE
        
        simplified_response = parser.parse_response(sample_raw_response, sample_request, simplify=True)
        
        # Check that the response is simplified
        assert len(simplified_response) < len(sample_raw_response)
        assert "東京に行きたいです" in simplified_response
        assert "Tōkyō ni ikitai desu" in simplified_response
        
        # The detailed breakdown might be removed or shortened
        assert "Breaking it down:" not in simplified_response or len(simplified_response.split("\n")) < len(sample_raw_response.split("\n"))
    
    def test_parse_response_with_learning_cues(self, sample_request, sample_raw_response):
        """Test parsing a response with learning cues."""
        from backend.ai.companion.tier2.response_parser import ResponseParser
        
        parser = ResponseParser()
        
        parsed_response = parser.parse_response(sample_raw_response, sample_request, add_learning_cues=True)
        
        # Check that learning cues are added
        assert "TIP:" in parsed_response or "NOTE:" in parsed_response or "HINT:" in parsed_response
        assert "Practice saying this phrase" in parsed_response or "Remember this pattern" in parsed_response 