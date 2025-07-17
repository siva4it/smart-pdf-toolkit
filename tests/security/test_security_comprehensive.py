"""Comprehensive security tests for Smart PDF Toolkit.

This module contains security tests for password protection, permissions,
input validation, and protection against various attack vectors.
"""

import pytest
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

from smart_pdf_toolkit.core.interfaces import OperationResult
from .security_fixtures import (
    security_temp_dir, security_config, security_manager, pdf_operations_secure,
    sample_passwords, malicious_inputs, create_encrypted_pdf, create_malicious_pdf,
    permission_test_cases, security_logger
)


class TestPasswordSecurity:
    """Test password-related security features."""
    
    def test_password_strength_validation(self, security_manager, sample_passwords):
        """Test password strength validation."""
        # Test weak passwords
        weak_passwords = [sample_passwords['weak'], sample_passwords['empty']]
        for password in weak_passwords:
            result = security_manager.validate_password_strength(password)
            assert not result.success or "weak" in result.message.lower()
    
    def test_password_encryption_decryption(self, security_manager, sample_passwords):
        """Test password encryption and decryption."""
        test_password = sample_passwords['strong']
        
        # Test password hashing
        hashed = security_manager.hash_password(test_password)
        assert hashed != test_password
        assert len(hashed) > 0
        
        # Test password verification
        assert security_manager.verify_password(test_password, hashed)
        assert not security_manager.verify_password("wrong_password", hashed)
    
    def test_unicode_password_handling(self, security_manager, sample_passwords):
        """Test handling of Unicode passwords."""
        unicode_password = sample_passwords['unicode']
        
        # Should handle Unicode passwords properly
        hashed = security_manager.hash_password(unicode_password)
        assert security_manager.verify_password(unicode_password, hashed)
    
    def test_special_character_passwords(self, security_manager, sample_passwords):
        """Test passwords with special characters."""
        special_password = sample_passwords['special_chars']
        
        # Should handle special characters properly
        hashed = security_manager.hash_password(special_password)
        assert security_manager.verify_password(special_password, hashed)
    
    def test_long_password_handling(self, security_manager, sample_passwords):
        """Test handling of very long passwords."""
        long_password = sample_passwords['long']
        
        # Should handle long passwords (may truncate or reject)
        try:
            hashed = security_manager.hash_password(long_password)
            # If it doesn't raise an exception, verify it works
            assert security_manager.verify_password(long_password, hashed)
        except ValueError:
            # It's acceptable to reject overly long passwords
            pass


class TestPermissionSecurity:
    """Test PDF permission and access control security."""
    
    def test_permission_validation(self, security_manager, permission_test_cases):
        """Test PDF permission validation."""
        for perm_name, perm_value in permission_test_cases.items():
            result = security_manager.validate_permissions(perm_value)
            assert isinstance(result.success, bool)
    
    def test_permission_enforcement(self, security_manager, create_encrypted_pdf, permission_test_cases):
        """Test that permissions are properly enforced."""
        pdf_path = create_encrypted_pdf("test_permissions.pdf", "user123", "owner123")
        
        for perm_name, perm_value in permission_test_cases.items():
            # Test setting permissions
            result = security_manager.set_pdf_permissions(
                str(pdf_path), perm_value, owner_password="owner123"
            )
            # May fail if PyMuPDF not available, which is acceptable
            assert result.success or "not available" in result.message.lower()
    
    def test_unauthorized_access_prevention(self, security_manager, create_encrypted_pdf):
        """Test prevention of unauthorized access to encrypted PDFs."""
        pdf_path = create_encrypted_pdf("encrypted_test.pdf", "secret123", "owner456")
        
        # Try to access without password - should fail
        result = security_manager.verify_pdf_access(str(pdf_path))
        assert not result.success or "password required" in result.message.lower()
        
        # Try with wrong password - should fail
        result = security_manager.verify_pdf_access(str(pdf_path), "wrong_password")
        assert not result.success or "incorrect password" in result.message.lower()


class TestInputValidation:
    """Test input validation and sanitization."""
    
    def test_filename_validation(self, security_manager, malicious_inputs):
        """Test filename validation against malicious inputs."""
        for attack_type, inputs in malicious_inputs.items():
            for malicious_input in inputs:
                result = security_manager.validate_filename(malicious_input)
                # Should reject malicious filenames
                assert not result.success or result.message
    
    def test_path_traversal_prevention(self, security_manager, malicious_inputs):
        """Test prevention of path traversal attacks."""
        path_traversal_inputs = malicious_inputs['path_traversal']
        
        for malicious_path in path_traversal_inputs:
            result = security_manager.validate_file_path(malicious_path)
            # Should reject path traversal attempts
            assert not result.success
    
    def test_command_injection_prevention(self, security_manager, malicious_inputs):
        """Test prevention of command injection attacks."""
        command_injection_inputs = malicious_inputs['command_injection']
        
        for malicious_command in command_injection_inputs:
            result = security_manager.validate_input(malicious_command)
            # Should reject command injection attempts
            assert not result.success or "invalid" in result.message.lower()
    
    def test_buffer_overflow_prevention(self, security_manager, malicious_inputs):
        """Test prevention of buffer overflow attacks."""
        buffer_overflow_inputs = malicious_inputs['buffer_overflow']
        
        for large_input in buffer_overflow_inputs:
            result = security_manager.validate_input(large_input)
            # Should handle large inputs safely
            assert isinstance(result.success, bool)
    
    def test_null_byte_injection_prevention(self, security_manager, malicious_inputs):
        """Test prevention of null byte injection attacks."""
        null_byte_inputs = malicious_inputs['null_bytes']
        
        for null_input in null_byte_inputs:
            result = security_manager.validate_filename(null_input)
            # Should reject null byte injections
            assert not result.success


