"""
Tests for the usage tracker module.

This module contains tests for the usage tracker, which is used
to track API usage and enforce quotas for Amazon Bedrock.
"""

import pytest
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from backend.ai.companion.tier3.usage_tracker import (
    UsageQuota,
    UsageRecord,
    UsageTracker,
    track_request,
    check_quota,
    get_usage_summary
)


@pytest.fixture
def sample_record():
    """Create a sample usage record for testing."""
    return UsageRecord(
        timestamp=datetime.now(),
        request_id="test-123",
        model_id="amazon.nova-micro-v1:0",
        input_tokens=100,
        output_tokens=50,
        duration_ms=500,
        success=True,
        error_type=None
    )


@pytest.fixture
def sample_failed_record():
    """Create a sample failed usage record for testing."""
    return UsageRecord(
        timestamp=datetime.now(),
        request_id="test-456",
        model_id="amazon.nova-micro-v1:0",
        input_tokens=100,
        output_tokens=0,
        duration_ms=200,
        success=False,
        error_type="connection_error"
    )


@pytest.fixture
def temp_storage_path():
    """Create a temporary file for storage."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
        yield temp_file.name
    
    # Clean up after the test
    Path(temp_file.name).unlink(missing_ok=True)


class TestUsageQuota:
    """Tests for the UsageQuota class."""
    
    def test_initialization(self):
        """Test initialization of the UsageQuota."""
        quota = UsageQuota()
        
        # Check default values
        assert quota.daily_token_limit == 100000
        assert quota.hourly_request_limit == 100
        assert quota.monthly_cost_limit == 50.0
        
        # Check that pricing dictionaries are initialized
        assert "amazon.nova-micro-v1:0" in quota.cost_per_1k_input_tokens
        assert "amazon.nova-micro-v1:0" in quota.cost_per_1k_output_tokens
        
        # Test with custom values
        custom_quota = UsageQuota(
            daily_token_limit=200000,
            hourly_request_limit=200,
            monthly_cost_limit=100.0
        )
        
        assert custom_quota.daily_token_limit == 200000
        assert custom_quota.hourly_request_limit == 200
        assert custom_quota.monthly_cost_limit == 100.0


class TestUsageRecord:
    """Tests for the UsageRecord class."""
    
    def test_initialization(self, sample_record):
        """Test initialization of the UsageRecord."""
        # Check that all attributes are set correctly
        assert isinstance(sample_record.timestamp, datetime)
        assert sample_record.request_id == "test-123"
        assert sample_record.model_id == "amazon.nova-micro-v1:0"
        assert sample_record.input_tokens == 100
        assert sample_record.output_tokens == 50
        assert sample_record.duration_ms == 500
        assert sample_record.success is True
        assert sample_record.error_type is None
    
    def test_to_dict(self, sample_record):
        """Test converting a record to a dictionary."""
        record_dict = sample_record.to_dict()
        
        # Check that all attributes are in the dictionary
        assert "timestamp" in record_dict
        assert "request_id" in record_dict
        assert "model_id" in record_dict
        assert "input_tokens" in record_dict
        assert "output_tokens" in record_dict
        assert "duration_ms" in record_dict
        assert "success" in record_dict
        assert "error_type" in record_dict
        
        # Check that values are correct
        assert record_dict["request_id"] == "test-123"
        assert record_dict["model_id"] == "amazon.nova-micro-v1:0"
        assert record_dict["input_tokens"] == 100
        assert record_dict["output_tokens"] == 50
        assert record_dict["duration_ms"] == 500
        assert record_dict["success"] is True
        assert record_dict["error_type"] is None
    
    def test_from_dict(self):
        """Test creating a record from a dictionary."""
        record_dict = {
            "timestamp": datetime.now().isoformat(),
            "request_id": "test-789",
            "model_id": "amazon.titan-text-express-v1",
            "input_tokens": 200,
            "output_tokens": 100,
            "duration_ms": 800,
            "success": False,
            "error_type": "timeout_error"
        }
        
        record = UsageRecord.from_dict(record_dict)
        
        # Check that all attributes are set correctly
        assert isinstance(record.timestamp, datetime)
        assert record.request_id == "test-789"
        assert record.model_id == "amazon.titan-text-express-v1"
        assert record.input_tokens == 200
        assert record.output_tokens == 100
        assert record.duration_ms == 800
        assert record.success is False
        assert record.error_type == "timeout_error"


class TestUsageTracker:
    """Tests for the UsageTracker class."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, temp_storage_path):
        """Test initialization of the UsageTracker."""
        # Test with default values
        tracker = UsageTracker()
        
        assert isinstance(tracker.quota, UsageQuota)
        assert tracker.storage_path is None
        assert tracker.auto_save is True
        assert tracker.records == []
        
        # Test with custom values
        custom_quota = UsageQuota(daily_token_limit=200000)
        tracker = UsageTracker(
            quota=custom_quota,
            storage_path=temp_storage_path,
            auto_save=False
        )
        
        assert tracker.quota is custom_quota
        assert tracker.storage_path == temp_storage_path
        assert tracker.auto_save is False
    
    @pytest.mark.asyncio
    async def test_track_usage(self):
        """Test tracking API usage."""
        tracker = UsageTracker(auto_save=False)
        
        # Track a successful request
        record = await tracker.track_usage(
            request_id="test-123",
            model_id="amazon.nova-micro-v1:0",
            input_tokens=100,
            output_tokens=50,
            duration_ms=500,
            success=True
        )
        
        # Check that the record was created correctly
        assert record.request_id == "test-123"
        assert record.model_id == "amazon.nova-micro-v1:0"
        assert record.input_tokens == 100
        assert record.output_tokens == 50
        assert record.duration_ms == 500
        assert record.success is True
        
        # Check that the record was added to the tracker
        assert len(tracker.records) == 1
        assert tracker.records[0] is record
        
        # Track a failed request
        record = await tracker.track_usage(
            request_id="test-456",
            model_id="amazon.nova-micro-v1:0",
            input_tokens=100,
            output_tokens=0,
            duration_ms=200,
            success=False,
            error_type="connection_error"
        )
        
        # Check that the record was created correctly
        assert record.request_id == "test-456"
        assert record.success is False
        assert record.error_type == "connection_error"
        
        # Check that the record was added to the tracker
        assert len(tracker.records) == 2
    
    @pytest.mark.asyncio
    async def test_check_quota(self):
        """Test checking if a request would exceed the quota."""
        tracker = UsageTracker(
            quota=UsageQuota(
                daily_token_limit=1000,
                hourly_request_limit=10,
                monthly_cost_limit=1.0
            ),
            auto_save=False
        )
        
        # Add some usage records
        for i in range(5):
            await tracker.track_usage(
                request_id=f"test-{i}",
                model_id="amazon.nova-micro-v1:0",
                input_tokens=100,
                output_tokens=50,
                duration_ms=500,
                success=True
            )
        
        # Check that a small request is allowed
        allowed, reason = await tracker.check_quota("amazon.nova-micro-v1:0", 100)
        assert allowed is True
        assert reason == "Quota check passed"
        
        # Check that a request that would exceed the daily token limit is not allowed
        allowed, reason = await tracker.check_quota("amazon.nova-micro-v1:0", 1000)
        assert allowed is False
        assert "Daily token limit exceeded" in reason
        
        # Add more records to exceed the hourly request limit
        for i in range(5):
            await tracker.track_usage(
                request_id=f"test-{i+5}",
                model_id="amazon.nova-micro-v1:0",
                input_tokens=10,
                output_tokens=5,
                duration_ms=500,
                success=True
            )
        
        # Check that a request that would exceed the hourly request limit is not allowed
        allowed, reason = await tracker.check_quota("amazon.nova-micro-v1:0", 10)
        assert allowed is False
        assert "Hourly request limit exceeded" in reason
    
    def test_get_token_usage_for_period(self, sample_record, sample_failed_record):
        """Test getting the total token usage for a period."""
        tracker = UsageTracker(auto_save=False)
        
        # Add some records
        tracker.records = [sample_record, sample_failed_record]
        
        # Check token usage for a period that includes all records
        usage = tracker.get_token_usage_for_period(timedelta(days=1))
        
        # Only successful records should be counted
        assert usage == sample_record.input_tokens + sample_record.output_tokens
    
    def test_get_request_count_for_period(self, sample_record, sample_failed_record):
        """Test getting the number of requests for a period."""
        tracker = UsageTracker(auto_save=False)
        
        # Add some records
        tracker.records = [sample_record, sample_failed_record]
        
        # Check request count for a period that includes all records
        count = tracker.get_request_count_for_period(timedelta(days=1))
        
        # All records should be counted, regardless of success
        assert count == 2
    
    def test_get_cost_for_period(self, sample_record, sample_failed_record):
        """Test getting the total cost for a period."""
        tracker = UsageTracker(auto_save=False)
        
        # Add some records
        tracker.records = [sample_record, sample_failed_record]
        
        # Check cost for a period that includes all records
        cost = tracker.get_cost_for_period(timedelta(days=1))
        
        # Only successful records should be counted
        expected_cost = tracker._calculate_cost(
            sample_record.model_id,
            sample_record.input_tokens,
            sample_record.output_tokens
        )
        
        assert cost == expected_cost
    
    def test_get_usage_summary(self, sample_record, sample_failed_record):
        """Test getting a summary of usage statistics."""
        tracker = UsageTracker(auto_save=False)
        
        # Add some records
        tracker.records = [sample_record, sample_failed_record]
        
        # Get the summary
        summary = tracker.get_usage_summary()
        
        # Check that the summary contains the expected sections
        assert "total_requests" in summary
        assert "daily" in summary
        assert "weekly" in summary
        assert "monthly" in summary
        assert "by_model" in summary
        assert "quota_status" in summary
        
        # Check that the total requests count is correct
        assert summary["total_requests"] == 2
        
        # Check that the model usage is tracked
        assert sample_record.model_id in summary["by_model"]
        
        # Check that the quota status is included
        assert "daily_tokens" in summary["quota_status"]
        assert "hourly_requests" in summary["quota_status"]
        assert "monthly_cost" in summary["quota_status"]
    
    def test_calculate_cost(self):
        """Test calculating the cost for a request."""
        tracker = UsageTracker(auto_save=False)
        
        # Calculate cost for a known model
        cost = tracker._calculate_cost(
            "amazon.nova-micro-v1:0",
            1000,  # 1000 input tokens
            500    # 500 output tokens
        )
        
        # Expected cost: (1000/1000 * 0.0003) + (500/1000 * 0.0006) = 0.0003 + 0.0003 = 0.0006
        expected_cost = 0.0006
        
        assert cost == expected_cost
        
        # Calculate cost for an unknown model (should use default pricing)
        cost = tracker._calculate_cost(
            "unknown-model",
            1000,  # 1000 input tokens
            500    # 500 output tokens
        )
        
        # Expected cost: (1000/1000 * 0.001) + (500/1000 * 0.002) = 0.001 + 0.001 = 0.002
        expected_cost = 0.002
        
        assert cost == expected_cost
    
    @pytest.mark.asyncio
    async def test_save_and_load_records(self, temp_storage_path, sample_record):
        """Test saving and loading usage records."""
        # Create a tracker with a storage path
        tracker = UsageTracker(
            storage_path=temp_storage_path,
            auto_save=False
        )
        
        # Add a record
        tracker.records = [sample_record]
        
        # Save the records
        await tracker._save_records()
        
        # Create a new tracker that will load the records
        new_tracker = UsageTracker(
            storage_path=temp_storage_path,
            auto_save=False
        )
        
        # Check that the records were loaded
        assert len(new_tracker.records) == 1
        assert new_tracker.records[0].request_id == sample_record.request_id
        assert new_tracker.records[0].model_id == sample_record.model_id
        assert new_tracker.records[0].input_tokens == sample_record.input_tokens
        assert new_tracker.records[0].output_tokens == sample_record.output_tokens


