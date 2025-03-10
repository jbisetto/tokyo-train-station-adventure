"""
Tests for the Amazon Bedrock client.

This module contains tests for the Amazon Bedrock client, which is used
to interact with Amazon Bedrock models for the Tier 3 processor.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock

from backend.ai.companion.core.models import CompanionRequest
from backend.ai.companion.tier3.bedrock_client import BedrockClient, BedrockError


@pytest.fixture
def sample_request():
    """Create a sample request for testing."""
    return CompanionRequest(
        request_id="test-123",
        player_input="How do I say 'I want to go to Tokyo' in Japanese?",
        request_type="language_help",
        additional_params={"complexity": "high"}
    )


@pytest.fixture
def sample_bedrock_response():
    """Create a sample response from the Bedrock API."""
    return {
        "inputTextTokenCount": 42,
        "results": [{
            "tokenCount": 128,
            "outputText": "「東京に行きたいです」(Tōkyō ni ikitai desu) is how you say 'I want to go to Tokyo' in Japanese.",
            "completionReason": "FINISH"
        }],
        "amazon-bedrock-invocationMetrics": {
            "inputTokenCount": 42,
            "outputTokenCount": 128,
            "invocationLatency": 1234,
            "firstByteLatency": 567
        }
    }


class TestBedrockClient:
    """Tests for the BedrockClient class."""
    
    def test_initialization(self):
        """Test that the BedrockClient can be initialized."""
        client = BedrockClient()
        
        assert client.region_name == "us-east-1"  # Default region
        assert client.model_id == "anthropic.claude-3-sonnet-20240229-v1:0"  # Default model
        assert client.max_tokens == 1000  # Default max tokens
        
        # Test with custom parameters
        client = BedrockClient(
            region_name="us-west-2",
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            max_tokens=500
        )
        
        assert client.region_name == "us-west-2"
        assert client.model_id == "anthropic.claude-3-haiku-20240307-v1:0"
        assert client.max_tokens == 500
    
    @pytest.mark.asyncio
    async def test_generate(self, sample_request, sample_bedrock_response):
        """Test generating a response from Bedrock."""
        client = BedrockClient()
        
        # Mock the _call_bedrock_api method
        with patch.object(client, '_call_bedrock_api', new_callable=AsyncMock) as mock_call_api:
            mock_call_api.return_value = sample_bedrock_response
            
            # Generate a response
            response = await client.generate(sample_request)
            
            # Check that the response is correct
            assert response == sample_bedrock_response["results"][0]["outputText"]
            
            # Check that _call_bedrock_api was called with the correct parameters
            mock_call_api.assert_called_once()
            args, kwargs = mock_call_api.call_args
            
            # Check that the prompt was created correctly
            assert "How do I say 'I want to go to Tokyo' in Japanese?" in kwargs["prompt"]
            assert kwargs["model_id"] == client.model_id
            assert kwargs["max_tokens"] == client.max_tokens
    
    @pytest.mark.asyncio
    async def test_generate_with_custom_parameters(self, sample_request, sample_bedrock_response):
        """Test generating a response with custom parameters."""
        client = BedrockClient()
        
        # Mock the _call_bedrock_api method
        with patch.object(client, '_call_bedrock_api', new_callable=AsyncMock) as mock_call_api:
            mock_call_api.return_value = sample_bedrock_response
            
            # Generate a response with custom parameters
            response = await client.generate(
                sample_request,
                model_id="anthropic.claude-3-haiku-20240307-v1:0",
                temperature=0.5,
                max_tokens=300,
                prompt="Custom prompt"
            )
            
            # Check that the response is correct
            assert response == sample_bedrock_response["results"][0]["outputText"]
            
            # Check that _call_bedrock_api was called with the correct parameters
            mock_call_api.assert_called_once()
            args, kwargs = mock_call_api.call_args
            
            # Check that the custom parameters were used
            assert kwargs["prompt"] == "Custom prompt"
            assert kwargs["model_id"] == "anthropic.claude-3-haiku-20240307-v1:0"
            assert kwargs["max_tokens"] == 300
            assert kwargs["temperature"] == 0.5
    
    @pytest.mark.asyncio
    async def test_generate_with_error(self, sample_request):
        """Test generating a response with an error."""
        client = BedrockClient()
        
        # Mock the _call_bedrock_api method to raise an exception
        with patch.object(client, '_call_bedrock_api', new_callable=AsyncMock) as mock_call_api:
            mock_call_api.side_effect = BedrockError("Failed to generate response")
            
            # Check that the exception is propagated
            with pytest.raises(BedrockError) as excinfo:
                await client.generate(sample_request)
            
            assert "Failed to generate response" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_call_bedrock_api(self, sample_bedrock_response):
        """Test calling the Bedrock API."""
        client = BedrockClient()
        
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=json.dumps(sample_bedrock_response).encode('utf-8'))
        mock_response.headers = {"Content-Type": "application/json"}
        
        # Mock the aiohttp.ClientSession.post method
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Call the API
            response = await client._call_bedrock_api(
                prompt="Test prompt",
                model_id="anthropic.claude-3-sonnet-20240229-v1:0",
                temperature=0.7,
                max_tokens=1000
            )
            
            # Check that the response is correct
            assert response == sample_bedrock_response
            
            # Check that post was called with the correct parameters
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            
            # Check the URL
            assert args[0].startswith("https://bedrock-runtime")
            
            # Check the headers
            assert "Authorization" in kwargs["headers"]
            assert kwargs["headers"]["Content-Type"] == "application/json"
            
            # Check the payload
            payload = json.loads(kwargs["data"])
            assert payload["anthropic_version"] == "bedrock-2023-05-31"
            assert payload["max_tokens"] == 1000
            assert payload["temperature"] == 0.7
            assert "messages" in payload
    
    @pytest.mark.asyncio
    async def test_call_bedrock_api_with_error(self):
        """Test calling the Bedrock API with an error."""
        client = BedrockClient()
        
        # Mock the aiohttp.ClientSession.post method to raise an exception
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = Exception("Connection error")
            
            # Check that the exception is wrapped in a BedrockError
            with pytest.raises(BedrockError) as excinfo:
                await client._call_bedrock_api(
                    prompt="Test prompt",
                    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
                    temperature=0.7,
                    max_tokens=1000
                )
            
            assert "Connection error" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_call_bedrock_api_with_error_response(self):
        """Test calling the Bedrock API with an error response."""
        client = BedrockClient()
        
        # Create a mock error response
        mock_response = MagicMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Bad request")
        
        # Mock the aiohttp.ClientSession.post method
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Check that the error response is wrapped in a BedrockError
            with pytest.raises(BedrockError) as excinfo:
                await client._call_bedrock_api(
                    prompt="Test prompt",
                    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
                    temperature=0.7,
                    max_tokens=1000
                )
            
            assert "400" in str(excinfo.value)
            assert "Bad request" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_get_available_models(self):
        """Test getting available models from Bedrock."""
        client = BedrockClient()
        
        # Create a mock response
        mock_response = {
            "modelSummaries": [
                {
                    "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
                    "modelName": "Claude 3 Sonnet"
                },
                {
                    "modelId": "anthropic.claude-3-haiku-20240307-v1:0",
                    "modelName": "Claude 3 Haiku"
                }
            ]
        }
        
        # Mock the boto3.client.list_foundation_models method
        with patch('boto3.client') as mock_boto3_client:
            mock_bedrock = MagicMock()
            mock_bedrock.list_foundation_models.return_value = mock_response
            mock_boto3_client.return_value = mock_bedrock
            
            # Get available models
            models = await client.get_available_models()
            
            # Check that the models are correct
            assert len(models) == 2
            assert models[0]["modelId"] == "anthropic.claude-3-sonnet-20240229-v1:0"
            assert models[1]["modelId"] == "anthropic.claude-3-haiku-20240307-v1:0"
            
            # Check that list_foundation_models was called
            mock_bedrock.list_foundation_models.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_available_models_with_error(self):
        """Test getting available models with an error."""
        client = BedrockClient()
        
        # Mock the boto3.client.list_foundation_models method to raise an exception
        with patch('boto3.client') as mock_boto3_client:
            mock_bedrock = MagicMock()
            mock_bedrock.list_foundation_models.side_effect = Exception("API error")
            mock_boto3_client.return_value = mock_bedrock
            
            # Check that the exception is wrapped in a BedrockError
            with pytest.raises(BedrockError) as excinfo:
                await client.get_available_models()
            
            assert "API error" in str(excinfo.value)
    
    def test_create_prompt(self, sample_request):
        """Test creating a prompt for the Bedrock API."""
        client = BedrockClient()
        
        # Create a prompt
        prompt = client._create_prompt(sample_request)
        
        # Check that the prompt contains the player input
        assert "How do I say 'I want to go to Tokyo' in Japanese?" in prompt
        
        # Check that the prompt is formatted for Claude
        assert "Human:" in prompt
        assert "Assistant:" in prompt 