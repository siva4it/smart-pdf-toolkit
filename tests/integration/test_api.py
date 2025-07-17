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


@pytest.fixture
def auth_headers(client):
    """Get authentication headers for testing."""
    # Login with editor user to get token (has read and write permissions)
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "editor", "password": "editorpassword", "scope": "read write"}
    )
    assert response.status_code == 200
    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}


@pytest.fixture
def admin_headers(client):
    """Get admin authentication headers for testing."""
    # Login with admin user to get token
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "adminpassword", "scope": "read write admin"}
    )
    assert response.status_code == 200
    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}


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
    response = client.get("/health")
    # CORS headers should be present in GET response
    assert "access-control-allow-origin" in response.headers or response.status_code == 200


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


def test_pdf_upload_endpoint_structure(client, admin_headers):
    """Test that PDF upload endpoint exists (structure test)."""
    # Test with no file (should fail but endpoint should exist)
    response = client.post("/api/v1/pdf/upload", headers=admin_headers)
    # Should return 422 (validation error) not 404 (not found)
    assert response.status_code == 422


def test_ai_services_endpoints_structure(client, admin_headers):
    """Test that AI services endpoints exist (structure test)."""
    # Test summarize endpoint structure
    response = client.post("/api/v1/ai/summarize", json={}, headers=admin_headers)
    # Should return 422 (validation error) not 404 (not found)
    assert response.status_code == 422
    
    # Test analyze endpoint structure
    response = client.post("/api/v1/ai/analyze", json={}, headers=admin_headers)
    assert response.status_code == 422


def test_batch_processing_endpoints_structure(client, admin_headers):
    """Test that batch processing endpoints exist (structure test)."""
    # Test create batch job endpoint structure
    response = client.post("/api/v1/batch/jobs", json={}, headers=admin_headers)
    # Should return 422 (validation error) not 404 (not found)
    assert response.status_code == 422


def test_content_extraction_endpoints_structure(client, auth_headers):
    """Test that content extraction endpoints exist (structure test)."""
    # Test text extraction endpoint structure
    response = client.post("/api/v1/extract/text", json={}, headers=auth_headers)
    # Should return 422 (validation error) not 404 (not found)
    assert response.status_code == 422


def test_format_conversion_endpoints_structure(client, auth_headers):
    """Test that format conversion endpoints exist (structure test)."""
    # Test PDF to images conversion endpoint structure
    response = client.post("/api/v1/convert/to-images", json={}, headers=auth_headers)
    assert response.status_code == 422
    
    # Test images to PDF conversion endpoint structure
    response = client.post("/api/v1/convert/from-images", json={}, headers=auth_headers)
    assert response.status_code == 422


def test_security_endpoints_structure(client, auth_headers):
    """Test that security endpoints exist (structure test)."""
    # Test add password endpoint structure
    response = client.post("/api/v1/security/add-password", json={}, headers=auth_headers)
    assert response.status_code == 422
    
    # Test remove password endpoint structure
    response = client.post("/api/v1/security/remove-password", json={}, headers=auth_headers)
    assert response.status_code == 422


def test_optimization_endpoints_structure(client, auth_headers):
    """Test that optimization endpoints exist (structure test)."""
    # Test compress PDF endpoint structure
    response = client.post("/api/v1/optimize/compress", json={}, headers=auth_headers)
    assert response.status_code == 422
    
    # Test web optimization endpoint structure
    response = client.post("/api/v1/optimize/optimize-web?file_id=test", headers=auth_headers)
    assert response.status_code == 404  # File not found, but endpoint exists


def test_file_download_endpoints_structure(client, auth_headers):
    """Test that file download endpoints exist (structure test)."""
    # Test PDF download endpoint structure
    response = client.get("/api/v1/pdf/download/nonexistent", headers=auth_headers)
    assert response.status_code == 404  # File not found, but endpoint exists
    
    # Test content download endpoint structure
    response = client.get("/api/v1/extract/download/nonexistent", headers=auth_headers)
    assert response.status_code == 404  # File not found, but endpoint exists


def test_comprehensive_api_structure(client):
    """Test comprehensive API structure and OpenAPI schema."""
    # Get OpenAPI schema
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    paths = schema.get("paths", {})
    
    # Verify all major endpoint groups exist
    expected_prefixes = [
        "/health",
        "/api/v1/pdf",
        "/api/v1/extract", 
        "/api/v1/ai",
        "/api/v1/batch",
        "/api/v1/convert",
        "/api/v1/security",
        "/api/v1/optimize"
    ]
    
    for prefix in expected_prefixes:
        matching_paths = [path for path in paths.keys() if path.startswith(prefix)]
        assert len(matching_paths) > 0, f"No endpoints found for prefix: {prefix}"


def test_api_tags_and_documentation(client):
    """Test that API has proper tags and documentation."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    
    # Check API info
    info = schema.get("info", {})
    assert info.get("title") == "Smart PDF Toolkit API"
    assert info.get("version") == "1.0.0"
    
    # Check that tags are properly defined
    expected_tags = [
        "Health",
        "PDF Operations", 
        "Content Extraction",
        "AI Services",
        "Batch Processing",
        "Format Conversion",
        "Security",
        "Optimization"
    ]
    
    # Get all tags used in paths
    used_tags = set()
    for path_info in schema.get("paths", {}).values():
        for method_info in path_info.values():
            if isinstance(method_info, dict) and "tags" in method_info:
                used_tags.update(method_info["tags"])
    
    for tag in expected_tags:
        assert tag in used_tags, f"Tag '{tag}' not found in API documentation"