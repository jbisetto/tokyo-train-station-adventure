"""
Tests for the FastAPI application structure.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add the project root to the path so we can import the backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from src.main import app


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.
    """
    return TestClient(app)


def test_app_exists():
    """
    Test that the FastAPI application exists.
    """
    assert app is not None


def test_health_endpoint(client):
    """
    Test that the health endpoint returns a 200 status code.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_root_endpoint(client):
    """
    Test that the API root endpoint returns a 200 status code.
    """
    response = client.get("/api")
    assert response.status_code == 200
    assert "version" in response.json() 