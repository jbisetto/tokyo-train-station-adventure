#!/usr/bin/env python3
"""
Simple standalone Ollama test

This is a minimal script that tests the Ollama API directly without any project dependencies.
"""

import json
import asyncio
import aiohttp
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Configuration
OLLAMA_URL = "http://localhost:11434"
MODEL = "deepseek-r1:latest"
PROMPT = "You are a helpful assistant. Say hello in Japanese. Keep it brief."

async def test_ollama():
    """Test basic Ollama functionality"""
    logger.info(f"Testing Ollama at {OLLAMA_URL} with model {MODEL}")
    
    # Check if Ollama is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_URL}/api/version") as response:
                if response.status == 200:
                    version_data = await response.json()
                    logger.info(f"Ollama is running (version: {version_data.get('version', 'unknown')})")
                else:
                    logger.error(f"Ollama returned status code {response.status}")
                    return False
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        return False
    
    # List available models
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_URL}/api/tags") as response:
                if response.status == 200:
                    models_data = await response.json()
                    models = [model["name"] for model in models_data.get("models", [])]
                    logger.info(f"Available models: {models}")
                    
                    # Check if our model is available
                    if MODEL not in models and MODEL.split(':')[0] not in models:
                        logger.warning(f"Model {MODEL} not found in available models")
                        logger.warning(f"You may need to run: ollama pull {MODEL}")
                else:
                    logger.error(f"Failed to list models: status {response.status}")
                    return False
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        return False
    
    # Test text generation
    try:
        payload = {
            "model": MODEL,
            "prompt": PROMPT,
            "options": {
                "temperature": 0.7,
                "num_predict": 100,
                "stream": False
            }
        }
        
        logger.info(f"Sending generation request with payload: {json.dumps(payload, indent=2)}")
        
        async with aiohttp.ClientSession() as session:
            start_time = asyncio.get_event_loop().time()
            
            async with session.post(f"{OLLAMA_URL}/api/generate", json=payload) as response:
                elapsed = asyncio.get_event_loop().time() - start_time
                logger.info(f"Response received in {elapsed:.2f} seconds (status: {response.status})")
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Generation failed: {error_text}")
                    return False
                
                # Get the response content and content type
                content_type = response.headers.get('content-type', '')
                response_text = await response.text()
                
                logger.info(f"Response content type: {content_type}")
                logger.info(f"Raw response: {response_text[:500]}")
                
                # Handle different response formats
                if 'application/x-ndjson' in content_type:
                    logger.info("Parsing streaming ndjson response")
                    # Parse the last line which should contain the final response
                    lines = [line for line in response_text.strip().split('\n') if line.strip()]
                    if not lines:
                        logger.error("Empty response")
                        return False
                    
                    last_line = lines[-1]
                    try:
                        last_data = json.loads(last_line)
                        result = last_data.get("response", "")
                        logger.info(f"Final response: {result}")
                        return bool(result)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON: {e}")
                        return False
                else:
                    # Regular JSON response
                    try:
                        data = json.loads(response_text)
                        result = data.get("response", "")
                        logger.info(f"Response: {result}")
                        return bool(result)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON: {e}")
                        return False
    
    except Exception as e:
        logger.error(f"Error during generation test: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("Starting Ollama tests")
    
    success = await test_ollama()
    
    if success:
        logger.info("All tests passed successfully!")
    else:
        logger.error("Tests failed. Check the logs for details.")

if __name__ == "__main__":
    asyncio.run(main()) 