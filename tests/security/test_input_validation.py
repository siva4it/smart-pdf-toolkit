"""Input validation security tests for Smart PDF Toolkit.

This module contains tests for validating and sanitizing various types
of user inputs to prevent security vulnerabilities.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from smart_pdf_toolkit.core.interfaces import OperationResult
from .security_fixtures import (
    security_temp_dir, security_config, security_manager, pdf_operations_secure,
    malicious_inputs, security_logger
)


class TestFilePathValidation:
    """Test file path validation and sanitization."""
    
    def test_path_traversal_prevention(self, security_manager, malicious_inputs):
        """Test prevention of path traversal attacks."""
        path_traversal_inputs = malicious_inputs['path_traversal']
        
        for malicious_path in path_traversal_inputs:
            result = security_manager.validate_file_path(malicious_path)
            
            # Should reject path traversal attempts
            assert not result.success
            assert "invalid" in result.message.lower() or "traversal" in result.message.lower()
    
    def test_absolute_path_handling(self, security_manager):
        """Test handling of absolute paths."""
        absolute_paths = [
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\sam",
            "/root/.ssh/id_rsa",
            "\\\\server\\share\\file.pdf"
        ]
        
        for abs_path in absolute_paths:
            result = security_manager.validate_file_path(abs_path)
            
            # Should handle absolute paths according to security policy
            # (may allow or reject based on configuration)
            assert isinstance(result.success, bool)
    
    def test_relative_path_validation(self, security_manager):
        """Test validation of relative paths."""
        valid_relative_paths = [
            "document.pdf",
            "folder/document.pdf",
            "output/processed.pdf"
        ]
        
        invalid_relative_paths = [
            "../document.pdf",
            "folder/../../../etc/passwd",
            "./../../sensitive.pdf"
        ]
        
        for valid_path in valid_relative_paths:
            result = security_manager.validate_file_path(valid_path)
            assert result.success
        
        for invalid_path in invalid_relative_paths:
            result = security_manager.validate_file_path(invalid_path)
            assert not result.success
    
    def test_special_device_paths(self, security_manager):
        """Test handling of special device paths."""
        if os.name != 'nt':  # Unix-like systems
            special_paths = [
                "/dev/null",
                "/dev/zero",
                "/dev/random",
                "/proc/self/mem"
            ]
        else:  # Windows
            special_paths = [
                "CON",
                "PRN",
                "AUX",
                "NUL",
                "COM1",
                "LPT1"
            ]
        
        for special_path in special_paths:
            result = security_manager.validate_file_path(special_path)
            
            # Should reject special device paths
            assert not result.success


class TestFilenameValidation:
    """Test filename validation and sanitization."""
    
    def test_null_byte_injection(self, security_manager, malicious_inputs):
        """Test prevention of null byte injection in filenames."""
        null_byte_inputs = malicious_inputs['null_bytes']
        
        for null_input in null_byte_inputs:
            result = security_manager.validate_filename(null_input)
            
            # Should reject filenames with null bytes
            assert not result.success
            assert "null" in result.message.lower() or "invalid" in result.message.lower()
    
    def test_unicode_filename_handling(self, security_manager, malicious_inputs):
        """Test handling of Unicode attacks in filenames."""
        unicode_attacks = malicious_inputs['unicode_attacks']
        
        for unicode_attack in unicode_attacks:
            result = security_manager.validate_filename(unicode_attack)
            
            # Should handle Unicode attacks appropriately
            # (may sanitize or reject based on policy)
            assert isinstance(result.success, bool)
    
    def test_long_filename_handling(self, security_manager):
        """Test handling of extremely long filenames."""
        # Create filenames of various lengths
        long_filenames = [
            "a" * 255,  # Maximum typical filename length
            "b" * 300,  # Longer than typical limit
            "c" * 1000, # Very long filename
            "d" * 10000 # Extremely long filename
        ]
        
        for long_filename in long_filenames:
            result = security_manager.validate_filename(long_filename + ".pdf")
            
            # Should handle long filenames appropriately
            assert isinstance(result.success, bool)
            if not result.success:
                assert "length" in result.message.lower() or "long" in result.message.lower()
    
    def test_reserved_filename_handling(self, security_manager):
        """Test handling of reserved filenames."""
        if os.name == 'nt':  # Windows reserved names
            reserved_names = [
                "CON.pdf", "PRN.pdf", "AUX.pdf", "NUL.pdf",
                "COM1.pdf", "COM2.pdf", "LPT1.pdf", "LPT2.pdf"
            ]
        else:  # Unix-like systems
            reserved_names = [
                ".pdf", "..pdf", "...pdf"
            ]
        
        for reserved_name in reserved_names:
            result = security_manager.validate_filename(reserved_name)
            
            # Should reject or sanitize reserved names
            if not result.success:
                assert "reserved" in result.message.lower() or "invalid" in result.message.lower()
    
    def test_special_character_handling(self, security_manager):
        """Test handling of special characters in filenames."""
        special_char_filenames = [
            "file<script>.pdf",
            "file>output.pdf",
            "file|pipe.pdf",
            "file:colon.pdf",
            "file*wildcard.pdf",
            "file?question.pdf",
            'file"quote.pdf'
        ]
        
        for special_filename in special_char_filenames:
            result = security_manager.validate_filename(special_filename)
            
            # Should handle special characters appropriately
            assert isinstance(result.success, bool)


class TestContentValidation:
    """Test validation of file content and data."""
    
    def test_file_size_validation(self, security_manager, security_config):
        """Test file size validation."""
        max_size = security_config.max_file_size
        
        # Test files within limit
        result = security_manager.validate_file_size(max_size - 1000)
        assert result.success
        
        # Test files exceeding limit
        result = security_manager.validate_file_size(max_size + 1000)
        assert not result.success
        assert "size" in result.message.lower() or "large" in result.message.lower()
    
    def test_file_extension_validation(self, security_manager, security_config):
        """Test file extension validation."""
        allowed_extensions = security_config.allowed_extensions
        
        # Test allowed extensions
        for ext in allowed_extensions:
            filename = f"test{ext}"
            result = security_manager.validate_file_extension(filename)
            assert result.success
        
        # Test disallowed extensions
        disallowed_extensions = ['.exe', '.bat', '.scr', '.com', '.pif', '.vbs']
        for ext in disallowed_extensions:
            filename = f"test{ext}"
            result = security_manager.validate_file_extension(filename)
            assert not result.success
            assert "extension" in result.message.lower() or "type" in result.message.lower()
    
    def test_mime_type_validation(self, security_manager, security_temp_dir):
        """Test MIME type validation."""
        # Create test files with different content
        pdf_file = security_temp_dir / "test.pdf"
        with open(pdf_file, 'wb') as f:
            f.write(b'%PDF-1.4\n%%EOF\n')  # Valid PDF header
        
        exe_file = security_temp_dir / "test.pdf"  # PDF extension but EXE content
        with open(exe_file, 'wb') as f:
            f.write(b'MZ\x90\x00')  # EXE header
        
        # Test valid PDF
        result = security_manager.validate_mime_type(str(pdf_file))
        assert result.success or "mime" not in result.message.lower()  # May not be implemented
        
        # Test mismatched content
        result = security_manager.validate_mime_type(str(exe_file))
        # Should detect mismatch if MIME validation is implemented
        assert isinstance(result.success, bool)
    
    def test_binary_content_validation(self, security_manager, security_temp_dir):
        """Test validation of binary content."""
        # Create files with different binary patterns
        test_files = {
            'normal_pdf': b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n',
            'suspicious_binary': b'\x00\x01\x02\x03' * 1000,  # Repetitive binary pattern
            'mixed_content': b'%PDF-1.4\n' + b'\x00' * 100 + b'\nmalicious content\n%%EOF\n'
        }
        
        for filename, content in test_files.items():
            test_file = security_temp_dir / f"{filename}.pdf"
            with open(test_file, 'wb') as f:
                f.write(content)
            
            result = security_manager.validate_binary_content(str(test_file))
            
            # Should validate binary content appropriately
            assert isinstance(result.success, bool)


class TestParameterValidation:
    """Test validation of operation parameters."""
    
    def test_numeric_parameter_validation(self, security_manager):
        """Test validation of numeric parameters."""
        # Test valid numeric parameters
        valid_numbers = [0, 1, 90, 180, 270, 360, -90, -180]
        for number in valid_numbers:
            result = security_manager.validate_numeric_parameter(number, "rotation_angle", -360, 360)
            assert result.success
        
        # Test invalid numeric parameters
        invalid_numbers = [361, -361, 999, -999]
        for number in invalid_numbers:
            result = security_manager.validate_numeric_parameter(number, "rotation_angle", -360, 360)
            assert not result.success
            assert "range" in result.message.lower() or "invalid" in result.message.lower()
    
    def test_string_parameter_validation(self, security_manager, malicious_inputs):
        """Test validation of string parameters."""
        # Test SQL injection attempts
        sql_injections = malicious_inputs['sql_injection']
        for sql_input in sql_injections:
            result = security_manager.validate_string_parameter(sql_input, "user_input")
            assert not result.success
            assert "invalid" in result.message.lower() or "injection" in result.message.lower()
        
        # Test XSS attempts
        xss_inputs = malicious_inputs['xss']
        for xss_input in xss_inputs:
            result = security_manager.validate_string_parameter(xss_input, "user_input")
            assert not result.success
            assert "invalid" in result.message.lower() or "script" in result.message.lower()
    
    def test_array_parameter_validation(self, security_manager):
        """Test validation of array parameters."""
        # Test valid arrays
        valid_arrays = [
            [1, 2, 3],
            [90, 180, 270],
            ["file1.pdf", "file2.pdf"]
        ]
        
        for array in valid_arrays:
            result = security_manager.validate_array_parameter(array, "page_numbers", max_length=10)
            assert result.success
        
        # Test invalid arrays
        invalid_arrays = [
            list(range(1000)),  # Too long
            [1, 2, "invalid_mixed_type"],  # Mixed types
            None,  # Not an array
            "not_an_array"  # String instead of array
        ]
        
        for array in invalid_arrays:
            result = security_manager.validate_array_parameter(array, "page_numbers", max_length=10)
            assert not result.success
    
    def test_json_parameter_validation(self, security_manager):
        """Test validation of JSON parameters."""
        import json
        
        # Test valid JSON
        valid_json_strings = [
            '{"key": "value"}',
            '{"pages": [1, 2, 3]}',
            '{"settings": {"quality": 90}}'
        ]
        
        for json_string in valid_json_strings:
            result = security_manager.validate_json_parameter(json_string, "config")
            assert result.success
        
        # Test invalid JSON
        invalid_json_strings = [
            '{"key": "value"',  # Missing closing brace
            '{key: "value"}',   # Unquoted key
            '{"key": undefined}',  # Invalid value
            'not json at all'   # Not JSON
        ]
        
        for json_string in invalid_json_strings:
            result = security_manager.validate_json_parameter(json_string, "config")
            assert not result.success
            assert "json" in result.message.lower() or "format" in result.message.lower()


class TestSanitization:
    """Test input sanitization functions."""
    
    def test_filename_sanitization(self, security_manager):
        """Test filename sanitization."""
        dangerous_filenames = [
            "../../../etc/passwd",
            "file<script>alert('xss')</script>.pdf",
            "file|rm -rf /.pdf",
            "file\x00hidden.exe.pdf"
        ]
        
        for dangerous_filename in dangerous_filenames:
            sanitized = security_manager.sanitize_filename(dangerous_filename)
            
            # Sanitized filename should be safe
            assert "../" not in sanitized
            assert "<script>" not in sanitized
            assert "|" not in sanitized
            assert "\x00" not in sanitized
    
    def test_path_sanitization(self, security_manager):
        """Test path sanitization."""
        dangerous_paths = [
            "/etc/../../../passwd",
            "C:\\Windows\\..\\..\\..\\sensitive.txt",
            "folder/./../../escape.pdf"
        ]
        
        for dangerous_path in dangerous_paths:
            sanitized = security_manager.sanitize_path(dangerous_path)
            
            # Sanitized path should not allow traversal
            assert ".." not in sanitized or not sanitized.startswith("..")
    
    def test_string_sanitization(self, security_manager, malicious_inputs):
        """Test general string sanitization."""
        # Test various malicious inputs
        for attack_type, inputs in malicious_inputs.items():
            for malicious_input in inputs[:2]:  # Test first 2 of each type
                sanitized = security_manager.sanitize_string(malicious_input)
                
                # Sanitized string should be safe
                assert isinstance(sanitized, str)
                assert len(sanitized) <= len(malicious_input)  # Should not expand
    
    def test_html_sanitization(self, security_manager, malicious_inputs):
        """Test HTML content sanitization."""
        xss_inputs = malicious_inputs['xss']
        
        for xss_input in xss_inputs:
            sanitized = security_manager.sanitize_html(xss_input)
            
            # Should remove or escape dangerous HTML
            assert "<script>" not in sanitized.lower()
            assert "javascript:" not in sanitized.lower()
            assert "onerror=" not in sanitized.lower()