@pytest.mark.asyncio
async def test_track_request():
    """Test the track_request helper function."""
    # Create a mock tracker
    mock_tracker = MagicMock()
    mock_tracker.track_usage = AsyncMock(return_value=MagicMock())
    
    # Call the helper function
    await track_request(
        request_id="test-123",
        model_id="amazon.nova-micro-v1:0",
        input_tokens=100,
        output_tokens=50,
        duration_ms=500,
        success=True,
        tracker=mock_tracker
    )
    
    # Check that the tracker's track_usage method was called with the correct arguments
    mock_tracker.track_usage.assert_called_once_with(
        request_id="test-123",
        model_id="amazon.nova-micro-v1:0",
        input_tokens=100,
        output_tokens=50,
        duration_ms=500,
        success=True,
        error_type=None
    )


@pytest.mark.asyncio
async def test_check_quota():
    """Test the check_quota helper function."""
    # Create a mock tracker
    mock_tracker = MagicMock()
    mock_tracker.check_quota = AsyncMock(return_value=(True, "Quota check passed"))
    
    # Call the helper function
    allowed, reason = await check_quota(
        model_id="amazon.nova-micro-v1:0",
        estimated_tokens=100,
        tracker=mock_tracker
    )
    
    # Check that the tracker's check_quota method was called with the correct arguments
    mock_tracker.check_quota.assert_called_once_with(
        "amazon.nova-micro-v1:0",
        100
    )
    
    # Check that the result is correct
    assert allowed is True
    assert reason == "Quota check passed"


def test_get_usage_summary():
    """Test the get_usage_summary helper function."""
    # Create a mock tracker
    mock_tracker = MagicMock()
    mock_tracker.get_usage_summary = MagicMock(return_value={"total_requests": 10})
    
    # Call the helper function
    summary = get_usage_summary(tracker=mock_tracker)
    
    # Check that the tracker's get_usage_summary method was called
    mock_tracker.get_usage_summary.assert_called_once()
    
    # Check that the result is correct
    assert summary == {"total_requests": 10} 