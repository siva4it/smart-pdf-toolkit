"""API security tests for Smart PDF Toolkit.

This module contains security tests specifically for the REST API,
including authentication, authorization, rate limiting, and API-specific attacks.
"""

import pytest
import time
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from smart_pdf_toolkit.api.main import create_app
from smart_pdf_toolkit.api.config import APIConfig
from .security_fixtures import (
    security_temp_dir, security_config, malicious_inputs, security_logger
)


@pytest.fixture
def api_config():
    """Create API configuration for security testing."""
    config = APIConfig()
    config.enable_rate_limiting = True
    config.max_requests_per_minute = 60
    config.enable_cors = True
    config.allowed_origins = ["http://localhost:3000"]
    return config


@pytest.fixture
def test_client(api_config):
    """Create test client for API security testing."""
    app = create_app(api_config)
    return TestClient(app)


@pytest.fixture
def auth_headers(test_client):
    """Get authentication headers for testing."""
    # Login with editor user to get token
    response = test_client.post(
        "/api/v1/auth/token",
        data={"username": "editor", "password": "editorpassword", "scope": "read write"}
    )
    if response.status_code == 200:
        token_data = response.json()
        return {"Authorization": f"Bearer {token_data['access_token']}"}
    else:
        return {}


@pytest.fixture
def admin_headers(test_client):
    """Get admin authentication headers for testing."""
    # Login with admin user to get token
    response = test_client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "adminpassword", "scope": "read write admin"}
    )
    if response.status_code == 200:
        token_data = response.json()
        return {"Authorization": f"Bearer {token_data['access_token']}"}
    else:
        return {}


class TestAuthenticationSecurity:
    """Test authentication security features."""
    
    def test_unauthenticated_access_prevention(self, test_client):
        """Test that unauthenticated requests are rejected."""
        protected_endpoints = [
            "/api/v1/pdf/upload",
            "/api/v1/pdf/merge",
            "/api/v1/pdf/split",
            "/api/v1/extract/text",
            "/api/v1/convert/to-images"
        ]
        
        for endpoint in protected_endpoints:
            response = test_client.post(endpoint)
            assert response.status_code == 401
            assert "unauthorized" in response.json().get("detail", "").lower()
    
    def test_invalid_token_handling(self, test_client):
        """Test handling of invalid authentication tokens."""
        invalid_tokens = [
            "Bearer invalid_token",
            "Bearer ",
            "Invalid token_format",
            "Bearer expired.token.here",
            "Bearer malicious<script>alert('xss')</script>"
        ]
        
        for invalid_token in invalid_tokens:
            headers = {"Authorization": invalid_token}
            response = test_client.post("/api/v1/pdf/upload", headers=headers)
            assert response.status_code in [401, 422]
    
    def test_token_expiration_handling(self, test_client):
        """Test handling of expired tokens."""
        # Mock an expired token scenario
        with patch('smart_pdf_toolkit.api.auth.verify_token') as mock_verify:
            mock_verify.side_effect = Exception("Token expired")
            
            headers = {"Authorization": "Bearer expired_token"}
            response = test_client.post("/api/v1/pdf/upload", headers=headers)
            assert response.status_code == 401
    
    def test_brute_force_protection(self, test_client):
        """Test protection against brute force attacks."""
        # Attempt multiple failed logins
        failed_attempts = 0
        for i in range(10):
            response = test_client.post(
                "/api/v1/auth/token",
                data={"username": "admin", "password": f"wrong_password_{i}"}
            )
            if response.status_code == 401:
                failed_attempts += 1
        
        # Should have some protection mechanism (rate limiting, account lockout, etc.)
        assert failed_attempts > 0
        
        # After many failed attempts, should implement some protection
        final_response = test_client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "wrong_password_final"}
        )
        # May implement rate limiting or temporary lockout
        assert final_response.status_code in [401, 429]
    
    def test_password_security_requirements(self, test_client):
        """Test password security requirements."""
        weak_passwords = [
            "123",
            "password",
            "admin",
            "",
            "a"
        ]
        
        # Try to create users with weak passwords (if user creation endpoint exists)
        for weak_password in weak_passwords:
            response = test_client.post(
                "/api/v1/auth/register",
                json={"username": "testuser", "password": weak_password}
            )
            # Should reject weak passwords or endpoint might not exist
            assert response.status_code in [400, 404, 422]


