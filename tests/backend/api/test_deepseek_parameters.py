"""
Tests for the DeepSeek engine parameters API.
"""

import pytest
from fastapi.testclient import TestClient

from backend.api import create_app
from backend.data.deepseek_parameters import _deepseek_parameters


@pytest.fixture
def client():
    """Create a test client for the API."""
    app = create_app()
    return TestClient(app)


def test_update_deepseek_parameters(client):
    """Test updating DeepSeek engine parameters."""
    # Save the original parameters
    original_parameters = _deepseek_parameters.copy()
    
    # Create a parameters update
    parameters_update = {
        "temperature": 0.8,
        "top_p": 0.9,
        "max_tokens": 2048,
        "jlpt_level_cap": "N3"
    }
    
    # Send a POST request to update the parameters
    response = client.post("/api/npc/engine/parameters", json=parameters_update)
    
    # Check that the response is successful
    assert response.status_code == 200
    
    # Check that the response contains the updated parameters
    data = response.json()
    assert data["success"] is True
    assert data["parameters"]["temperature"] == 0.8
    assert data["parameters"]["top_p"] == 0.9
    assert data["parameters"]["max_tokens"] == 2048
    assert data["parameters"]["jlpt_level_cap"] == "N3"
    
    # Verify that the parameters were actually updated in the data store
    assert _deepseek_parameters["temperature"] == 0.8
    assert _deepseek_parameters["top_p"] == 0.9
    assert _deepseek_parameters["max_tokens"] == 2048
    assert _deepseek_parameters["jlpt_level_cap"] == "N3"
    
    # Restore the original parameters for other tests
    for key, value in original_parameters.items():
        _deepseek_parameters[key] = value


def test_update_deepseek_parameters_invalid_data(client):
    """Test updating DeepSeek engine parameters with invalid data."""
    # Create an invalid parameters update (temperature out of range)
    invalid_parameters = {
        "temperature": 1.5,  # Should be between 0.0 and 1.0
        "top_p": 0.9
    }
    
    # Send a POST request with invalid data
    response = client.post("/api/npc/engine/parameters", json=invalid_parameters)
    
    # Check that the response is a validation error
    assert response.status_code == 422
    
    # Check that the response contains validation error details
    data = response.json()
    assert "error" in data
    assert "message" in data
    assert "details" in data
    assert "fieldErrors" in data["details"]


def test_update_deepseek_parameters_empty_request(client):
    """Test updating DeepSeek engine parameters with an empty request."""
    # Create an empty parameters update
    empty_parameters = {}
    
    # Send a POST request with empty data
    response = client.post("/api/npc/engine/parameters", json=empty_parameters)
    
    # Check that the response is a validation error
    assert response.status_code == 422
    
    # Check that the response contains validation error details
    data = response.json()
    assert "error" in data
    assert "message" in data
    assert "details" in data
    assert "fieldErrors" in data["details"]


def test_update_deepseek_parameters_invalid_model(client):
    """Test updating DeepSeek engine parameters with an invalid model."""
    # Create a parameters update with an invalid model
    invalid_model_parameters = {
        "temperature": 0.8,
        "model_version": "invalid-model"
    }
    
    # Send a POST request with invalid model
    response = client.post("/api/npc/engine/parameters", json=invalid_model_parameters)
    
    # Check that the response is a validation error or bad request
    assert response.status_code in [400, 422]
    
    # Check that the response contains error details
    data = response.json()
    if response.status_code == 422:
        assert "error" in data
        assert "message" in data
        assert "details" in data
        assert "fieldErrors" in data["details"]
    else:
        assert "error" in data
        assert "message" in data 