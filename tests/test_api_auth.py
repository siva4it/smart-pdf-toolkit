"""
Tests for API authentication and security.
"""

import pytest
from fastapi.testclient import TestClient
import tempfile
import os
from jose import jwt
from datetime import datetime, timedelta

from smart_pdf_toolkit.api.main import create_app
from smart_pdf_toolkit.api.config import APIConfig
from smart_pdf_toolkit.api.auth import fake_users_db


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    temp_dir = tempfile.mkdtemp()
    upload_dir = os.path.join(temp_dir, "uploads")
    output_dir = os.path.join(temp_dir, "output")
    
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    return {
        "temp_dir": temp_dir,
        "upload_dir": upload_dir,
        "output_dir": output_dir
    }


@pytest.fixture
def test_config(temp_dirs):
    """Create test configuration."""
    return APIConfig(
        host="127.0.0.1",
        port=8001,
        debug=True,
        upload_dir=temp_dirs["upload_dir"],
        temp_dir=temp_dirs["temp_dir"],
        output_dir=temp_dirs["output_dir"],
        max_file_size=10 * 1024 * 1024,  # 10MB for testing
        cors_origins=["*"],
        secret_key="test_secret_key_for_testing_only"
    )


@pytest.fixture
def client(test_config, monkeypatch):
    """Create test client."""
    # Mock the get_api_config function to return our test config
    def mock_get_api_config():
        return test_config
    
    monkeypatch.setattr("smart_pdf_toolkit.api.config.get_api_config", mock_get_api_config)
    monkeypatch.setattr("smart_pdf_toolkit.api.auth.get_api_config", mock_get_api_config)
    
    app = create_app(test_config)
    return TestClient(app)


def test_login_success(client):
    """Test successful login."""
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "user", "password": "userpassword", "scope": "read"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Verify token
    token = data["access_token"]
    payload = jwt.decode(token, "test_secret_key_for_testing_only", algorithms=["HS256"])
    assert payload["sub"] == "user"
    assert "read" in payload["scopes"]


def test_login_failure(client):
    """Test failed login."""
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "user", "password": "wrongpassword", "scope": "read"}
    )
    assert response.status_code == 401


def test_get_current_user(client):
    """Test getting current user information."""
    # First login to get token
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "user", "password": "userpassword", "scope": "read"}
    )
    token = login_response.json()["access_token"]
    
    # Use token to get user info
    response = client.get(
        "/api/v1/auth/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["username"] == "user"
    assert not data["disabled"]
    assert "read" in data["scopes"]


def test_get_user_scopes(client):
    """Test getting user scopes."""
    # First login to get token
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "user", "password": "userpassword", "scope": "read"}
    )
    token = login_response.json()["access_token"]
    
    # Use token to get user scopes
    response = client.get(
        "/api/v1/auth/users/me/scopes",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["username"] == "user"
    assert "read" in data["scopes"]


def test_admin_access(client):
    """Test admin access to user list."""
    # First login as admin to get token
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "adminpassword", "scope": "admin"}
    )
    token = login_response.json()["access_token"]
    
    # Use admin token to get all users
    response = client.get(
        "/api/v1/auth/admin/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 3  # admin, user, editor
    usernames = [user["username"] for user in data]
    assert "admin" in usernames
    assert "user" in usernames
    assert "editor" in usernames


def test_insufficient_permissions(client):
    """Test access denied for insufficient permissions."""
    # Login as regular user
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "user", "password": "userpassword", "scope": "read"}
    )
    token = login_response.json()["access_token"]
    
    # Try to access admin endpoint
    response = client.get(
        "/api/v1/auth/admin/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_invalid_token(client):
    """Test invalid token handling."""
    response = client.get(
        "/api/v1/auth/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


def test_missing_token(client):
    """Test missing token handling."""
    response = client.get("/api/v1/auth/users/me")
    assert response.status_code == 401


def test_expired_token(client, test_config):
    """Test expired token handling."""
    from smart_pdf_toolkit.api.auth import create_access_token
    from datetime import timedelta
    
    # Create an expired token
    expired_token = create_access_token(
        data={"sub": "user", "scopes": ["read"]},
        expires_delta=timedelta(seconds=-1)  # Already expired
    )
    
    response = client.get(
        "/api/v1/auth/users/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401


def test_scope_validation(client):
    """Test scope validation for different user types."""
    # Test editor with read and write scope
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "editor", "password": "editorpassword", "scope": "read write"}
    )
    assert login_response.status_code == 200
    
    token = login_response.json()["access_token"]
    
    # Editor should be able to access their info
    response = client.get(
        "/api/v1/auth/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["username"] == "editor"
    assert "write" in data["scopes"]
    assert "read" in data["scopes"]


def test_security_headers(client):
    """Test security headers are present."""
    response = client.get("/health")
    
    # Check for security headers
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "X-XSS-Protection" in response.headers
    assert "Referrer-Policy" in response.headers
    assert "Content-Security-Policy" in response.headers
    assert "Strict-Transport-Security" in response.headers


def test_sql_injection_protection(client):
    """Test SQL injection protection middleware."""
    # Test with potential SQL injection in query parameter
    response = client.get("/health?test='; DROP TABLE users; --")
    assert response.status_code == 400
    assert response.text == "Invalid request"


def test_multiple_scopes(client):
    """Test user with multiple scopes."""
    # Login as admin with multiple scopes
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "adminpassword", "scope": "read write admin"}
    )
    assert login_response.status_code == 200
    
    token_data = login_response.json()
    token = token_data["access_token"]
    
    # Verify token contains all requested scopes
    from jose import jwt
    payload = jwt.decode(token, "test_secret_key_for_testing_only", algorithms=["HS256"])
    assert "read" in payload["scopes"]
    assert "write" in payload["scopes"]
    assert "admin" in payload["scopes"]


def test_password_hashing():
    """Test password hashing functionality."""
    from smart_pdf_toolkit.api.auth import get_password_hash, verify_password
    
    password = "test_password"
    hashed = get_password_hash(password)
    
    # Hash should be different from original password
    assert hashed != password
    
    # Should verify correctly
    assert verify_password(password, hashed)
    
    # Should not verify with wrong password
    assert not verify_password("wrong_password", hashed)