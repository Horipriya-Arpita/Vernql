"""
Tests for authentication and API key management
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.security import generate_api_key, hash_api_key, create_api_key
from app.models import Company, APIKey

client = TestClient(app)


def test_generate_api_key():
    """Test API key generation"""
    key = generate_api_key()

    # Should start with prefix
    assert key.startswith("textsql_")

    # Should be long enough
    assert len(key) > 40


def test_hash_api_key():
    """Test API key hashing"""
    key = "textsql_test123"
    hash1 = hash_api_key(key)
    hash2 = hash_api_key(key)

    # Same key should produce same hash
    assert hash1 == hash2

    # Hash should be hex string
    assert len(hash1) == 64  # SHA-256 hex is 64 characters


def test_get_current_auth_info_without_key():
    """Test /auth/me endpoint without API key"""
    response = client.get("/v1/auth/me")

    assert response.status_code == 401
    assert "Missing API key" in response.json()["detail"]


def test_get_current_auth_info_with_invalid_key():
    """Test /auth/me endpoint with invalid API key"""
    response = client.get(
        "/v1/auth/me",
        headers={"X-API-Key": "textsql_invalid_key_123"}
    )

    assert response.status_code == 401
    assert "Invalid or expired API key" in response.json()["detail"]


def test_create_and_use_api_key(db: Session):
    """Test creating and using an API key"""
    # Create a test company
    company = Company(name="Test Company", is_active=True)
    db.add(company)
    db.commit()
    db.refresh(company)

    # Create an API key
    raw_key, api_key_obj = create_api_key(
        db=db,
        company_id=str(company.id),
        name="Test Key"
    )

    # Verify key format
    assert raw_key.startswith("textsql_")
    assert api_key_obj.name == "Test Key"
    assert api_key_obj.is_active is True

    # Use the key to authenticate
    response = client.get(
        "/v1/auth/me",
        headers={"X-API-Key": raw_key}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Test Company"
    assert data["authenticated"] is True


def test_list_api_keys(db: Session):
    """Test listing API keys"""
    # Create a test company
    company = Company(name="Test Company 2", is_active=True)
    db.add(company)
    db.commit()
    db.refresh(company)

    # Create multiple API keys
    raw_key1, _ = create_api_key(db=db, company_id=str(company.id), name="Key 1")
    raw_key2, _ = create_api_key(db=db, company_id=str(company.id), name="Key 2")

    # List keys using authentication
    response = client.get(
        "/v1/auth/keys",
        headers={"X-API-Key": raw_key1}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["keys"]) == 2


def test_revoke_api_key(db: Session):
    """Test revoking an API key"""
    # Create a test company
    company = Company(name="Test Company 3", is_active=True)
    db.add(company)
    db.commit()
    db.refresh(company)

    # Create an API key
    raw_key, api_key_obj = create_api_key(
        db=db,
        company_id=str(company.id),
        name="Key to Revoke"
    )

    # Verify it works
    response = client.get(
        "/v1/auth/me",
        headers={"X-API-Key": raw_key}
    )
    assert response.status_code == 200

    # Revoke the key
    response = client.delete(
        f"/v1/auth/keys/{api_key_obj.id}",
        headers={"X-API-Key": raw_key}
    )
    assert response.status_code == 204

    # Verify it no longer works
    response = client.get(
        "/v1/auth/me",
        headers={"X-API-Key": raw_key}
    )
    assert response.status_code == 401


def test_ping_endpoint():
    """Test ping endpoint (no auth required)"""
    response = client.get("/v1/ping")

    assert response.status_code == 200
    assert response.json()["message"] == "pong"


def test_health_endpoint():
    """Test health endpoint (no auth required)"""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
