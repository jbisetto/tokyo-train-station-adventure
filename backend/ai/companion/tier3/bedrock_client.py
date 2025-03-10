"""
Tokyo Train Station Adventure - Amazon Bedrock Client

This module provides a client for interacting with Amazon Bedrock, a fully managed
service that offers high-performing foundation models from leading AI companies.
"""

import json
import logging
import asyncio
import aiohttp
import boto3
from typing import Dict, List, Any, Optional, Union
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials

from backend.ai.companion.core.models import CompanionRequest

logger = logging.getLogger(__name__)


class BedrockError(Exception):
    """Exception raised for errors in the Amazon Bedrock API."""
    
    # Error type constants
    CONNECTION_ERROR = "connection_error"
    MODEL_ERROR = "model_error"
    TIMEOUT_ERROR = "timeout_error"
    CONTENT_ERROR = "content_error"
    QUOTA_ERROR = "quota_error"
    UNKNOWN_ERROR = "unknown_error"
    
    def __init__(self, message: str, error_type: str = None):
        """
        Initialize the BedrockError.
        
        Args:
            message: The error message
            error_type: The type of error (one of the constants defined above)
        """
        super().__init__(message)
        self.message = message
        
        # Determine error type from message if not provided
        if error_type is None:
            self.error_type = self._determine_error_type(message)
        else:
            self.error_type = error_type
    
    def _determine_error_type(self, message: str) -> str:
        """
        Determine the error type from the message.
        
        Args:
            message: The error message
            
        Returns:
            The error type
        """
        message_lower = message.lower()
        
        if any(term in message_lower for term in ["connect", "connection", "network", "unreachable", "refused"]):
            return self.CONNECTION_ERROR
        elif any(term in message_lower for term in ["model", "not found", "doesn't exist"]):
            return self.MODEL_ERROR
        elif any(term in message_lower for term in ["timeout", "timed out", "too long"]):
            return self.TIMEOUT_ERROR
        elif any(term in message_lower for term in ["content", "filter", "safety", "inappropriate"]):
            return self.CONTENT_ERROR
        elif any(term in message_lower for term in ["quota", "limit", "throttle", "rate"]):
            return self.QUOTA_ERROR
        else:
            return self.UNKNOWN_ERROR
    
    def is_transient(self) -> bool:
        """
        Check if this error is likely transient and can be retried.
        
        Returns:
            True if the error is transient, False otherwise
        """
        return self.error_type in [
            self.CONNECTION_ERROR,
            self.TIMEOUT_ERROR,
            self.QUOTA_ERROR
        ]


