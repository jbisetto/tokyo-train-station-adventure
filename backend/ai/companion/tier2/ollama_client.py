"""
Tokyo Train Station Adventure - Ollama Client

This module provides a client for interacting with Ollama, a local language model server.
It handles API communication, prompt engineering, response parsing, and caching.
"""

import os
import json
import logging
import hashlib
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import aiohttp

from backend.ai.companion.core.models import CompanionRequest

logger = logging.getLogger(__name__)


class OllamaError(Exception):
    """Exception raised for errors in the Ollama API."""
    pass


class OllamaClient:
    """
    Client for interacting with Ollama API.
    
    This client provides methods for generating responses from local language models
    using the Ollama API. It includes caching to improve performance and reduce
    unnecessary API calls.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "llama3",
        cache_enabled: bool = True,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize the Ollama client.
        
        Args:
            base_url: Base URL for the Ollama API
            default_model: Default model to use for generation
            cache_enabled: Whether to enable response caching
            cache_dir: Directory to store cache files (defaults to ~/.ollama_cache)
        """
        self.base_url = base_url
        self.default_model = default_model
        self.cache_enabled = cache_enabled
        
        # Set up cache directory
        if cache_dir is None:
            self.cache_dir = os.path.expanduser("~/.ollama_cache")
        else:
            self.cache_dir = cache_dir
            
        # Create cache directory if it doesn't exist
        if self.cache_enabled and not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
            
        logger.debug(f"Initialized OllamaClient with base_url={base_url}, default_model={default_model}")
    
    async def generate(
        self,
        request: CompanionRequest,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Generate a response from Ollama.
        
        Args:
            request: The player's request
            model: Model to use (defaults to self.default_model)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            The generated response
            
        Raises:
            OllamaError: If there's an error communicating with Ollama
        """
        # Use default model if not specified
        if model is None:
            model = self.default_model
            
        # Check cache first if enabled
        if self.cache_enabled:
            cache_key = self._hash_request(request, model)
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for request {request.request_id}")
                return cached_response
        
        # Create the prompt
        prompt = self._create_prompt(request)
        
        try:
            # Call the Ollama API
            response_text = await self._call_ollama_api(prompt, model, temperature, max_tokens)
            
            # Save to cache if enabled
            if self.cache_enabled:
                self._save_to_cache(cache_key, response_text, model)
                
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating response from Ollama: {e}")
            raise OllamaError(f"Failed to generate response: {str(e)}")
    
    async def get_available_models(self) -> List[str]:
        """
        Get a list of available models from Ollama.
        
        Returns:
            List of model names
            
        Raises:
            OllamaError: If there's an error communicating with Ollama
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status != 200:
                        error_data = await response.json()
                        error_msg = error_data.get("error", "Unknown error")
                        raise OllamaError(f"Failed to get models: {error_msg}")
                    
                    data = await response.json()
                    return [model["name"] for model in data.get("models", [])]
                    
        except Exception as e:
            logger.error(f"Error getting available models from Ollama: {e}")
            raise OllamaError(f"Failed to get available models: {str(e)}")
    
    async def _call_ollama_api(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        Call the Ollama API to generate a response.
        
        Args:
            prompt: The prompt to send to the model
            model: The model to use
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            The generated response
            
        Raises:
            OllamaError: If there's an error communicating with Ollama
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        error_msg = error_data.get("error", "Unknown error")
                        raise OllamaError(f"Failed to generate response: {error_msg}")
                    
                    data = await response.json()
                    return data.get("response", "")
                    
        except aiohttp.ClientError as e:
            logger.error(f"Error calling Ollama API: {e}")
            raise OllamaError(f"Failed to communicate with Ollama: {str(e)}")
    
    def _create_prompt(self, request: CompanionRequest) -> str:
        """
        Create a prompt for the language model based on the request.
        
        Args:
            request: The player's request
            
        Returns:
            The formatted prompt
        """
        # Basic prompt template
        prompt = f"""You are Hachiko, a helpful AI companion in the Tokyo Train Station Adventure game.
The player has asked: "{request.player_input}"

This is a {request.request_type} request.

Please provide a helpful, concise response that addresses the player's question directly.
Focus on being informative and educational about Japanese language and culture.
"""
        
        # Add specific instructions based on request type
        if request.request_type == "translation":
            prompt += "\nProvide the Japanese translation with both kanji/kana and romaji."
        elif request.request_type == "vocabulary":
            prompt += "\nExplain the meaning, usage, and provide example sentences."
        elif request.request_type == "grammar":
            prompt += "\nExplain the grammar point clearly with examples and usage notes."
        elif request.request_type == "culture":
            prompt += "\nProvide accurate cultural information with historical context if relevant."
        
        return prompt
    
    def _hash_request(self, request: CompanionRequest, model: str) -> str:
        """
        Create a hash of the request for cache lookup.
        
        Args:
            request: The player's request
            model: The model being used
            
        Returns:
            A hash string representing the request
        """
        # Combine relevant request properties
        request_str = f"{request.player_input}|{request.request_type}|{model}"
        
        # Create a hash
        return hashlib.md5(request_str.encode()).hexdigest()
    
    def _get_from_cache(self, request_hash: str) -> Optional[str]:
        """
        Get a response from the cache.
        
        Args:
            request_hash: Hash of the request
            
        Returns:
            The cached response, or None if not found
        """
        if not self.cache_enabled:
            return None
            
        cache_file = os.path.join(self.cache_dir, f"{request_hash}.json")
        
        if not os.path.exists(cache_file):
            return None
            
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
                
            # Check if the cache entry is still valid (1 day)
            timestamp = datetime.fromisoformat(cache_data.get("timestamp", "2000-01-01T00:00:00"))
            now = datetime.now()
            
            if (now - timestamp).days > 1:
                logger.debug(f"Cache entry expired for hash {request_hash}")
                return None
                
            return cache_data.get("response")
            
        except Exception as e:
            logger.warning(f"Error reading from cache: {e}")
            return None
    
    def _save_to_cache(self, request_hash: str, response: str, model: str) -> None:
        """
        Save a response to the cache.
        
        Args:
            request_hash: Hash of the request
            response: The response to cache
            model: The model used to generate the response
        """
        if not self.cache_enabled:
            return
            
        cache_file = os.path.join(self.cache_dir, f"{request_hash}.json")
        
        try:
            cache_data = {
                "request_hash": request_hash,
                "response": response,
                "model": model,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
                
            logger.debug(f"Saved response to cache for hash {request_hash}")
            
        except Exception as e:
            logger.warning(f"Error saving to cache: {e}") 