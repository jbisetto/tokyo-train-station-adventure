import logging
import asyncio
import uuid
import pytest
from src.ai.companion.tier2.ollama_client import OllamaClient, OllamaError
from src.ai.companion.config import get_config
from src.ai.companion.core.models import CompanionRequest


@pytest.fixture
async def config():
    """Fixture for Ollama configuration."""
    tier2_config = get_config('tier2', {})
    ollama_config = tier2_config.get('ollama', {})
    return {
        "base_url": ollama_config.get("base_url", "http://localhost:11434"),
        "default_model": ollama_config.get("default_model", "deepseek-r1:latest"),
        "temperature": ollama_config.get("temperature", 0.7),
        "max_tokens": ollama_config.get("max_tokens", 500),
    }


@pytest.fixture
async def client(config):
    """Fixture for Ollama client."""
    client_instance = OllamaClient(
        base_url=config["base_url"],
        default_model=config["default_model"],
        cache_enabled=False  # Disable cache for testing
    )
    return client_instance

async def test_ollama_connectivity(client, config):
    """Test the connection to Ollama."""
    # Check if Ollama is available by making a request to list models
    models = await client.get_available_models()
    print(f"Available models: {models}")
    
    # If we got this far, Ollama is running and responding
    print("Ollama is available and responding to requests")
    
    assert config["default_model"] in models, f"Model {config['default_model']} not found in available models"
    print("Connectivity test passed!")

async def test_simple_generation(client, config):
    """Test a simple text generation."""
    prompt = "Translate 'Hello' to Japanese"
    print(f"Testing generation with prompt: '{prompt}'")
    
    # Create a CompanionRequest object
    request = CompanionRequest(
        request_id=str(uuid.uuid4()),
        player_input=prompt,
        request_type="translation"
    )
    
    response = await client.generate(
        request=request,
        model=config["default_model"],
        temperature=config["temperature"],
        max_tokens=config["max_tokens"]
    )
    
    print(f"Response: {response}")
    assert response, "Empty response received"
    print("Simple generation test passed!")

async def test_request_format(client, config):
    """Test different request formats and parameter handling."""
    # Test different temperature values
    for temp in [0.1, 0.5, 0.9]:
        request = CompanionRequest(
            request_id=str(uuid.uuid4()),
            player_input="Count from 1 to 3",
            request_type="test"
        )
        response = await client.generate(
            request=request,
            temperature=temp,
            max_tokens=20
        )
        print(f"Response with temperature {temp}: {response[:30]}...")
    
    # Test different max_tokens values
    for tokens in [10, 50, 100]:
        request = CompanionRequest(
            request_id=str(uuid.uuid4()),
            player_input="Write a short poem",
            request_type="test"
        )
        response = await client.generate(
            request=request,
            max_tokens=tokens
        )
        print(f"Response with max_tokens {tokens}: length={len(response)}")
    
    print("Request format test passed!")

async def test_direct_api_call(config):
    """Test a direct API call to Ollama without using the client."""
    import aiohttp
    import json
    
    base_url = config["base_url"]
    model = config["default_model"]
    
    async with aiohttp.ClientSession() as session:
        url = f"{base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": "What is the capital of Japan?",
            "options": {
                "temperature": 0.7,
                "num_predict": 100
            }
        }
        
        print(f"Making direct API call to {url} with model {model}")
        async with session.post(url, json=payload) as response:
            assert response.status == 200, f"API call failed with status {response.status}"
            data = await response.text()
            print(f"Raw response: {data[:100]}...")
            
            # Parse the JSON response (handling NDJSON if necessary)
            if "content-type" in response.headers and "application/x-ndjson" in response.headers["content-type"].lower():
                # Handle NDJSON response
                lines = data.strip().split('\n')
                responses = []
                for line in lines:
                    if line.strip():
                        try:
                            json_obj = json.loads(line)
                            if "response" in json_obj:
                                responses.append(json_obj["response"])
                        except json.JSONDecodeError:
                            print(f"Error parsing JSON: {line}")
                
                final_response = "".join(responses)
            else:
                # Handle regular JSON response
                json_response = json.loads(data)
                final_response = json_response.get("response", "")
                
            print(f"Final response: {final_response}")
            assert final_response, "Empty response received"
            
    print("Direct API call test passed!")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests directly (without pytest) if executed as a script
    async def run_tests():
        print("=== Running Ollama Integration Tests ===")
        
        # Manual implementation of the test_config fixture
        tier2_config = get_config('tier2', {})
        ollama_config = tier2_config.get('ollama', {})
        config = {
            "base_url": ollama_config.get("base_url", "http://localhost:11434"),
            "default_model": ollama_config.get("default_model", "deepseek-r1:latest"),
            "temperature": ollama_config.get("temperature", 0.7),
            "max_tokens": ollama_config.get("max_tokens", 500),
        }
        
        # Manual implementation of the client fixture
        client_instance = OllamaClient(
            base_url=config["base_url"],
            default_model=config["default_model"],
            cache_enabled=False  # Disable cache for testing
        )
        
        try:
            print("\n== Testing Ollama Connectivity ==")
            await test_ollama_connectivity(client_instance, config)
            
            print("\n== Testing Simple Generation ==")
            await test_simple_generation(client_instance, config)
            
            print("\n== Testing Request Format ==")
            await test_request_format(client_instance, config)
            
            print("\n== Testing Direct API Call ==")
            await test_direct_api_call(config)
            
            print("\n=== All tests completed ===")
        except Exception as e:
            print(f"\n=== Test failed with error: {str(e)} ===")
            import traceback
            traceback.print_exc()
    
    # Run the tests
    asyncio.run(run_tests()) 