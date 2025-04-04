"""
Tests for the monitoring utilities.

This module contains tests for the monitoring utilities, particularly the
ProcessorMonitor class.
"""

import pytest
import os
import json
import time
from unittest.mock import patch, MagicMock
import signal

from src.ai.companion.utils.monitoring import ProcessorMonitor


class TestProcessorMonitor:
    """Tests for the ProcessorMonitor class."""
    
    def test_singleton_pattern(self):
        """Test that ProcessorMonitor follows the singleton pattern."""
        monitor1 = ProcessorMonitor()
        monitor2 = ProcessorMonitor()
        
        assert monitor1 is monitor2
    
    def test_reset(self):
        """Test resetting the monitor."""
        monitor = ProcessorMonitor()
        
        # Add some metrics
        monitor.track_request("tier2", "test-123")
        monitor.track_error("tier2", "connection_error", "Failed to connect")
        
        # Reset the monitor
        monitor.reset()
        
        # Check that metrics were reset
        metrics = monitor.get_metrics()
        assert metrics['requests'] == {}
        assert metrics['errors'] == {}
    
    def test_track_request(self):
        """Test tracking requests."""
        monitor = ProcessorMonitor()
        monitor.reset()
        
        # Track some requests
        monitor.track_request("tier2", "test-123")
        monitor.track_request("tier2", "test-456")
        monitor.track_request("tier1", "test-789")
        
        # Check the metrics
        metrics = monitor.get_metrics()
        assert metrics['requests']['tier2'] == 2
        assert metrics['requests']['tier1'] == 1
    
    def test_track_error(self):
        """Test tracking errors."""
        monitor = ProcessorMonitor()
        monitor.reset()
        
        # Track some errors
        monitor.track_error("tier2", "connection_error", "Failed to connect")
        monitor.track_error("tier2", "connection_error", "Failed to connect again")
        monitor.track_error("tier2", "model_error", "Model not found")
        
        # Check the metrics
        metrics = monitor.get_metrics()
        assert metrics['errors']['tier2:connection_error'] == 2
        assert metrics['errors']['tier2:model_error'] == 1
        
        # Check that last errors were tracked
        assert len(metrics['last_errors']['tier2:connection_error']) == 2
        assert metrics['last_errors']['tier2:connection_error'][0]['message'] == "Failed to connect"
        assert metrics['last_errors']['tier2:connection_error'][1]['message'] == "Failed to connect again"
    
    def test_track_retry(self):
        """Test tracking retries."""
        monitor = ProcessorMonitor()
        monitor.reset()
        
        # Track some retries
        monitor.track_retry("tier2", 1)
        monitor.track_retry("tier2", 2)
        monitor.track_retry("tier2", 1)
        
        # Check the metrics
        metrics = monitor.get_metrics()
        assert metrics['retries']['tier2:retry_1'] == 2
        assert metrics['retries']['tier2:retry_2'] == 1
    
    def test_track_fallback(self):
        """Test tracking fallbacks."""
        monitor = ProcessorMonitor()
        monitor.reset()
        
        # Track some fallbacks
        monitor.track_fallback("tier2", "simpler_model")
        monitor.track_fallback("tier2", "tier1")
        monitor.track_fallback("tier2", "tier1")
        
        # Check the metrics
        metrics = monitor.get_metrics()
        assert metrics['fallbacks']['tier2:simpler_model'] == 1
        assert metrics['fallbacks']['tier2:tier1'] == 2
    
    def test_track_response_time(self):
        """Test tracking response times."""
        monitor = ProcessorMonitor()
        monitor.reset()
        
        # Track some response times
        monitor.track_response_time("tier2", 100)
        monitor.track_response_time("tier2", 200)
        monitor.track_response_time("tier1", 50)
        
        # Check the metrics
        metrics = monitor.get_metrics()
        assert metrics['avg_response_time_ms']['tier2'] == 150  # (100 + 200) / 2
        assert metrics['avg_response_time_ms']['tier1'] == 50
    
    def test_track_success(self):
        """Test tracking success rates."""
        monitor = ProcessorMonitor()
        monitor.reset()
        
        # Track requests first
        monitor.track_request("tier2", "test-123")
        monitor.track_request("tier2", "test-456")
        monitor.track_request("tier2", "test-789")
        monitor.track_request("tier1", "test-abc")
        
        # Track some successes and failures
        monitor.track_success("tier2", True)
        monitor.track_success("tier2", True)
        monitor.track_success("tier2", False)
        monitor.track_success("tier1", True)
        
        # Check the metrics
        metrics = monitor.get_metrics()
        
        # Check success counts
        assert metrics['success_counts']['tier2'] == 2
        assert metrics['success_counts']['tier1'] == 1
        
        # Check success rates
        assert metrics['success_rate']['tier2'] == 2/3
        assert metrics['success_rate']['tier1'] == 1.0
    
    @patch('json.dump')
    @patch('builtins.open')
    @patch('os.makedirs')
    def test_save_metrics(self, mock_makedirs, mock_open, mock_json_dump):
        """Test saving metrics to disk."""
        # Define a timeout handler
        def timeout_handler(signum, frame):
            raise TimeoutError("Test timed out after 5 seconds")
        
        # Set a timeout of 5 seconds
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)
        
        try:
            # Create a new instance with a mocked _initialize method
            with patch.object(ProcessorMonitor, '_initialize') as mock_initialize:
                monitor = ProcessorMonitor()
                # Reset the monitor to ensure clean state
                monitor.reset()
                
                # Add some metrics
                monitor.track_request("tier2", "test-123")
                
                # Save the metrics
                monitor.save_metrics()
                
                # Check that the metrics were saved
                # Note: We don't check makedirs since it's called in _initialize
                mock_open.assert_called_once()
                mock_json_dump.assert_called_once()
        finally:
            # Cancel the alarm
            signal.alarm(0)
    
    @patch('logging.Logger.info')
    def test_log_metrics_summary(self, mock_log_info):
        """Test logging a metrics summary."""
        # Define a timeout handler
        def timeout_handler(signum, frame):
            raise TimeoutError("Test timed out after 5 seconds")
        
        # Set a timeout of 5 seconds
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)
        
        try:
            monitor = ProcessorMonitor()
            monitor.reset()
            
            # Add some metrics
            monitor.track_request("tier2", "test-123")
            monitor.track_error("tier2", "connection_error", "Failed to connect")
            monitor.track_fallback("tier2", "tier1")
            monitor.track_response_time("tier2", 100)
            monitor.track_success("tier2", True)
            
            # Log the metrics summary
            monitor.log_metrics_summary()
            
            # Check that the summary was logged
            assert mock_log_info.call_count >= 5  # At least 5 log entries 
        finally:
            # Cancel the alarm
            signal.alarm(0) 