"""Security test fixtures for Smart PDF Toolkit.

This module provides fixtures for security testing including
malicious PDFs, encrypted files, and security test utilities.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
import logging
from typing import List, Dict, Any

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
    """Create a security test configuration."""
    config = Config()
    config.output_dir = security_temp_dir
    config.temp_dir = security_temp_dir / "temp"
    config.max_file_size = 100 * 1024 * 1024  # 100MB for security tests
    config.allowed_extensions = ['.pdf', '.txt', '.png', '.jpg', '.jpeg']
    return config


@pytest.fixture(scope="function")
def security_manager(security_config):
    """Create a SecurityManager instance for testing."""
    return SecurityManager(security_config)


@pytest.fixture(scope="function")
def pdf_operations(security_config):
    """Create a PDFOperationsManager instance for security testing."""
    return PDFOperationsManager(security_config)


@pytest.fixture(scope="function")
def password_protected_pdf(security_temp_dir, security_manager):
    """Create a password-protected PDF for testing."""
    # Create a simple PDF first
    simple_pdf = security_temp_dir / "simple.pdf"
    simple_pdf.touch()  # Placeholder - in real implementation would create actual PDF
    
    # Create password-protected version
    protected_pdf = security_temp_dir / "protected.pdf"
    
    # In a real implementation, this would actually create a password-protected PDF
    # For now, we'll just create a file and track the password
    protected_pdf.touch()
    
    return {
        'path': protected_pdf,
        'password': 'test_password_123',
        'owner_password': 'owner_password_456'
    }


@pytest.fixture(scope="function")
def malicious_pdf_samples(security_temp_dir):
    """Create sample malicious PDF files for testing."""
    samples = {}
    
    # Oversized PDF (simulated)
    oversized_pdf = security_temp_dir / "oversized.pdf"
    with open(oversized_pdf, 'wb') as f:
        # Write a large amount of data to simulate oversized file
        f.write(b'%PDF-1.4\n' + b'A' * (200 * 1024 * 1024))  # 200MB of 'A's
    samples['oversized'] = oversized_pdf
    
    # Malformed PDF header
    malformed_pdf = security_temp_dir / "malformed.pdf"
    with open(malformed_pdf, 'wb') as f:
        f.write(b'INVALID_PDF_HEADER\n')
    samples['malformed'] = malformed_pdf
    
    # Empty file with PDF extension
    empty_pdf = security_temp_dir / "empty.pdf"
    empty_pdf.touch()
    samples['empty'] = empty_pdf
    
    # Binary file with PDF extension
    binary_pdf = security_temp_dir / "binary.pdf"
    with open(binary_pdf, 'wb') as f:
        f.write(os.urandom(1024))  # Random binary data
    samples['binary'] = binary_pdf
    
    # PDF with suspicious JavaScript (simulated)
    js_pdf = security_temp_dir / "javascript.pdf"
    with open(js_pdf, 'wb') as f:
        f.write(b'%PDF-1.4\n/JS (app.alert("XSS attempt");)\n')
    samples['javascript'] = js_pdf
    
    return samples


@pytest.fixture(scope="function")
def large_pdf_files(security_temp_dir):
    """Create large PDF files for stress testing."""
    files = []
    
    # Create files of different sizes
    sizes = [
        (1, "1MB"),
        (10, "10MB"),
        (50, "50MB"),
        (100, "100MB")
    ]
    
    for size_mb, name in sizes:
        file_path = security_temp_dir / f"large_{name}.pdf"
        with open(file_path, 'wb') as f:
            # Write PDF header and then fill with data
            f.write(b'%PDF-1.4\n')
            # Fill with repeated pattern to simulate large PDF
            pattern = b'Large PDF content pattern. ' * 1000
            bytes_written = len(b'%PDF-1.4\n')
            target_bytes = size_mb * 1024 * 1024
            
            while bytes_written < target_bytes:
                chunk_size = min(len(pattern), target_bytes - bytes_written)
                f.write(pattern[:chunk_size])
                bytes_written += chunk_size
        
        files.append({
            'path': file_path,
            'size_mb': size_mb,
            'name': name
        })
    
    return files


@pytest.fixture(scope="function")
def security_test_vectors():
    """Provide security test vectors for input validation."""
    return {
        'path_traversal': [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '/etc/shadow',
            'C:\\Windows\\System32\\config\\SAM',
            '....//....//....//etc/passwd',
            '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd'
        ],
        'command_injection': [
            '; rm -rf /',
            '| cat /etc/passwd',
            '&& del C:\\*.*',
            '`whoami`',
            '$(id)',
            '${IFS}cat${IFS}/etc/passwd'
        ],
        'sql_injection': [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM users--",
            "admin'--",
            "' OR 1=1#"
        ],
        'xss_payloads': [
            '<script>alert("XSS")</script>',
            'javascript:alert("XSS")',
            '<img src=x onerror=alert("XSS")>',
            '<svg onload=alert("XSS")>',
            '"><script>alert("XSS")</script>'
        ],
        'buffer_overflow': [
            'A' * 1000,
            'A' * 10000,
            'A' * 100000,
            '\x00' * 1000,
            '\xff' * 1000
        ],
        'null_bytes': [
            'test\x00.pdf',
            'file\x00\x00.pdf',
            '\x00test.pdf'
        ]
    }


@pytest.fixture(scope="function")
def performance_monitor():
    """Create a performance monitoring utility for stress tests."""
    import psutil
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.start_memory = None
            self.start_cpu = None
            self.process = psutil.Process()
        
        def start_monitoring(self):
            self.start_time = time.time()
            self.start_memory = self.process.memory_info().rss
            self.start_cpu = self.process.cpu_percent()
            return self
        
        def get_metrics(self):
            current_time = time.time()
            current_memory = self.process.memory_info().rss
            current_cpu = self.process.cpu_percent()
            
            return {
                'elapsed_time': current_time - self.start_time if self.start_time else 0,
                'memory_used': current_memory - self.start_memory if self.start_memory else 0,
                'memory_current': current_memory,
                'cpu_percent': current_cpu,
                'memory_mb': current_memory / (1024 * 1024)
            }
    
    return PerformanceMonitor()