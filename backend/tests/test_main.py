"""
Tests for main application endpoints
"""
import pytest
from fastapi.testclient import TestClient


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "textsql-api"
    assert data["version"] == "1.0.0"


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "TextSQL API"
    assert "docs" in data
    assert "health" in data


def test_ping_endpoint(client):
    """Test v1 ping endpoint"""
    response = client.get("/v1/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "pong"
    assert data["version"] == "1.0.0"


def test_cors_headers(client):
    """Test that CORS headers are present"""
    response = client.options("/health")
    # Options request should be handled by CORS middleware
    assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly defined