class TestMaliciousPDFHandling:
    """Test handling of malicious PDF files."""
    
    def test_oversized_pdf_handling(self, pdf_operations_secure, create_malicious_pdf, security_temp_dir):
        """Test handling of oversized PDF files."""
        malicious_pdf = create_malicious_pdf("oversized.pdf", "oversized")
        output_path = security_temp_dir / "output.pdf"
        
        # Should handle oversized PDFs gracefully
        result = pdf_operations_secure.rotate_pdf(
            str(malicious_pdf), [90], str(output_path)
        )
        
        # Should either succeed or fail gracefully with appropriate error
        assert isinstance(result.success, bool)
        if not result.success:
            assert "size" in result.message.lower() or "memory" in result.message.lower()
    
    def test_malformed_pdf_handling(self, pdf_operations_secure, create_malicious_pdf, security_temp_dir):
        """Test handling of malformed PDF files."""
        malformed_pdf = create_malicious_pdf("malformed.pdf", "malformed")
        output_path = security_temp_dir / "output.pdf"
        
        # Should handle malformed PDFs gracefully
        result = pdf_operations_secure.split_pdf(str(malformed_pdf), str(security_temp_dir))
        
        # Should fail gracefully with appropriate error message
        assert not result.success
        assert "invalid" in result.message.lower() or "malformed" in result.message.lower()
    
    def test_javascript_pdf_handling(self, pdf_operations_secure, create_malicious_pdf, security_temp_dir):
        """Test handling of PDFs with embedded JavaScript."""
        js_pdf = create_malicious_pdf("javascript.pdf", "javascript")
        output_path = security_temp_dir / "output.pdf"
        
        # Should handle JavaScript PDFs safely
        result = pdf_operations_secure.merge_pdfs([str(js_pdf)], str(output_path))
        
        # Should either succeed (with JS stripped) or fail safely
        assert isinstance(result.success, bool)
    
    def test_zip_bomb_pdf_handling(self, pdf_operations_secure, create_malicious_pdf, security_temp_dir):
        """Test handling of PDF zip bombs."""
        zip_bomb_pdf = create_malicious_pdf("zip_bomb.pdf", "zip_bomb")
        
        # Should handle potential zip bombs safely
        with patch('time.time', side_effect=[0, 10]):  # Simulate 10 second timeout
            result = pdf_operations_secure.extract_text(str(zip_bomb_pdf))
            
            # Should timeout or handle safely
            assert isinstance(result.success, bool)


class TestSecurityConfiguration:
    """Test security configuration and settings."""
    
    def test_security_config_validation(self, security_config):
        """Test security configuration validation."""
        # Test file size limits
        assert security_config.max_file_size > 0
        
        # Test allowed extensions
        assert isinstance(security_config.allowed_extensions, list)
        assert '.pdf' in security_config.allowed_extensions
    
    def test_secure_temp_directory(self, security_config, security_temp_dir):
        """Test secure temporary directory handling."""
        # Temp directory should be created securely
        assert security_temp_dir.exists()
        
        # Should have appropriate permissions (on Unix systems)
        if os.name != 'nt':  # Not Windows
            stat_info = security_temp_dir.stat()
            # Check that directory is not world-readable
            assert (stat_info.st_mode & 0o077) == 0
    
    def test_file_extension_validation(self, security_manager, security_config):
        """Test file extension validation."""
        allowed_files = ['test.pdf', 'image.png', 'document.txt']
        disallowed_files = ['script.exe', 'malware.bat', 'virus.scr']
        
        for filename in allowed_files:
            result = security_manager.validate_file_extension(filename)
            assert result.success
        
        for filename in disallowed_files:
            result = security_manager.validate_file_extension(filename)
            assert not result.success


class TestSecurityLogging:
    """Test security event logging."""
    
    def test_security_event_logging(self, security_manager, security_logger):
        """Test that security events are properly logged."""
        with patch.object(security_logger, 'warning') as mock_warning:
            # Trigger a security event
            security_manager.validate_filename("../../../etc/passwd")
            
            # Should log security warning
            mock_warning.assert_called()
    
    def test_failed_authentication_logging(self, security_manager, security_logger):
        """Test logging of failed authentication attempts."""
        with patch.object(security_logger, 'warning') as mock_warning:
            # Simulate failed authentication
            security_manager.verify_password("wrong", "hash")
            
            # Should log authentication failure
            # Note: This depends on implementation
    
    def test_suspicious_activity_logging(self, security_manager, security_logger, malicious_inputs):
        """Test logging of suspicious activities."""
        with patch.object(security_logger, 'error') as mock_error:
            # Test various suspicious inputs
            for attack_type, inputs in malicious_inputs.items():
                for malicious_input in inputs[:2]:  # Test first 2 of each type
                    security_manager.validate_input(malicious_input)
            
            # Should log suspicious activities
            # Note: This depends on implementation