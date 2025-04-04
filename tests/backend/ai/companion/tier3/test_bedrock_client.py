"""
Tests for the Amazon Bedrock client.

This module contains tests for the Amazon Bedrock client, which is used
to interact with Amazon Bedrock models for the Tier 3 processor.
"""

import pytest
import json
import boto3
from unittest.mock import patch, MagicMock, AsyncMock
import datetime

from src.ai.companion.core.models import CompanionRequest
from src.ai.companion.tier3.bedrock_client import BedrockClient, BedrockError


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
    """Return a sample response from the Bedrock API."""
    return {
        "output": {
            "message": {
                "content": [
                    {
                        "text": "「東京に行きたいです」(Tōkyō ni ikitai desu) is how you say 'I want to go to Tokyo' in Japanese."
                    }
                ],
                "role": "assistant"
            }
        },
        "stopReason": "end_turn",
        "usage": {
            "inputTokens": 42,
            "outputTokens": 128,
            "totalTokens": 170,
            "cacheReadInputTokenCount": 0,
            "cacheWriteInputTokenCount": 0
        }
    }


class TestBedrockClient:
    """Tests for the BedrockClient class."""
    
    def test_initialization(self):
        """Test initialization of the BedrockClient."""
        client = BedrockClient()
        
        # Check that the client has the correct default values
        assert client.region_name == "us-east-1"
        assert client.default_model == "amazon.nova-micro-v1:0"
        assert client.max_tokens == 512
        
        # Test with custom values
        custom_client = BedrockClient(
            region_name="us-west-2",
            model_id="amazon.titan-text-express-v1",
            max_tokens=500
        )
        
        assert custom_client.region_name == "us-west-2"
        assert custom_client.default_model == "amazon.titan-text-express-v1"
        assert custom_client.max_tokens == 500
    
    @pytest.mark.asyncio
    async def test_generate(self, sample_bedrock_response):
        """Test generating a response."""
        client = BedrockClient()
        
        # Mock the _call_bedrock_api method
        with patch.object(client, '_call_bedrock_api') as mock_call_api:
            # Set the return value of the mocked method
            mock_call_api.return_value = sample_bedrock_response
            
            # Create a request
            request = CompanionRequest(
                request_id="test-123",
                player_input="What does 'I want to go to Tokyo' mean in Japanese?",
                request_type="language_help",
                timestamp=datetime.datetime(2023, 1, 1)
            )
            
            # Call generate
            response = await client.generate(
                request, 
                prompt="What does 'I want to go to Tokyo' mean in Japanese?"
            )
            
            # Check the response - generate() returns just the completion string
            assert response == "「東京に行きたいです」(Tōkyō ni ikitai desu) is how you say 'I want to go to Tokyo' in Japanese."
            
            # Check that _call_bedrock_api was called with the correct arguments
            mock_call_api.assert_called_once()
            args, _ = mock_call_api.call_args
            assert args[0] == "amazon.nova-micro-v1:0"  # model_id
            assert "messages" in args[1]  # payload
    
    @pytest.mark.asyncio
    async def test_generate_with_custom_parameters(self, sample_bedrock_response):
        """Test generating a response with custom parameters."""
        client = BedrockClient()
        
        # Mock the _call_bedrock_api method
        with patch.object(client, '_call_bedrock_api') as mock_call_api:
            # Set the return value of the mocked method
            mock_call_api.return_value = sample_bedrock_response
            
            # Create a request with custom parameters in additional_params
            request = CompanionRequest(
                request_id="test-123",
                player_input="What does 'I want to go to Tokyo' mean in Japanese?",
                request_type="language_help",
                timestamp=datetime.datetime(2023, 1, 1),
                additional_params={
                    "temperature": 0.5,
                    "top_p": 0.8,
                    "max_tokens": 500
                }
            )
            
            # Call generate with custom parameters directly
            response = await client.generate(
                request,
                temperature=0.5,
                max_tokens=500,
                prompt="What does 'I want to go to Tokyo' mean in Japanese?"
            )
            
            # Check the response - generate() returns just the completion string
            assert response == "「東京に行きたいです」(Tōkyō ni ikitai desu) is how you say 'I want to go to Tokyo' in Japanese."
            
            # Check that _call_bedrock_api was called with the correct arguments
            mock_call_api.assert_called_once()
            args, _ = mock_call_api.call_args
            assert args[0] == "amazon.nova-micro-v1:0"  # model_id
            
            # For Nova models, temperature and max_tokens are in the inferenceConfig
            payload = args[1]
            if "nova" in client.default_model.lower():
                assert payload["inferenceConfig"]["temperature"] == 0.5
                assert payload["inferenceConfig"]["maxTokens"] == 500
    
    @pytest.mark.asyncio
    async def test_generate_with_error(self, sample_request):
        """Test generating a response with an error."""
        client = BedrockClient()
        
        # Mock the _call_bedrock_api method to raise an error
        with patch.object(client, '_call_bedrock_api') as mock_call_api:
            mock_call_api.side_effect = BedrockError("Test error", BedrockError.API_ERROR)
            
            # Generate a response (should raise an error)
            with pytest.raises(BedrockError) as excinfo:
                await client.generate(sample_request, prompt="test prompt")
            
            # Check that the error is correct
            assert "Test error" in str(excinfo.value)
            assert excinfo.value.error_type == BedrockError.API_ERROR
    
    @pytest.mark.asyncio
    async def test_generate_with_quota_exceeded(self, sample_request):
        """Test generating a response when the quota is exceeded."""
        client = BedrockClient()
        
        # Mock the _call_bedrock_api method to raise a quota error
        with patch.object(client, '_call_bedrock_api') as mock_call_api:
            mock_call_api.side_effect = BedrockError("Quota exceeded", BedrockError.QUOTA_ERROR)
            
            # Generate a response (should raise a quota error)
            with pytest.raises(BedrockError) as excinfo:
                await client.generate(sample_request, prompt="test prompt")
            
            # Check that the error is correct
            assert "Quota exceeded" in str(excinfo.value)
            assert excinfo.value.error_type == BedrockError.QUOTA_ERROR
    
    def test_call_bedrock_api(self, sample_bedrock_response):
        """Test calling the Bedrock API."""
        client = BedrockClient()
        
        # Mock the boto3 client
        with patch.object(client, 'client') as mock_client:
            # Set up the mock response
            mock_response = {
                "body": MagicMock()
            }
            mock_response["body"].read.return_value = json.dumps(sample_bedrock_response).encode('utf-8')
            mock_client.invoke_model.return_value = mock_response
            
            # Call the API
            response = client._call_bedrock_api(
                "amazon.nova-micro-v1:0",
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": "Test prompt"}]
                        }
                    ],
                    "inferenceConfig": {
                        "maxTokens": 1000,
                        "temperature": 0.7,
                        "topP": 0.9
                    }
                }
            )
            
            # Check the response
            assert response == sample_bedrock_response
            
            # Check that invoke_model was called correctly
            mock_client.invoke_model.assert_called_once()
            kwargs = mock_client.invoke_model.call_args[1]
            assert kwargs["modelId"] == "amazon.nova-micro-v1:0"
            assert kwargs["contentType"] == "application/json"
            assert kwargs["accept"] == "application/json"
            
            # Parse the body to check the payload
            payload = json.loads(kwargs["body"])
            assert "messages" in payload
            assert "inferenceConfig" in payload
    
    def test_call_bedrock_api_error(self):
        """Test error handling when calling the Bedrock API."""
        client = BedrockClient()
        
        # Mock the boto3 client to raise an exception
        with patch.object(client, 'client') as mock_client:
            mock_client.invoke_model.side_effect = Exception("Test error")
            
            # Call the API (should raise a BedrockError)
            with pytest.raises(BedrockError) as excinfo:
                client._call_bedrock_api(
                    "amazon.nova-micro-v1:0",
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": [{"text": "Test prompt"}]
                            }
                        ],
                        "inferenceConfig": {
                            "maxTokens": 1000,
                            "temperature": 0.7,
                            "topP": 0.9
                        }
                    }
                )
            
            # Check that the error is correct
            assert "Test error" in str(excinfo.value)
            assert excinfo.value.error_type == BedrockError.API_ERROR
    
    def test_redact_sensitive_info(self):
        """Test redacting sensitive information."""
        client = BedrockClient()
        
        # Test with a dictionary containing sensitive information
        sensitive_data = {
            "api_key": "my-secret-key",
            "credentials": {
                "access_key": "ABCDEFG",
                "secret_key": "12345"
            },
            "safe_data": "this is safe",
            "parameters": {
                "temperature": 0.7
            }
        }
        
        redacted = client._redact_sensitive_info(sensitive_data)
        
        assert redacted["api_key"] == "[REDACTED]"
        assert redacted["credentials"] == "[REDACTED]"
        assert redacted["safe_data"] == "this is safe"
        assert redacted["parameters"]["temperature"] == 0.7
    
    @pytest.mark.asyncio
    async def test_get_available_models(self):
        """Test getting available models from Bedrock."""
        client = BedrockClient()
        
        # Mock the boto3.client
        with patch('boto3.client') as mock_boto3_client:
            # Set up the mock response
            mock_bedrock_client = MagicMock()
            mock_boto3_client.return_value = mock_bedrock_client
            
            mock_response = {
                "modelSummaries": [
                    {
                        "modelId": "amazon.nova-micro-v1:0",
                        "modelName": "Nova Micro"
                    },
                    {
                        "modelId": "anthropic.claude-v2",
                        "modelName": "Claude 2"
                    }
                ]
            }
            mock_bedrock_client.list_foundation_models.return_value = mock_response
            
            # Get the available models
            models = await client.get_available_models()
            
            # Check the response
            assert len(models) == 2
            assert models[0]["modelId"] == "amazon.nova-micro-v1:0"
            assert models[1]["modelId"] == "anthropic.claude-v2"
            
            # Check that list_foundation_models was called
            mock_bedrock_client.list_foundation_models.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_available_models_with_error(self):
        """Test error handling when getting available models."""
        client = BedrockClient()
        
        # Mock the boto3.client to raise an exception
        with patch('boto3.client') as mock_boto3_client:
            mock_bedrock_client = MagicMock()
            mock_boto3_client.return_value = mock_bedrock_client
            mock_bedrock_client.list_foundation_models.side_effect = Exception("Test error")
            
            # Get available models (should raise a BedrockError)
            with pytest.raises(BedrockError) as excinfo:
                await client.get_available_models()
            
            # Check that the error is correct
            assert "Test error" in str(excinfo.value) 