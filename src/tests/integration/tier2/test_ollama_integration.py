"""
Integration Test for Ollama Client

This test directly tests the Ollama client's connection to a local Ollama instance
with the deepseek model.
"""

import os
import sys
import asyncio
import pytest
import logging
from unittest.mock import patch
from typing import Optional

# Add the root directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../../../.."))
sys.path.insert(0, root_dir)

from src.ai.companion.tier2.ollama_client import OllamaClient, OllamaError
from src.ai.companion.core.models import CompanionRequest
from src.ai.companion.config import get_config

logger = logging.getLogger(__name__)

@pytest.fixture
def test_config():
    """Get test configuration from companion.yaml"""
    tier2_config = get_config('tier2', {})
    ollama_config = tier2_config.get('ollama', {})
    
    # Return the test configuration with defaults if not specified
    return {
        "base_url": ollama_config.get("base_url", "http://localhost:11434"),
        "default_model": ollama_config.get("default_model", "deepseek-r1:latest"),
        "temperature": ollama_config.get("temperature", 0.7),
        "max_tokens": ollama_config.get("max_tokens", 500),
    }

@pytest.fixture
def client(test_config):
    """Create an OllamaClient instance for testing."""
    return OllamaClient(
        base_url=test_config["base_url"],
        default_model=test_config["default_model"],
        cache_enabled=False  # Disable cache for testing
    )

@pytest.mark.asyncio
async def test_ollama_connectivity(client, test_config):
    """Test basic connectivity to Ollama API."""
    try:
        models = await client.get_available_models()
        assert len(models) > 0, "No models returned from Ollama server"
        print(f"Available models: {models}")
        
        # Check if the default model is available
        default_model = test_config["default_model"]
        # Strip version tag if present (models list may not include version)
        base_model = default_model.split(':')[0] if ':' in default_model else default_model
        
        model_found = any(base_model in model for model in models)
        if not model_found:
            print(f"WARNING: Default model '{default_model}' not found in available models.")
            print(f"You may need to pull it first with: ollama pull {default_model}")
        else:
            print(f"Default model '{default_model}' is available.")
    
    except OllamaError as e:
        pytest.fail(f"Failed to connect to Ollama server: {str(e)}")
    except Exception as e:
        pytest.fail(f"Unexpected error during connectivity test: {str(e)}")

@pytest.mark.asyncio
async def test_simple_generation(client, test_config):
    """Test simple text generation with the deepseek model."""
    # Create a basic test request
    request = CompanionRequest(
        request_id="test-simple-generation",
        player_input="How do I say 'hello' in Japanese?",
        request_type="test",
        timestamp="2025-03-20T17:37:37",
        game_context={"player_location": "station_entrance"},
        additional_params={}
    )
    
    try:
        # Simple prompt for testing
        test_prompt = "You are a helpful AI assistant. Please answer the following question briefly: How do I say 'hello' in Japanese?"
        
        # Generate response using the configured model
        response = await client.generate(
            request=request,
            model=test_config["default_model"],
            temperature=test_config["temperature"],
            max_tokens=test_config["max_tokens"],
            prompt=test_prompt
        )
        
        assert response, "Empty response received from Ollama"
        assert len(response) > 0, "Response is empty"
        
        print(f"Generated response: {response}")
        
        # Check for expected content (very basic check)
        assert any(word in response.lower() for word in ["konnichiwa", "こんにちは", "hello", "japanese"]), \
            "Response doesn't contain expected content"
    
    except OllamaError as e:
        pytest.fail(f"Error generating response: {str(e)}")
    except Exception as e:
        pytest.fail(f"Unexpected error during generation test: {str(e)}")

