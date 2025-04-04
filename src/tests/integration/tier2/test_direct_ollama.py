#!/usr/bin/env python3
"""
Direct Ollama API Test

This script directly tests the Ollama API using raw HTTP requests,
completely independent of the application code. This helps isolate
API connectivity and format issues.

Usage:
    python test_direct_ollama.py [--model MODEL] [--url URL]

Example:
    python test_direct_ollama.py --model deepseek-r1:latest
"""

import os
import sys
import json
import argparse
import asyncio
import logging
from typing import Dict, Any, Optional

try:
    import aiohttp
except ImportError:
    print("Error: aiohttp package is required. Install with 'pip install aiohttp'")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_URL = "http://localhost:11434"
DEFAULT_MODEL = "deepseek-r1:latest"
TEST_PROMPT = "You are a helpful assistant. Say hello in Japanese. Keep it brief."

class OllamaDirectTester:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model
    
    async def test_list_models(self) -> bool:
        """Test listing available models from Ollama."""
        logger.info(f"Testing model listing from Ollama at {self.base_url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to get model list. Status: {response.status}, Error: {error_text}")
                        return False
                    
                    data = await response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    
                    logger.info(f"Available models: {models}")
                    
                    # Check if the specified model is available
                    base_model = self.model.split(':')[0] if ':' in self.model else self.model
                    model_found = any(base_model in model for model in models)
                    
                    if not model_found:
                        logger.warning(f"Model '{self.model}' not found in available models.")
                        logger.warning(f"You may need to pull it first with: ollama pull {self.model}")
                    else:
                        logger.info(f"Model '{self.model}' is available.")
                    
                    return True
        
        except aiohttp.ClientError as e:
            logger.error(f"Connection error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return False
    
    async def test_generation(self) -> bool:
        """Test text generation with Ollama."""
        logger.info(f"Testing text generation with model '{self.model}'")
        
        # Prepare the request payload
        payload = {
            "model": self.model,
            "prompt": TEST_PROMPT,
            "options": {
                "temperature": 0.7,
                "num_predict": 100,
                "stream": False
            }
        }
        
        logger.info(f"Request payload: {json.dumps(payload, indent=2)}")
        
        try:
            async with aiohttp.ClientSession() as session:
                logger.info(f"Sending request to {self.base_url}/api/generate")
                
                start_time = asyncio.get_event_loop().time()
                
                async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                    end_time = asyncio.get_event_loop().time()
                    elapsed = end_time - start_time
                    
                    logger.info(f"Response received in {elapsed:.2f} seconds")
                    logger.info(f"Response status: {response.status}")
                    
                    if response.status != 200:
                        try:
                            error_data = await response.json()
                            error_message = error_data.get("error", "Unknown error")
                            logger.error(f"Error generating text: {error_message}")
                        except:
                            error_text = await response.text()
                            logger.error(f"Error response: {error_text}")
                        return False
                    
                    # Handle both regular JSON and streaming ndjson responses
                    content_type = response.headers.get('content-type', '')
                    response_text = await response.text()
                    
                    if 'application/x-ndjson' in content_type:
                        # Handle streaming response format
                        logger.info("Received ndjson streaming response")
                        
                        # Extract the last complete JSON object which contains the final response
                        json_lines = [line for line in response_text.strip().split('\n') if line.strip()]
                        if not json_lines:
                            logger.error("Empty response received")
                            return False
                            
                        try:
                            # The final response should be in the last complete JSON object
                            final_data = json.loads(json_lines[-1])
                            response_text = final_data.get("response", "")
                            logger.info(f"Final response extracted: {response_text}")
                            return True if response_text else False
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse ndjson response: {e}")
                            return False
                    else:
                        # Handle regular JSON response
                        try:
                            data = json.loads(response_text)
                            logger.info("Response structure:")
                            for key, value in data.items():
                                if isinstance(value, str) and len(value) > 100:
                                    logger.info(f"  {key}: {value[:100]}... ({len(value)} chars)")
                                else:
                                    logger.info(f"  {key}: {value}")
                            
                            response_text = data.get("response", "")
                            if response_text:
                                logger.info(f"Generated text: {response_text}")
                                return True
                            else:
                                logger.warning("Empty response received")
                                return False
                        
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON response: {response_text[:200]}...")
                            return False
        
        except aiohttp.ClientError as e:
            logger.error(f"Connection error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return False

async def run_tests(base_url: str, model: str) -> None:
    """Run all Ollama API tests."""
    logger.info("=== Starting Direct Ollama API Tests ===")
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Model: {model}")
    
    tester = OllamaDirectTester(base_url, model)
    
    # Test 1: List models
    logger.info("\n== Test 1: List Available Models ==")
    models_success = await tester.test_list_models()
    
    # Test 2: Generate text
    logger.info("\n== Test 2: Generate Text ==")
    generation_success = await tester.test_generation()
    
    # Summary
    logger.info("\n=== Test Results ===")
    logger.info(f"List Models: {'SUCCESS' if models_success else 'FAILED'}")
    logger.info(f"Generate Text: {'SUCCESS' if generation_success else 'FAILED'}")
    
    if not models_success or not generation_success:
        logger.warning("\nSome tests failed. Check the logs for details.")
        
        if not models_success:
            logger.warning("- Could not connect to Ollama or list models")
        
        if not generation_success:
            logger.warning("- Text generation failed - check if the model is properly installed")
            logger.warning(f"  Try running: ollama pull {model}")
    else:
        logger.info("\nAll tests passed successfully!")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Test Ollama API directly')
    parser.add_argument('--url', default=DEFAULT_URL, help=f'Ollama API URL (default: {DEFAULT_URL})')
    parser.add_argument('--model', default=DEFAULT_MODEL, help=f'Model to test (default: {DEFAULT_MODEL})')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_tests(args.url, args.model)) 