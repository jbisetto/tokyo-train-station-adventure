"""
Tests for the Amazon Bedrock client.

This module contains tests for the Amazon Bedrock client, which is used
to interact with Amazon Bedrock models for the Tier 3 processor.
"""

import pytest
import json
import aiohttp
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
        timestamp="2025-03-10T18:35:30.927478",
        additional_params={"complexity": "high"}
    )


@pytest.fixture
def sample_bedrock_response():
    """Create a sample response from the Bedrock API."""
    return {
        "amazon-bedrock-invocationMetrics": {
            "firstByteLatency": 567,
            "inputTokenCount": 42,
            "invocationLatency": 1234,
            "outputTokenCount": 128
        },
        "results": [
            {
                "outputText": "「東京に行きたいです」(Tōkyō ni ikitai desu) is how you say 'I want to go to Tokyo' in Japanese.",
                "tokenCount": 128
            }
        ]
    }


class TestBedrockClient:
    """Tests for the BedrockClient class."""
    
    def test_initialization(self):
        """Test initialization of the BedrockClient."""
        client = BedrockClient()
        
        # Check that the client has the correct default values
        assert client.region_name == "us-east-1"
        assert client.model_id == "amazon.nova-micro-v1:0"
        assert client.max_tokens == 1000
        
        # Test with custom values
        custom_client = BedrockClient(
            region_name="us-west-2",
            model_id="amazon.titan-text-express-v1",
            max_tokens=500
        )
        
        assert custom_client.region_name == "us-west-2"
        assert custom_client.model_id == "amazon.titan-text-express-v1"
        assert custom_client.max_tokens == 500
    
    @pytest.mark.asyncio
    async def test_generate(self, sample_request, sample_bedrock_response):
        """Test generating a response from Bedrock."""
        client = BedrockClient()
        
        # Create the expected response format after processing
        processed_response = {
            "completion": sample_bedrock_response["results"][0]["outputText"],
            "stop_reason": "",
            "usage": {
                "input_tokens": sample_bedrock_response["amazon-bedrock-invocationMetrics"]["inputTokenCount"],
                "output_tokens": sample_bedrock_response["results"][0]["tokenCount"]
            }
        }
        
        # Mock the check_quota function
        with patch('backend.ai.companion.tier3.bedrock_client.check_quota', new_callable=AsyncMock) as mock_check_quota:
            mock_check_quota.return_value = (True, "Quota check passed")
            
            # Mock the track_request function
            with patch('backend.ai.companion.tier3.bedrock_client.track_request', new_callable=AsyncMock) as mock_track_request:
                # Mock the _call_bedrock_api method
                with patch.object(client, '_call_bedrock_api', new_callable=AsyncMock) as mock_call_api:
                    mock_call_api.return_value = processed_response
                    
                    # Generate a response
                    response = await client.generate(sample_request)
                    
                    # Check that the response is correct
                    assert response == processed_response["completion"]
                    
                    # Check that _call_bedrock_api was called with the correct parameters
                    mock_call_api.assert_called_once()
                    args, kwargs = mock_call_api.call_args
                    
                    assert kwargs["model_id"] == "amazon.nova-micro-v1:0"
                    assert kwargs["temperature"] == 0.7
                    assert kwargs["max_tokens"] == 1000
                    assert sample_request.player_input in kwargs["prompt"]
                    
                    # Check that check_quota was called
                    mock_check_quota.assert_called_once()
                    
                    # Check that track_request was called
                    mock_track_request.assert_called_once()
                    track_args, track_kwargs = mock_track_request.call_args
                    
                    assert track_kwargs["request_id"] == sample_request.request_id
                    assert track_kwargs["model_id"] == "amazon.nova-micro-v1:0"
                    assert track_kwargs["success"] is True
    
    @pytest.mark.asyncio
    async def test_generate_with_custom_parameters(self, sample_request, sample_bedrock_response):
        """Test generating a response with custom parameters."""
        client = BedrockClient()
        
        # Create the expected response format after processing
        processed_response = {
            "completion": sample_bedrock_response["results"][0]["outputText"],
            "stop_reason": "",
            "usage": {
                "input_tokens": sample_bedrock_response["amazon-bedrock-invocationMetrics"]["inputTokenCount"],
                "output_tokens": sample_bedrock_response["results"][0]["tokenCount"]
            }
        }
        
        # Mock the check_quota function
        with patch('backend.ai.companion.tier3.bedrock_client.check_quota', new_callable=AsyncMock) as mock_check_quota:
            mock_check_quota.return_value = (True, "Quota check passed")
            
            # Mock the track_request function
            with patch('backend.ai.companion.tier3.bedrock_client.track_request', new_callable=AsyncMock) as mock_track_request:
                # Mock the _call_bedrock_api method
                with patch.object(client, '_call_bedrock_api', new_callable=AsyncMock) as mock_call_api:
                    mock_call_api.return_value = processed_response
                    
                    # Generate a response with custom parameters
                    response = await client.generate(
                        sample_request,
                        model_id="amazon.titan-text-express-v1",
                        temperature=0.5,
                        max_tokens=300,
                        prompt="Custom prompt"
                    )
                    
                    # Check that the response is correct
                    assert response == processed_response["completion"]
                    
                    # Check that _call_bedrock_api was called with the correct parameters
                    mock_call_api.assert_called_once()
                    args, kwargs = mock_call_api.call_args
                    
                    assert kwargs["model_id"] == "amazon.titan-text-express-v1"
                    assert kwargs["temperature"] == 0.5
                    assert kwargs["max_tokens"] == 300
                    assert kwargs["prompt"] == "Custom prompt"
                    
                    # Check that check_quota was called with the custom model
                    mock_check_quota.assert_called_once()
                    quota_args, quota_kwargs = mock_check_quota.call_args
                    assert quota_kwargs["model_id"] == "amazon.titan-text-express-v1"
                    
                    # Check that track_request was called with the custom model
                    mock_track_request.assert_called_once()
                    track_args, track_kwargs = mock_track_request.call_args
                    assert track_kwargs["model_id"] == "amazon.titan-text-express-v1"
    
    @pytest.mark.asyncio
    async def test_generate_with_error(self, sample_request):
        """Test generating a response with an error."""
        client = BedrockClient()
        
        # Mock the check_quota function
        with patch('backend.ai.companion.tier3.bedrock_client.check_quota', new_callable=AsyncMock) as mock_check_quota:
            mock_check_quota.return_value = (True, "Quota check passed")
            
            # Mock the track_request function
            with patch('backend.ai.companion.tier3.bedrock_client.track_request', new_callable=AsyncMock) as mock_track_request:
                # Mock the _call_bedrock_api method to raise an error
                with patch.object(client, '_call_bedrock_api', new_callable=AsyncMock) as mock_call_api:
                    mock_call_api.side_effect = BedrockError("Test error", BedrockError.MODEL_ERROR)
                    
                    # Generate a response (should raise an error)
                    with pytest.raises(BedrockError) as excinfo:
                        await client.generate(sample_request)
                    
                    # Check that the error is correct
                    assert "Test error" in str(excinfo.value)
                    assert excinfo.value.error_type == BedrockError.MODEL_ERROR
                    
                    # Check that track_request was called with success=False
                    mock_track_request.assert_called_once()
                    track_args, track_kwargs = mock_track_request.call_args
                    assert track_kwargs["success"] is False
                    assert track_kwargs["error_type"] == BedrockError.MODEL_ERROR
    
    @pytest.mark.asyncio
    async def test_generate_with_quota_exceeded(self, sample_request):
        """Test generating a response when the quota is exceeded."""
        client = BedrockClient()
        
        # Mock the check_quota function to return False
        with patch('backend.ai.companion.tier3.bedrock_client.check_quota', new_callable=AsyncMock) as mock_check_quota:
            mock_check_quota.return_value = (False, "Daily token limit exceeded")
            
            # Mock the track_request function
            with patch('backend.ai.companion.tier3.bedrock_client.track_request', new_callable=AsyncMock) as mock_track_request:
                # Mock the _call_bedrock_api method to ensure it's not called
                with patch.object(client, '_call_bedrock_api', new_callable=AsyncMock) as mock_call_api:
                    # Generate a response (should raise a quota error)
                    with pytest.raises(BedrockError) as excinfo:
                        await client.generate(sample_request)
                    
                    # Check that the error is correct
                    assert "Quota exceeded" in str(excinfo.value)
                    assert excinfo.value.error_type == BedrockError.QUOTA_ERROR
                    
                    # Check that track_request was not called (since we didn't make an API call)
                    mock_track_request.assert_not_called()
                    
                    # Check that _call_bedrock_api was not called
                    mock_call_api.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_call_bedrock_api(self, sample_bedrock_response):
        """Test calling the Bedrock API."""
        client = BedrockClient()
        
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=json.dumps(sample_bedrock_response).encode('utf-8'))
        mock_response.headers = {"Content-Type": "application/json"}
        
        # Expected processed response
        expected_processed_response = {
            "completion": sample_bedrock_response["results"][0]["outputText"],
            "stop_reason": "",
            "usage": {
                "input_tokens": sample_bedrock_response["amazon-bedrock-invocationMetrics"]["inputTokenCount"],
                "output_tokens": sample_bedrock_response["results"][0]["tokenCount"]
            }
        }
        
        # Mock the aiohttp.ClientSession.post method
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Call the API
            response = await client._call_bedrock_api(
                prompt="Test prompt",
                model_id="amazon.nova-micro-v1:0",
                temperature=0.7,
                max_tokens=1000
            )
            
            # Check that the response is correctly processed
            assert response["completion"] == expected_processed_response["completion"]
            assert "usage" in response
            assert "input_tokens" in response["usage"]
            assert "output_tokens" in response["usage"]
            
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
            assert "inputText" in payload
            assert "textGenerationConfig" in payload
            assert payload["textGenerationConfig"]["maxTokenCount"] == 1000
            assert payload["textGenerationConfig"]["temperature"] == 0.7
    
    @pytest.mark.asyncio
    async def test_call_bedrock_api_with_error(self):
        """Test calling the Bedrock API with a connection error."""
        client = BedrockClient()
        
        # Mock the aiohttp.ClientSession.post method to raise an error
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = aiohttp.ClientError("Connection error")
            
            # Call the API (should raise an error)
            with pytest.raises(BedrockError) as excinfo:
                await client._call_bedrock_api(
                    prompt="Test prompt",
                    model_id="amazon.nova-micro-v1:0",
                    temperature=0.7,
                    max_tokens=1000
                )
            
            # Check that the error is correct
            assert "Connection error" in str(excinfo.value)
            assert excinfo.value.error_type == BedrockError.CONNECTION_ERROR
    
    @pytest.mark.asyncio
    async def test_call_bedrock_api_with_error_response(self):
        """Test calling the Bedrock API with an error response."""
        client = BedrockClient()
        
        # Create a mock response with an error status
        mock_response = MagicMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Bad request")
        
        # Mock the aiohttp.ClientSession.post method
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Call the API (should raise an error)
            with pytest.raises(BedrockError) as excinfo:
                await client._call_bedrock_api(
                    prompt="Test prompt",
                    model_id="amazon.nova-micro-v1:0",
                    temperature=0.7,
                    max_tokens=1000
                )
            
            # Check that the error is correct
            assert "400" in str(excinfo.value)
            assert "Bad request" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_get_available_models(self):
        """Test getting available models from Bedrock."""
        client = BedrockClient()
        
        # Mock the boto3 client
        with patch('boto3.client') as mock_boto3_client:
            mock_client = MagicMock()
            mock_boto3_client.return_value = mock_client
            
            # Mock the list_foundation_models method
            mock_client.list_foundation_models.return_value = {
                'modelSummaries': [
                    {
                        'modelId': 'amazon.nova-micro-v1:0',
                        'modelName': 'Amazon Nova Micro',
                        'providerName': 'Amazon'
                    },
                    {
                        'modelId': 'anthropic.claude-3-sonnet-20240229-v1:0',
                        'modelName': 'Claude 3 Sonnet',
                        'providerName': 'Anthropic'
                    }
                ]
            }
            
            # Get the available models
            models = await client.get_available_models()
            
            # Check that the models are correct
            assert len(models) == 2
            assert models[0]['modelId'] == 'amazon.nova-micro-v1:0'
            assert models[1]['modelId'] == 'anthropic.claude-3-sonnet-20240229-v1:0'
            
            # Check that the boto3 client was created with the correct parameters
            mock_boto3_client.assert_called_once_with('bedrock', region_name='us-east-1')
            
            # Check that list_foundation_models was called
            mock_client.list_foundation_models.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_available_models_with_error(self):
        """Test getting available models with an error."""
        client = BedrockClient()
        
        # Mock the boto3 client to raise an error
        with patch('boto3.client') as mock_boto3_client:
            mock_boto3_client.side_effect = Exception("Connection error")
            
            # Get the available models (should raise an error)
            with pytest.raises(BedrockError) as excinfo:
                await client.get_available_models()
            
            # Check that the error is correct
            assert "Connection error" in str(excinfo.value)
            assert excinfo.value.error_type == BedrockError.CONNECTION_ERROR
    
    def test_create_prompt(self, sample_request):
        """Test creating a prompt for the Bedrock API."""
        client = BedrockClient()
        
        # Create a prompt
        prompt = client._create_prompt(sample_request)
        
        # Check that the prompt contains the player input
        assert sample_request.player_input in prompt
        
        # Check that the prompt contains the role description
        assert "helpful bilingual dog companion" in prompt
        
        # Check that the prompt contains instructions
        assert "assist the player with language help" in prompt 