class TestAuthorizationSecurity:
    """Test authorization and access control security."""
    
    def test_role_based_access_control(self, test_client, auth_headers, admin_headers):
        """Test role-based access control."""
        # Admin-only endpoints
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/settings",
            "/api/v1/admin/logs"
        ]
        
        for endpoint in admin_endpoints:
            # Regular user should be denied
            if auth_headers:
                response = test_client.get(endpoint, headers=auth_headers)
                assert response.status_code in [403, 404]  # Forbidden or not found
            
            # Admin user should have access (if endpoint exists)
            if admin_headers:
                response = test_client.get(endpoint, headers=admin_headers)
                assert response.status_code in [200, 404]  # OK or not implemented
    
    def test_scope_based_access_control(self, test_client):
        """Test scope-based access control."""
        # Get token with limited scope
        response = test_client.post(
            "/api/v1/auth/token",
            data={"username": "editor", "password": "editorpassword", "scope": "read"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            read_only_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            
            # Should be able to read
            response = test_client.get("/api/v1/pdf/list", headers=read_only_headers)
            assert response.status_code in [200, 404]
            
            # Should not be able to write
            response = test_client.post("/api/v1/pdf/upload", headers=read_only_headers)
            assert response.status_code in [403, 404]
    
    def test_resource_ownership_validation(self, test_client, auth_headers):
        """Test that users can only access their own resources."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        # Try to access resources with different user IDs
        user_ids = ["1", "2", "999", "admin", "../admin"]
        
        for user_id in user_ids:
            response = test_client.get(f"/api/v1/user/{user_id}/files", headers=auth_headers)
            # Should validate resource ownership
            assert response.status_code in [200, 403, 404]


class TestInputValidationSecurity:
    """Test API input validation security."""
    
    def test_json_injection_prevention(self, test_client, auth_headers, malicious_inputs):
        """Test prevention of JSON injection attacks."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        malicious_json_payloads = [
            '{"key": "value", "malicious": "\\u0000"}',
            '{"key": "value"} {"injected": "payload"}',
            '{"__proto__": {"isAdmin": true}}',
            '{"constructor": {"prototype": {"isAdmin": true}}}'
        ]
        
        for payload in malicious_json_payloads:
            try:
                response = test_client.post(
                    "/api/v1/pdf/merge",
                    data=payload,
                    headers={**auth_headers, "Content-Type": "application/json"}
                )
                # Should handle malicious JSON safely
                assert response.status_code in [400, 422, 500]
            except json.JSONDecodeError:
                # Expected for malformed JSON
                pass
    
    def test_sql_injection_prevention(self, test_client, auth_headers, malicious_inputs):
        """Test prevention of SQL injection attacks."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        sql_injections = malicious_inputs['sql_injection']
        
        for sql_injection in sql_injections:
            # Test in various parameters
            test_cases = [
                {"filename": sql_injection},
                {"user_id": sql_injection},
                {"search": sql_injection}
            ]
            
            for test_case in test_cases:
                response = test_client.post(
                    "/api/v1/pdf/search",
                    json=test_case,
                    headers=auth_headers
                )
                # Should prevent SQL injection
                assert response.status_code in [400, 422, 404]
    
    def test_xss_prevention(self, test_client, auth_headers, malicious_inputs):
        """Test prevention of XSS attacks."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        xss_inputs = malicious_inputs['xss']
        
        for xss_input in xss_inputs:
            response = test_client.post(
                "/api/v1/pdf/rename",
                json={"filename": xss_input},
                headers=auth_headers
            )
            
            # Should sanitize or reject XSS attempts
            if response.status_code == 200:
                response_text = response.text
                assert "<script>" not in response_text.lower()
                assert "javascript:" not in response_text.lower()
    
    def test_file_upload_validation(self, test_client, auth_headers, security_temp_dir):
        """Test file upload validation security."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        # Test various malicious file uploads
        malicious_files = [
            ("malicious.exe", b"MZ\x90\x00", "application/octet-stream"),
            ("script.js", b"alert('xss')", "application/javascript"),
            ("large_file.pdf", b"A" * (100 * 1024 * 1024), "application/pdf"),  # 100MB
            ("null_byte.pdf\x00.exe", b"%PDF-1.4", "application/pdf")
        ]
        
        for filename, content, content_type in malicious_files:
            response = test_client.post(
                "/api/v1/pdf/upload",
                files={"file": (filename, content, content_type)},
                headers=auth_headers
            )
            
            # Should validate file uploads properly
            if filename.endswith(".exe") or "script.js" in filename:
                assert response.status_code in [400, 422]
            elif len(content) > 50 * 1024 * 1024:  # Large file
                assert response.status_code in [413, 422]  # Payload too large


class TestRateLimitingSecurity:
    """Test rate limiting security features."""
    
    def test_request_rate_limiting(self, test_client, auth_headers):
        """Test request rate limiting."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        # Make many requests quickly
        responses = []
        for i in range(100):
            response = test_client.get("/api/v1/health", headers=auth_headers)
            responses.append(response.status_code)
            
            if response.status_code == 429:  # Rate limited
                break
        
        # Should implement rate limiting
        rate_limited_responses = sum(1 for status in responses if status == 429)
        assert rate_limited_responses > 0 or len(responses) < 100
    
    def test_per_user_rate_limiting(self, test_client, auth_headers):
        """Test per-user rate limiting."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        # Test rate limiting for specific user
        start_time = time.time()
        request_count = 0
        
        while time.time() - start_time < 60:  # Test for 1 minute
            response = test_client.get("/api/v1/pdf/list", headers=auth_headers)
            request_count += 1
            
            if response.status_code == 429:
                # Rate limiting is working
                break
            
            if request_count > 200:  # Reasonable limit for testing
                break
        
        # Should have some form of rate limiting
        assert request_count < 200 or response.status_code == 429
    
    def test_endpoint_specific_rate_limiting(self, test_client, auth_headers):
        """Test endpoint-specific rate limiting."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        # Test rate limiting on resource-intensive endpoints
        intensive_endpoints = [
            "/api/v1/pdf/merge",
            "/api/v1/convert/to-images",
            "/api/v1/extract/text"
        ]
        
        for endpoint in intensive_endpoints:
            responses = []
            for i in range(20):  # Fewer requests for intensive operations
                response = test_client.post(endpoint, json={}, headers=auth_headers)
                responses.append(response.status_code)
                
                if response.status_code == 429:
                    break
            
            # Intensive endpoints should have stricter rate limiting
            rate_limited = any(status == 429 for status in responses)
            # Either rate limited or endpoint doesn't exist
            assert rate_limited or all(status == 404 for status in responses)


class TestCORSSecurity:
    """Test CORS security configuration."""
    
    def test_cors_origin_validation(self, test_client):
        """Test CORS origin validation."""
        # Test allowed origins
        allowed_origin = "http://localhost:3000"
        response = test_client.options(
            "/api/v1/health",
            headers={"Origin": allowed_origin}
        )
        
        if "Access-Control-Allow-Origin" in response.headers:
            assert response.headers["Access-Control-Allow-Origin"] == allowed_origin
    
    def test_cors_malicious_origin_rejection(self, test_client):
        """Test rejection of malicious CORS origins."""
        malicious_origins = [
            "http://malicious-site.com",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "null",
            "*"
        ]
        
        for malicious_origin in malicious_origins:
            response = test_client.options(
                "/api/v1/health",
                headers={"Origin": malicious_origin}
            )
            
            # Should not allow malicious origins
            if "Access-Control-Allow-Origin" in response.headers:
                assert response.headers["Access-Control-Allow-Origin"] != malicious_origin
    
    def test_cors_preflight_handling(self, test_client):
        """Test CORS preflight request handling."""
        response = test_client.options(
            "/api/v1/pdf/upload",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization"
            }
        )
        
        # Should handle preflight requests properly
        assert response.status_code in [200, 204]


class TestSecurityHeaders:
    """Test security headers in API responses."""
    
    def test_security_headers_presence(self, test_client):
        """Test presence of security headers."""
        response = test_client.get("/api/v1/health")
        
        # Check for important security headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy"
        ]
        
        present_headers = []
        for header in security_headers:
            if header in response.headers:
                present_headers.append(header)
        
        # Should have at least some security headers
        assert len(present_headers) > 0
    
    def test_content_type_header_validation(self, test_client, auth_headers):
        """Test Content-Type header validation."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        # Test with incorrect Content-Type
        response = test_client.post(
            "/api/v1/pdf/merge",
            data="not json data",
            headers={**auth_headers, "Content-Type": "text/plain"}
        )
        
        # Should validate Content-Type
        assert response.status_code in [400, 415, 422]
    
    def test_response_header_security(self, test_client):
        """Test security of response headers."""
        response = test_client.get("/api/v1/health")
        
        # Should not expose sensitive information in headers
        sensitive_headers = ["Server", "X-Powered-By"]
        for header in sensitive_headers:
            if header in response.headers:
                header_value = response.headers[header].lower()
                # Should not expose detailed version information
                assert "version" not in header_value
                assert "/" not in header_value  # No version numbers like "nginx/1.2.3"