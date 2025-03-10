"""
Tests for the retry utilities.

This module contains tests for the retry utilities, particularly the
RetryConfig class and retry functions.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch

from backend.ai.companion.utils.retry import (
    RetryConfig,
    retry_async,
    retry_sync,
    retry_async_decorator,
    retry_sync_decorator
)


class TestRetryConfig:
    """Tests for the RetryConfig class."""
    
    def test_initialization(self):
        """Test that RetryConfig can be initialized with default values."""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.backoff_factor == 2.0
        assert config.jitter is True
        assert config.jitter_factor == 0.25
        assert config.retry_exceptions == []
        assert config.retry_on is None
    
    def test_initialization_with_custom_values(self):
        """Test that RetryConfig can be initialized with custom values."""
        config = RetryConfig(
            max_retries=5,
            base_delay=0.5,
            max_delay=30.0,
            backoff_factor=3.0,
            jitter=False,
            jitter_factor=0.1,
            retry_exceptions=[ValueError, TypeError],
            retry_on=lambda e: isinstance(e, Exception)
        )
        
        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.backoff_factor == 3.0
        assert config.jitter is False
        assert config.jitter_factor == 0.1
        assert config.retry_exceptions == [ValueError, TypeError]
        assert callable(config.retry_on)
    
    def test_should_retry(self):
        """Test the should_retry method."""
        # Test with default config
        config = RetryConfig()
        
        # Should retry if attempt < max_retries
        assert config.should_retry(Exception(), 0) is True
        assert config.should_retry(Exception(), 1) is True
        assert config.should_retry(Exception(), 2) is True
        
        # Should not retry if attempt >= max_retries
        assert config.should_retry(Exception(), 3) is False
        
        # Test with retry_exceptions
        config = RetryConfig(retry_exceptions=[ValueError])
        
        # Should retry if exception is in retry_exceptions
        assert config.should_retry(ValueError(), 0) is True
        
        # Should not retry if exception is not in retry_exceptions
        assert config.should_retry(TypeError(), 0) is False
        
        # Test with retry_on
        config = RetryConfig(retry_on=lambda e: isinstance(e, ValueError))
        
        # Should retry if retry_on returns True
        assert config.should_retry(ValueError(), 0) is True
        
        # Should not retry if retry_on returns False
        assert config.should_retry(TypeError(), 0) is False
    
    def test_get_delay(self):
        """Test the get_delay method."""
        # Test with default config (no jitter for deterministic testing)
        config = RetryConfig(jitter=False)
        
        # First attempt: base_delay
        assert config.get_delay(0) == 1.0
        
        # Second attempt: base_delay * backoff_factor
        assert config.get_delay(1) == 2.0
        
        # Third attempt: base_delay * backoff_factor^2
        assert config.get_delay(2) == 4.0
        
        # Test with custom config
        config = RetryConfig(
            base_delay=0.5,
            backoff_factor=3.0,
            max_delay=5.0,
            jitter=False
        )
        
        # First attempt: base_delay
        assert config.get_delay(0) == 0.5
        
        # Second attempt: base_delay * backoff_factor
        assert config.get_delay(1) == 1.5
        
        # Third attempt: base_delay * backoff_factor^2
        assert config.get_delay(2) == 4.5
        
        # Fourth attempt: capped at max_delay
        assert config.get_delay(3) == 5.0
        
        # Test with jitter
        config = RetryConfig(
            base_delay=1.0,
            jitter=True,
            jitter_factor=0.5
        )
        
        # With jitter, the delay should be within the range [0.5, 1.5]
        delay = config.get_delay(0)
        assert 0.5 <= delay <= 1.5


class TestRetrySync:
    """Tests for the retry_sync function."""
    
    def test_successful_execution(self):
        """Test that retry_sync returns the result of the function."""
        def func():
            return "success"
        
        result = retry_sync(func)
        assert result == "success"
    
    def test_retry_on_exception(self):
        """Test that retry_sync retries on exception."""
        mock_func = MagicMock(side_effect=[ValueError(), "success"])
        
        result = retry_sync(mock_func, config=RetryConfig(base_delay=0.01))
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_max_retries_exceeded(self):
        """Test that retry_sync raises the last exception after max_retries."""
        mock_func = MagicMock(side_effect=[ValueError(), ValueError(), ValueError(), ValueError()])
        
        with pytest.raises(ValueError):
            retry_sync(mock_func, config=RetryConfig(max_retries=3, base_delay=0.01))
        
        assert mock_func.call_count == 4  # Initial call + 3 retries
    
    def test_retry_on_specific_exceptions(self):
        """Test that retry_sync only retries on specified exceptions."""
        mock_func = MagicMock(side_effect=[ValueError(), TypeError(), "success"])
        
        # Only retry on ValueError
        config = RetryConfig(retry_exceptions=[ValueError], base_delay=0.01)
        
        with pytest.raises(TypeError):
            retry_sync(mock_func, config=config)
        
        assert mock_func.call_count == 2  # Initial call + 1 retry (ValueError)


class TestRetryAsync:
    """Tests for the retry_async function."""
    
    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test that retry_async returns the result of the function."""
        async def func():
            return "success"
        
        result = await retry_async(func)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_on_exception(self):
        """Test that retry_async retries on exception."""
        mock_func = MagicMock(side_effect=[ValueError(), "success"])
        
        async def func():
            return mock_func()
        
        result = await retry_async(func, config=RetryConfig(base_delay=0.01))
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test that retry_async raises the last exception after max_retries."""
        mock_func = MagicMock(side_effect=[ValueError(), ValueError(), ValueError(), ValueError()])
        
        async def func():
            return mock_func()
        
        with pytest.raises(ValueError):
            await retry_async(func, config=RetryConfig(max_retries=3, base_delay=0.01))
        
        assert mock_func.call_count == 4  # Initial call + 3 retries
    
    @pytest.mark.asyncio
    async def test_retry_on_specific_exceptions(self):
        """Test that retry_async only retries on specified exceptions."""
        mock_func = MagicMock(side_effect=[ValueError(), TypeError(), "success"])
        
        async def func():
            return mock_func()
        
        # Only retry on ValueError
        config = RetryConfig(retry_exceptions=[ValueError], base_delay=0.01)
        
        with pytest.raises(TypeError):
            await retry_async(func, config=config)
        
        assert mock_func.call_count == 2  # Initial call + 1 retry (ValueError)


class TestRetryDecorators:
    """Tests for the retry decorators."""
    
    def test_retry_sync_decorator(self):
        """Test the retry_sync_decorator."""
        # Create a function that fails twice then succeeds
        mock_func = MagicMock(side_effect=[ValueError(), ValueError(), "success"])
        
        @retry_sync_decorator(config=RetryConfig(base_delay=0.01))
        def decorated_func():
            return mock_func()
        
        result = decorated_func()
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_async_decorator(self):
        """Test the retry_async_decorator."""
        # Create a function that fails twice then succeeds
        mock_func = MagicMock(side_effect=[ValueError(), ValueError(), "success"])
        
        @retry_async_decorator(config=RetryConfig(base_delay=0.01))
        async def decorated_func():
            return mock_func()
        
        result = await decorated_func()
        
        assert result == "success"
        assert mock_func.call_count == 3 