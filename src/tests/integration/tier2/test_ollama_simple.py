#!/usr/bin/env python3
"""
Simple standalone Ollama test

This is a minimal script that tests the Ollama API directly without any project dependencies.
"""

import json
import asyncio
import aiohttp
import logging
import re

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

def remove_thinking_tags(text):
    """Remove the <think>...</think> tags and their contents from the response."""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

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
                    base_model = MODEL.split(':')[0] if ':' in MODEL else MODEL
                    model_found = any(base_model in model for model in models)
                    
                    if not model_found:
                        logger.warning(f"Model '{MODEL}' not found in available models")
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
                
                # Log a sample of the raw response
                if len(response_text) > 300:
                    logger.info(f"Raw response sample: {response_text[:300]}...")
                else:
                    logger.info(f"Raw response: {response_text}")
                
                # Handle different response formats
                if 'application/x-ndjson' in content_type:
                    logger.info("Parsing streaming ndjson response")
                    
                    # Extract all JSON objects from the response
                    json_lines = [line for line in response_text.strip().split('\n') if line.strip()]
                    logger.info(f"Found {len(json_lines)} JSON objects in the response")
                    
                    if not json_lines:
                        logger.error("Empty response")
                        return False
                    
                    # Assemble the complete response from all fragments
                    complete_response = ""
                    for i, line in enumerate(json_lines):
                        try:
                            obj = json.loads(line)
                            partial_response = obj.get("response", "")
                            complete_response += partial_response
                            done = obj.get("done", False)
                            
                            # Only log a sample of fragments to avoid verbose output
                            if i < 5 or i >= len(json_lines) - 5 or i % 20 == 0:
                                logger.info(f"Object {i+1}/{len(json_lines)}: response='{partial_response}', done={done}")
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse JSON line {i+1}: {e}")
                    
                    # Clean up the response by removing thinking tags
                    clean_response = remove_thinking_tags(complete_response)
                    
                    # Log the complete and cleaned responses
                    logger.info(f"Complete assembled response (length: {len(complete_response)}):")
                    logger.info(complete_response)
                    
                    logger.info(f"Clean response (length: {len(clean_response)}):")
                    logger.info(clean_response)
                    
                    return bool(clean_response.strip())
                else:
                    # Handle regular JSON response
                    try:
                        data = json.loads(response_text)
                        result = data.get("response", "")
                        
                        # Clean the response if needed
                        clean_result = remove_thinking_tags(result)
                        
                        logger.info(f"Response: {result}")
                        logger.info(f"Clean response: {clean_result}")
                        
                        return bool(clean_result.strip())
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON response: {e}")
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