@pytest.mark.asyncio
async def test_request_format(client, test_config):
    """Test the request format sent to Ollama API."""
    
    # Create a test request
    request = CompanionRequest(
        request_id="test-request-format",
        player_input="What's the best way to get to Tokyo Station?",
        request_type="test",
        timestamp="2025-03-20T17:37:37",
        game_context={"player_location": "shinjuku"},
        additional_params={}
    )
    
    # Track the request payload
    captured_payload = {}
    
    # Original _call_ollama_api method
    original_method = client._call_ollama_api
    
    # Create a mock implementation that captures the payload
    async def mock_call_ollama_api(prompt, model, temperature, max_tokens):
        nonlocal captured_payload
        captured_payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        # Still call the original method to test actual functionality
        return await original_method(prompt, model, temperature, max_tokens)
    
    try:
        # Patch the method to use our mock
        with patch.object(client, '_call_ollama_api', side_effect=mock_call_ollama_api):
            test_prompt = "You are a helpful guide. Please answer how to get to Tokyo Station."
            
            # This will call our mock method which captures the payload
            await client.generate(
                request=request,
                model=test_config["default_model"],
                temperature=test_config["temperature"],
                max_tokens=test_config["max_tokens"],
                prompt=test_prompt
            )
            
            # Verify payload format
            assert "model" in captured_payload, "Model missing from payload"
            assert "prompt" in captured_payload, "Prompt missing from payload"
            assert "temperature" in captured_payload, "Temperature missing from payload"
            assert "max_tokens" in captured_payload, "Max tokens missing from payload"
            
            # Print captured payload for debugging
            print("Request payload format:")
            print(f"- Model: {captured_payload['model']}")
            print(f"- Temperature: {captured_payload['temperature']}")
            print(f"- Max tokens: {captured_payload['max_tokens']}")
            print(f"- Prompt length: {len(captured_payload['prompt'])} characters")
    
    except OllamaError as e:
        # This test may fail if Ollama isn't running, but we still want to see the payload
        print("Error occurred, but here's the captured payload format:")
        for key, value in captured_payload.items():
            if key == "prompt":
                print(f"- Prompt length: {len(value)} characters")
            else:
                print(f"- {key}: {value}")
        pytest.fail(f"Error during request format test: {str(e)}")
    except Exception as e:
        pytest.fail(f"Unexpected error during request format test: {str(e)}")

@pytest.mark.asyncio
async def test_direct_api_call(test_config):
    """Test direct API call to Ollama without using the client class."""
    import json
    import aiohttp
    
    base_url = test_config["base_url"]
    model = test_config["default_model"]
    
    # Simple payload for testing
    payload = {
        "model": model,
        "prompt": "Say hello in Japanese",
        "options": {
            "temperature": 0.7,
            "num_predict": 100,
            "stream": False
        }
    }
    
    try:
        print(f"Sending direct API request to {base_url}/api/generate")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{base_url}/api/generate", json=payload) as response:
                status = response.status
                print(f"Response status: {status}")
                
                if status == 200:
                    data = await response.json()
                    response_text = data.get("response", "")
                    print(f"Raw API response: {json.dumps(data, indent=2)}")
                    print(f"Response text: {response_text}")
                    
                    assert response_text, "Empty response received from direct API call"
                else:
                    error_text = await response.text()
                    print(f"Error response: {error_text}")
                    pytest.fail(f"API call failed with status {status}: {error_text}")
    
    except aiohttp.ClientError as e:
        pytest.fail(f"Network error during direct API call: {str(e)}")
    except Exception as e:
        pytest.fail(f"Unexpected error during direct API call: {str(e)}")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests directly (without pytest) if executed as a script
    async def run_tests():
        print("=== Running Ollama Integration Tests ===")
        config = test_config()
        client_instance = client(config)
        
        print("\n== Testing Ollama Connectivity ==")
        await test_ollama_connectivity(client_instance, config)
        
        print("\n== Testing Simple Generation ==")
        await test_simple_generation(client_instance, config)
        
        print("\n== Testing Request Format ==")
        await test_request_format(client_instance, config)
        
        print("\n== Testing Direct API Call ==")
        await test_direct_api_call(config)
        
        print("\n=== All tests completed ===")
    
    # Run the tests
    asyncio.run(run_tests()) 