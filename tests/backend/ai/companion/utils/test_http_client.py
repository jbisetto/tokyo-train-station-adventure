"""
Tests for the HTTP client utilities.
"""

import pytest
import httpx
import json
from unittest.mock import AsyncMock, patch, MagicMock

from backend.ai.companion.utils.http_client import make_api_request


class MockAsyncClient:
    """A mock for httpx.AsyncClient that works with async context managers."""
    
    def __init__(self):
        self.get = AsyncMock()
        self.post = AsyncMock()
        self.put = AsyncMock()
        self.delete = AsyncMock()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.mark.asyncio
async def test_make_api_request_get(monkeypatch):
    """Test that make_api_request makes a GET request correctly."""
    # Create a mock response
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"data": "test_data"}
    
    # Create a mock client
    mock_client = MockAsyncClient()
    mock_client.get.return_value = mock_response
    
    # Patch the AsyncClient class
    monkeypatch.setattr("httpx.AsyncClient", lambda: mock_client)
    
    # Call the function
    result = await make_api_request("https://example.com/api")
    
    # Check that the client was called correctly
    mock_client.get.assert_called_once_with(
        "https://example.com/api", 
        headers={}, 
        timeout=10
    )
    
    # Check that the response was processed correctly
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    
    # Check the result
    assert result == {"data": "test_data"}


@pytest.mark.asyncio
async def test_make_api_request_post(monkeypatch):
    """Test that make_api_request makes a POST request correctly."""
    # Create a mock response
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"status": "success"}
    
    # Create a mock client
    mock_client = MockAsyncClient()
    mock_client.post.return_value = mock_response
    
    # Patch the AsyncClient class
    monkeypatch.setattr("httpx.AsyncClient", lambda: mock_client)
    
    # Call the function
    data = {"key": "value"}
    headers = {"Content-Type": "application/json"}
    result = await make_api_request(
        "https://example.com/api", 
        method="POST", 
        data=data, 
        headers=headers
    )
    
    # Check that the client was called correctly
    mock_client.post.assert_called_once_with(
        "https://example.com/api", 
        json=data, 
        headers=headers, 
        timeout=10
    )
    
    # Check the result
    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_make_api_request_error(monkeypatch):
    """Test that make_api_request handles errors correctly."""
    # Create a mock response that raises an error
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPError("API error")
    
    # Create a mock client
    mock_client = MockAsyncClient()
    mock_client.get.return_value = mock_response
    
    # Patch the AsyncClient class
    monkeypatch.setattr("httpx.AsyncClient", lambda: mock_client)
    
    # Call the function and check that it raises the expected error
    with pytest.raises(httpx.HTTPError, match="API error"):
        await make_api_request("https://example.com/api")
    
    # Check that the client was called
    mock_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_make_api_request_invalid_method(monkeypatch):
    """Test that make_api_request handles invalid methods correctly."""
    # Create a mock client
    mock_client = MockAsyncClient()
    
    # Patch the AsyncClient class
    monkeypatch.setattr("httpx.AsyncClient", lambda: mock_client)
    
    # Call the function with an invalid method and check that it raises the expected error
    with pytest.raises(ValueError, match="Unsupported HTTP method: INVALID"):
        await make_api_request("https://example.com/api", method="INVALID") 