class BedrockClient:
    """
    Client for interacting with Amazon Bedrock.
    
    This class provides methods for generating responses using Amazon Bedrock models.
    """
    
    def __init__(
        self,
        region_name: str = "us-east-1",
        model_id: str = "amazon.nova-micro-v1:0",
        max_tokens: int = 1000
    ):
        """
        Initialize the Bedrock client.
        
        Args:
            region_name: The AWS region to use
            model_id: The model ID to use
            max_tokens: The maximum number of tokens to generate
        """
        self.region_name = region_name
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.logger = logging.getLogger(__name__)
        
        # Log initialization
        self.logger.info(f"Initialized BedrockClient with model {model_id} in region {region_name}")
        
        # Get AWS credentials
        self.session = boto3.Session(region_name=region_name)
        self.credentials = self.session.get_credentials()
    
    async def generate(
        self,
        request: CompanionRequest,
        model_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        prompt: Optional[str] = None
    ) -> str:
        """
        Generate a response to the request.
        
        Args:
            request: The request to process
            model_id: The model ID to use (defaults to self.model_id)
            temperature: The temperature to use for generation
            max_tokens: The maximum number of tokens to generate (defaults to self.max_tokens)
            prompt: A custom prompt to use (if None, one will be created from the request)
            
        Returns:
            The generated response
            
        Raises:
            BedrockError: If there is an error generating the response
        """
        # Use default values if not provided
        model_id = model_id or self.model_id
        max_tokens = max_tokens or self.max_tokens
        
        # Create a prompt if one wasn't provided
        if prompt is None:
            prompt = self._create_prompt(request)
            
        try:
            # Call the API
            self.logger.info(f"Generating response for request {request.request_id} with model {model_id}")
            response = await self._call_bedrock_api(
                prompt=prompt,
                model_id=model_id,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract the completion from the response
            model_provider = model_id.split('.')[0]
            
            if model_provider == "anthropic":
                # For Anthropic models, the completion is in the 'completion' field
                completion = response.get("completion", "")
            elif model_provider == "amazon":
                # For Amazon models, the completion is already extracted in _call_bedrock_api
                completion = response.get("completion", "")
            else:
                # For other models, try to extract the completion from common fields
                completion = (
                    response.get("completion", "") or
                    response.get("content", "") or
                    response.get("text", "") or
                    response.get("generated_text", "") or
                    response.get("output", "") or
                    str(response)
                )
                
            self.logger.info(f"Generated {len(completion)} characters for request {request.request_id}")
            return completion
            
        except BedrockError:
            # Re-raise BedrockError
            raise
        except Exception as e:
            # Handle unexpected errors
            self.logger.error(f"Unexpected error generating response: {str(e)}")
            raise BedrockError(
                f"Unexpected error generating response: {str(e)}",
                error_type=BedrockError.UNKNOWN_ERROR
            )
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get a list of available models from Amazon Bedrock.
        
        Returns:
            A list of model information dictionaries
            
        Raises:
            BedrockError: If there is an error getting the models
        """
        logger.info("Getting available models from Bedrock")
        
        try:
            # Create a Bedrock client
            bedrock = boto3.client('bedrock', region_name=self.region_name)
            
            # Get the list of foundation models
            response = bedrock.list_foundation_models()
            
            # Extract the model summaries
            if "modelSummaries" in response:
                return response["modelSummaries"]
            else:
                return []
                
        except Exception as e:
            # Wrap exceptions in BedrockError
            logger.error(f"Error getting available models: {e}")
            raise BedrockError(f"Error getting available models: {e}")
    
    async def _call_bedrock_api(
        self,
        prompt: str,
        model_id: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        Call the Amazon Bedrock API.
        
        Args:
            prompt: The prompt to send to the API
            model_id: The model ID to use
            temperature: The temperature to use
            max_tokens: The maximum number of tokens to generate
            
        Returns:
            The API response
            
        Raises:
            BedrockError: If there is an error calling the API
        """
        # Determine the model provider from the model ID
        model_provider = model_id.split('.')[0]
        
        # Create the appropriate payload based on the model provider
        if model_provider == "anthropic":
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        elif model_provider == "amazon":
            payload = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": temperature,
                    "topP": 0.9
                }
            }
        else:
            raise BedrockError(f"Unsupported model provider: {model_provider}")
        
        # Convert the payload to JSON
        payload_json = json.dumps(payload)
        
        # Create the URL
        url = f"https://bedrock-runtime.{self.region_name}.amazonaws.com/model/{model_id}/invoke"
        
        # Get the authentication headers
        headers = self._get_auth_headers(url, payload_json)
        
        try:
            # Make the API call
            self.logger.debug(f"Calling Bedrock API with model {model_id}")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    data=payload_json,
                    timeout=30
                ) as response:
                    # Check for errors
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Bedrock API error: {response.status} - {error_text}")
                        raise BedrockError(
                            f"Bedrock API error: {response.status} - {error_text}",
                            error_type=BedrockError.MODEL_ERROR
                        )
                    
                    # Parse the response
                    response_data = json.loads(await response.read())
                    
                    # Extract the completion based on the model provider
                    if model_provider == "anthropic":
                        return response_data
                    elif model_provider == "amazon":
                        # For Amazon models, the response is in a different format
                        return {
                            "completion": response_data.get("results", [{}])[0].get("outputText", ""),
                            "stop_reason": response_data.get("results", [{}])[0].get("completionReason", ""),
                            "usage": {
                                "input_tokens": response_data.get("inputTextTokenCount", 0),
                                "output_tokens": response_data.get("results", [{}])[0].get("tokenCount", 0)
                            }
                        }
                    
                    return response_data
                    
        except aiohttp.ClientError as e:
            self.logger.error(f"Connection error calling Bedrock API: {str(e)}")
            raise BedrockError(
                f"Connection error calling Bedrock API: {str(e)}",
                error_type=BedrockError.CONNECTION_ERROR
            )
        except asyncio.TimeoutError:
            self.logger.error("Timeout calling Bedrock API")
            raise BedrockError(
                "Timeout calling Bedrock API",
                error_type=BedrockError.TIMEOUT_ERROR
            )
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing Bedrock API response: {str(e)}")
            raise BedrockError(
                f"Error parsing Bedrock API response: {str(e)}",
                error_type=BedrockError.CONTENT_ERROR
            )
        except Exception as e:
            self.logger.error(f"Unexpected error calling Bedrock API: {str(e)}")
            raise BedrockError(
                f"Unexpected error calling Bedrock API: {str(e)}",
                error_type=BedrockError.UNKNOWN_ERROR
            )
    
    def _get_auth_headers(self, url: str, body: str) -> Dict[str, str]:
        """
        Get headers with AWS SigV4 authentication.
        
        Args:
            url: The URL for the API call
            body: The request body
            
        Returns:
            Headers with authentication
        """
        # Create an AWS request
        request = AWSRequest(
            method='POST',
            url=url,
            data=body.encode('utf-8')
        )
        
        # Add content type header
        request.headers.add_header('Content-Type', 'application/json')
        
        # Sign the request with SigV4
        SigV4Auth(self.credentials, 'bedrock', self.region_name).add_auth(request)
        
        # Return the headers
        return dict(request.headers)
    
    def _create_prompt(self, request: CompanionRequest) -> str:
        """
        Create a prompt for the Bedrock API.
        
        Args:
            request: The request to process
            
        Returns:
            A prompt string
        """
        # Create a simple prompt format that works well with Amazon models
        return (
            "You are a helpful bilingual dog companion in a Japanese train station. "
            f"The player has asked: \"{request.player_input}\" "
            "Your role is to assist the player with language help, directions, and cultural information. "
            "Provide a helpful, concise response in English."
        )
