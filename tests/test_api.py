"""
Tests for the FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient
import tempfile
import os

from smart_pdf_toolkit.api.main import create_app
from smart_pdf_toolkit.api.config import APIConfig


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
        cors_origins=["*"]
    )


@pytest.fixture
def client(test_config):
    """Create test client."""
    app = create_app(test_config)
    return TestClient(app)


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Smart PDF Toolkit API"
    assert data["version"] == "1.0.0"
    assert "docs" in data
    assert "health" in data


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "services" in data


def test_detailed_health_check(client):
    """Test the detailed health check endpoint."""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "system" in data
    assert "services" in data
    assert "configuration" in data


def test_readiness_check(client):
    """Test the readiness check endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ready"
    assert "timestamp" in data


def test_openapi_docs(client):
    """Test that OpenAPI documentation is available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert data["info"]["title"] == "Smart PDF Toolkit API"


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.options("/")
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers


def test_security_headers(client):
    """Test security headers are present."""
    response = client.get("/")
    
    # Check for security headers
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-xss-protection") == "1; mode=block"


def test_gzip_compression(client):
    """Test that gzip compression is enabled."""
    response = client.get("/", headers={"accept-encoding": "gzip"})
    # For small responses, gzip might not be applied
    # This test mainly ensures the middleware is loaded without errors
    assert response.status_code == 200


def test_invalid_endpoint(client):
    """Test handling of invalid endpoints."""
    response = client.get("/invalid-endpoint")
    assert response.status_code == 404


def test_pdf_upload_endpoint_structure(client):
    """Test that PDF upload endpoint exists (structure test)."""
    # Test with no file (should fail but endpoint should exist)
    response = client.post("/api/v1/pdf/upload")
    # Should return 422 (validation error) not 404 (not found)
    assert response.status_code == 422


def test_ai_services_endpoints_structure(client):
    """Test that AI services endpoints exist (structure test)."""
    # Test summarize endpoint structure
    response = client.post("/api/v1/ai/summarize", json={})
    # Should return 422 (validation error) not 404 (not found)
    assert response.status_code == 422
    
    # Test analyze endpoint structure
    response = client.post("/api/v1/ai/analyze", json={})
    assert response.status_code == 422


def test_batch_processing_endpoints_structure(client):
    """Test that batch processing endpoints exist (structure test)."""
    # Test create batch job endpoint structure
    response = client.post("/api/v1/batch/jobs", json={})
    # Should return 422 (validation error) not 404 (not found)
    assert response.status_code == 422


def test_content_extraction_endpoints_structure(client):
    """Test that content extraction endpoints exist (structure test)."""
    # Test text extraction endpoint structure
    response = client.post("/api/v1/extract/text", json={})
    # Should return 422 (validation error) not 404 (not found)
    assert response.status_code == 422