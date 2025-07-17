"""Security test fixtures for Smart PDF Toolkit.

This module provides fixtures for security testing including
malicious PDFs, encrypted PDFs, and security validation utilities.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
import logging
from typing import List, Dict, Any, Optional

from smart_pdf_toolkit.core.config import Config
from smart_pdf_toolkit.core.security_manager import SecurityManager
from smart_pdf_toolkit.core.pdf_operations import PDFOperationsManager

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def security_temp_dir():
    """Create a temporary directory for security test files."""
    temp_dir = tempfile.mkdtemp(prefix="security_test_")
    yield Path(temp_dir)
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        logger.warning(f"Failed to clean up security temp directory {temp_dir}: {e}")


@pytest.fixture(scope="function")
def security_config(security_temp_dir):
    """Create a security-focused test configuration."""
    config = Config()
    config.output_dir = security_temp_dir
    config.temp_dir = security_temp_dir / "temp"
    config.max_file_size = 100 * 1024 * 1024  # 100MB limit for security tests
    config.allowed_extensions = ['.pdf', '.txt', '.png', '.jpg']
    return config


@pytest.fixture(scope="function")
def security_manager(security_config):
    """Create a SecurityManager instance for testing."""
    return SecurityManager(security_config)


@pytest.fixture(scope="function")
def pdf_operations_secure(security_config):
    """Create a PDFOperationsManager with security configuration."""
    return PDFOperationsManager(security_config)


@pytest.fixture(scope="function")
def sample_passwords():
    """Provide various password types for testing."""
    return {
        'weak': '123',
        'medium': 'password123',
        'strong': 'MyStr0ng!P@ssw0rd#2024',
        'unicode': 'пароль123',
        'special_chars': '!@#$%^&*()_+-=[]{}|;:,.<>?',
        'long': 'a' * 100,
        'empty': '',
        'spaces': '   password   '
    }


@pytest.fixture(scope="function")
def malicious_inputs():
    """Provide various malicious input patterns for testing."""
    return {
        'sql_injection': ["'; DROP TABLE users; --", "1' OR '1'='1", "admin'--"],
        'xss': ["<script>alert('xss')</script>", "javascript:alert('xss')", "<img src=x onerror=alert('xss')>"],
        'path_traversal': ["../../../etc/passwd", "..\\..\\..\\windows\\system32\\config\\sam", "....//....//....//etc/passwd"],
        'command_injection': ["; rm -rf /", "| cat /etc/passwd", "&& format c:", "`rm -rf /`"],
        'buffer_overflow': ["A" * 10000, "B" * 100000, "\x00" * 1000],
        'format_strings': ["%s%s%s%s", "%x%x%x%x", "%n%n%n%n"],
        'null_bytes': ["test\x00.pdf", "file\x00\x00.txt", "\x00malicious"],
        'unicode_attacks': ["\u202e.pdf", "\ufeff.pdf", "\u200b.pdf"]
    }


@pytest.fixture(scope="function")
def create_encrypted_pdf(security_temp_dir):
    """Factory function to create encrypted PDF files."""
    def _create_encrypted_pdf(filename: str, user_password: str = None, owner_password: str = None, permissions: int = None):
        """Create an encrypted PDF file for testing."""
        pdf_path = security_temp_dir / filename
        
        # Create a simple PDF content (in real implementation, would use PyMuPDF)
        # For now, create a placeholder file
        with open(pdf_path, 'wb') as f:
            # Write minimal PDF structure
            f.write(b'%PDF-1.4\n')
            f.write(b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
            f.write(b'2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n')
            f.write(b'3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n')
            f.write(b'xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n')
            f.write(b'trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n178\n%%EOF\n')
        
        return pdf_path
    
    return _create_encrypted_pdf


@pytest.fixture(scope="function")
def create_malicious_pdf(security_temp_dir):
    """Factory function to create malicious PDF files for testing."""
    def _create_malicious_pdf(filename: str, attack_type: str = "oversized"):
        """Create a malicious PDF file for testing."""
        pdf_path = security_temp_dir / filename
        
        if attack_type == "oversized":
            # Create an oversized PDF
            with open(pdf_path, 'wb') as f:
                f.write(b'%PDF-1.4\n')
                # Write large amount of data
                f.write(b'A' * (10 * 1024 * 1024))  # 10MB of 'A's
                f.write(b'\n%%EOF\n')
        
        elif attack_type == "malformed":
            # Create a malformed PDF
            with open(pdf_path, 'wb') as f:
                f.write(b'%PDF-1.4\n')
                f.write(b'MALFORMED CONTENT WITHOUT PROPER STRUCTURE\n')
                f.write(b'%%EOF\n')
        
        elif attack_type == "javascript":
            # Create PDF with JavaScript (potential security risk)
            with open(pdf_path, 'wb') as f:
                f.write(b'%PDF-1.4\n')
                f.write(b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R /OpenAction << /S /JavaScript /JS (app.alert("XSS")) >> >>\nendobj\n')
                f.write(b'%%EOF\n')
        
        elif attack_type == "zip_bomb":
            # Create a PDF that could be a zip bomb
            with open(pdf_path, 'wb') as f:
                f.write(b'%PDF-1.4\n')
                # Simulate compressed content that expands significantly
                f.write(b'stream\n')
                f.write(b'\x00' * 1000)  # Null bytes that could compress well
                f.write(b'\nendstream\n')
                f.write(b'%%EOF\n')
        
        return pdf_path
    
    return _create_malicious_pdf


@pytest.fixture(scope="function")
def large_file_generator(security_temp_dir):
    """Factory function to generate large files for stress testing."""
    def _generate_large_file(size_mb: int, filename: str = "large_test.pdf"):
        """Generate a large file of specified size."""
        file_path = security_temp_dir / filename
        
        with open(file_path, 'wb') as f:
            # Write PDF header
            f.write(b'%PDF-1.4\n')
            
            # Calculate remaining size
            remaining_size = (size_mb * 1024 * 1024) - len(b'%PDF-1.4\n%%EOF\n')
            
            # Write content in chunks
            chunk_size = 1024 * 1024  # 1MB chunks
            written = 0
            
            while written < remaining_size:
                chunk_data = b'A' * min(chunk_size, remaining_size - written)
                f.write(chunk_data)
                written += len(chunk_data)
            
            # Write PDF footer
            f.write(b'\n%%EOF\n')
        
        return file_path
    
    return _generate_large_file


@pytest.fixture(scope="function")
def permission_test_cases():
    """Provide various permission test cases."""
    return {
        'no_permissions': 0,
        'print_only': 4,  # Print permission
        'copy_only': 16,  # Copy permission
        'modify_only': 8,  # Modify permission
        'all_permissions': 28,  # Print + Copy + Modify
        'custom_permissions': 20  # Print + Copy
    }


@pytest.fixture(scope="function")
def security_logger():
    """Create a logger for security tests."""
    return logging.getLogger("security_tests")