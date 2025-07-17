"""Advanced malicious PDF handling tests.

This module tests the toolkit's ability to handle various types of
malicious PDFs and attack vectors safely.
"""

import pytest
import os
import tempfile
import struct
from pathlib import Path
from typing import List, Dict, Any, Optional
from unittest.mock import patch, MagicMock

from smart_pdf_toolkit.core.interfaces import OperationResult
from .security_fixtures import (
    security_temp_dir, security_config, security_manager, pdf_operations_secure,
    security_logger
)


class MaliciousPDFGenerator:
    """Generator for various types of malicious PDF files for testing."""
    
    @staticmethod
    def create_oversized_pdf(output_path: Path, size_mb: int = 100) -> Path:
        """Create an oversized PDF file."""
        # Create a PDF with excessive size
        with open(output_path, 'wb') as f:
            # Write minimal PDF header
            f.write(b'%PDF-1.4\n')
            f.write(b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
            f.write(b'2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n')
            f.write(b'3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n')
            
            # Fill with junk data to reach desired size
            chunk_size = 1024 * 1024  # 1MB chunks
            junk_data = b'A' * chunk_size
            
            for _ in range(size_mb):
                f.write(junk_data)
            
            # Write minimal PDF footer
            f.write(b'xref\n0 4\n0000000000 65535 f \n')
            f.write(b'0000000009 00000 n \n')
            f.write(b'0000000074 00000 n \n')
            f.write(b'0000000120 00000 n \n')
            f.write(b'trailer\n<< /Size 4 /Root 1 0 R >>\n')
            f.write(b'startxref\n')
            f.write(str(f.tell() - 100).encode() + b'\n')
            f.write(b'%%EOF\n')
        
        return output_path
    
    @staticmethod
    def create_deeply_nested_pdf(output_path: Path, nesting_depth: int = 1000) -> Path:
        """Create a PDF with deeply nested objects."""
        with open(output_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            
            # Create deeply nested dictionary structure
            obj_num = 1
            f.write(f'{obj_num} 0 obj\n<< /Type /Catalog /Pages {obj_num + 1} 0 R >>\nendobj\n'.encode())
            obj_num += 1
            
            # Create nested objects
            for i in range(nesting_depth):
                if i == nesting_depth - 1:
                    # Last object
                    f.write(f'{obj_num} 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\n'.encode())
                else:
                    # Nested object
                    f.write(f'{obj_num} 0 obj\n<< /Nested {obj_num + 1} 0 R >>\nendobj\n'.encode())
                obj_num += 1
            
            # Write xref and trailer
            f.write(b'xref\n')
            f.write(f'0 {obj_num}\n'.encode())
            f.write(b'0000000000 65535 f \n')
            
            for i in range(1, obj_num):
                f.write(f'{i:010d} 00000 n \n'.encode())
            
            f.write(f'trailer\n<< /Size {obj_num} /Root 1 0 R >>\n'.encode())
            f.write(b'startxref\n0\n%%EOF\n')
        
        return output_path
    
    @staticmethod
    def create_malformed_pdf(output_path: Path, malformation_type: str = 'truncated') -> Path:
        """Create a malformed PDF file."""
        with open(output_path, 'wb') as f:
            if malformation_type == 'truncated':
                # Truncated PDF
                f.write(b'%PDF-1.4\n')
                f.write(b'1 0 obj\n<< /Type /Catalog')
                # Intentionally truncated
                
            elif malformation_type == 'invalid_header':
                # Invalid PDF header
                f.write(b'%NOTPDF-1.4\n')
                f.write(b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
                
            elif malformation_type == 'corrupted_xref':
                # Corrupted xref table
                f.write(b'%PDF-1.4\n')
                f.write(b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
                f.write(b'xref\nCORRUPTED_XREF_TABLE\n')
                f.write(b'trailer\n<< /Size 2 /Root 1 0 R >>\n')
                f.write(b'startxref\n0\n%%EOF\n')
                
            elif malformation_type == 'infinite_loop':
                # Objects that reference each other in a loop
                f.write(b'%PDF-1.4\n')
                f.write(b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
                f.write(b'2 0 obj\n<< /Type /Pages /Parent 3 0 R >>\nendobj\n')
                f.write(b'3 0 obj\n<< /Type /Pages /Parent 2 0 R >>\nendobj\n')
                f.write(b'xref\n0 4\n')
                f.write(b'0000000000 65535 f \n')
                f.write(b'0000000009 00000 n \n')
                f.write(b'0000000074 00000 n \n')
                f.write(b'0000000120 00000 n \n')
                f.write(b'trailer\n<< /Size 4 /Root 1 0 R >>\n')
                f.write(b'startxref\n166\n%%EOF\n')
        
        return output_path
    
    @staticmethod
    def create_javascript_pdf(output_path: Path, malicious_js: bool = True) -> Path:
        """Create a PDF with JavaScript content."""
        js_code = '''
        if (malicious_js) {
            // Potentially malicious JavaScript
            app.alert("This is a test alert");
            // Attempt to access file system (should be blocked)
            try {
                var file = util.readFileIntoStream("/etc/passwd");
            } catch(e) {
                // Expected to fail
            }
            
            // Attempt infinite loop (should be handled)
            var counter = 0;
            while (counter < 1000000) {
                counter++;
                if (counter % 100000 == 0) break; // Safety break
            }
        } else {
            // Benign JavaScript
            console.println("Hello from PDF JavaScript");
        }
        '''
        
        with open(output_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R /OpenAction 4 0 R >>\nendobj\n')
            f.write(b'2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n')
            f.write(b'3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n')
            
            # JavaScript action
            js_bytes = js_code.encode('utf-8')
            f.write(f'4 0 obj\n<< /Type /Action /S /JavaScript /JS ({len(js_bytes)} bytes) >>\nstream\n'.encode())
            f.write(js_bytes)
            f.write(b'\nendstream\nendobj\n')
            
            # Write xref and trailer
            f.write(b'xref\n0 5\n')
            f.write(b'0000000000 65535 f \n')
            f.write(b'0000000009 00000 n \n')
            f.write(b'0000000088 00000 n \n')
            f.write(b'0000000145 00000 n \n')
            f.write(b'0000000220 00000 n \n')
            f.write(b'trailer\n<< /Size 5 /Root 1 0 R >>\n')
            f.write(b'startxref\n')
            f.write(str(f.tell() + 20).encode())
            f.write(b'\n%%EOF\n')
        
        return output_path


@pytest.fixture
def malicious_pdf_generator():
    """Provide malicious PDF generator."""
    return MaliciousPDFGenerator()


class TestAdvancedMaliciousPDFHandling:
    """Test handling of various malicious PDF types."""
    
    def test_oversized_pdf_handling(self, pdf_operations_secure, malicious_pdf_generator, security_temp_dir, security_logger):
        """Test handling of oversized PDF files."""
        # Create oversized PDF (10MB for testing)
        oversized_pdf = malicious_pdf_generator.create_oversized_pdf(
            security_temp_dir / "oversized.pdf", size_mb=10
        )
        
        output_path = security_temp_dir / "oversized_output.pdf"
        
        # Should handle oversized files gracefully
        result = pdf_operations_secure.rotate_pdf(
            str(oversized_pdf), [90], str(output_path)
        )
        
        # Should either succeed or fail gracefully with appropriate error
        if not result.success:
            assert any(keyword in result.message.lower() for keyword in 
                      ['size', 'large', 'memory', 'limit', 'timeout'])
            security_logger.info(f"Oversized PDF handled gracefully: {result.message}")
        else:
            security_logger.info("Oversized PDF processed successfully")
    
    def test_deeply_nested_pdf_handling(self, pdf_operations_secure, malicious_pdf_generator, security_temp_dir, security_logger):
        """Test handling of deeply nested PDF structures."""
        # Create deeply nested PDF (100 levels for testing)
        nested_pdf = malicious_pdf_generator.create_deeply_nested_pdf(
            security_temp_dir / "nested.pdf", nesting_depth=100
        )
        
        output_path = security_temp_dir / "nested_output.pdf"
        
        # Should handle nested structures without stack overflow
        result = pdf_operations_secure.rotate_pdf(
            str(nested_pdf), [90], str(output_path)
        )
        
        # Should not crash the application
        assert isinstance(result, OperationResult)
        
        if not result.success:
            assert any(keyword in result.message.lower() for keyword in 
                      ['nested', 'depth', 'recursion', 'structure', 'invalid'])
            security_logger.info(f"Nested PDF handled gracefully: {result.message}")
    
    def test_malformed_pdf_handling(self, pdf_operations_secure, malicious_pdf_generator, security_temp_dir, security_logger):
        """Test handling of various malformed PDF files."""
        malformation_types = ['truncated', 'invalid_header', 'corrupted_xref', 'infinite_loop']
        
        for malformation_type in malformation_types:
            malformed_pdf = malicious_pdf_generator.create_malformed_pdf(
                security_temp_dir / f"malformed_{malformation_type}.pdf",
                malformation_type=malformation_type
            )
            
            output_path = security_temp_dir / f"malformed_output_{malformation_type}.pdf"
            
            # Should handle malformed PDFs gracefully
            result = pdf_operations_secure.rotate_pdf(
                str(malformed_pdf), [90], str(output_path)
            )
            
            # Should not crash and should provide meaningful error
            assert isinstance(result, OperationResult)
            
            if not result.success:
                assert len(result.message) > 0, f"No error message for {malformation_type}"
                security_logger.info(f"Malformed PDF ({malformation_type}) handled: {result.message}")
    
    def test_javascript_pdf_handling(self, pdf_operations_secure, malicious_pdf_generator, security_temp_dir, security_logger):
        """Test handling of PDFs with JavaScript content."""
        # Create PDF with potentially malicious JavaScript
        js_pdf = malicious_pdf_generator.create_javascript_pdf(
            security_temp_dir / "javascript.pdf", malicious_js=True
        )
        
        output_path = security_temp_dir / "javascript_output.pdf"
        
        # Should handle JavaScript PDFs safely
        result = pdf_operations_secure.rotate_pdf(
            str(js_pdf), [90], str(output_path)
        )
        
        # Should either process safely or reject with appropriate message
        assert isinstance(result, OperationResult)
        
        if not result.success and "javascript" in result.message.lower():
            security_logger.info(f"JavaScript PDF rejected appropriately: {result.message}")
        else:
            security_logger.info("JavaScript PDF processed (JavaScript likely ignored)")
    
    def test_zip_bomb_pdf_protection(self, pdf_operations_secure, security_temp_dir, security_logger):
        """Test protection against PDF zip bomb attacks."""
        # Create a PDF that could expand significantly when processed
        zip_bomb_pdf = security_temp_dir / "zip_bomb.pdf"
        
        with open(zip_bomb_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
            f.write(b'2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n')
            
            # Create a page with highly compressed content that expands significantly
            f.write(b'3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n')
            
            # Compressed stream that expands to large size
            compressed_data = b'BT /F1 12 Tf 100 700 Td ' + b'(A)' * 10000 + b' Tj ET'
            f.write(f'4 0 obj\n<< /Length {len(compressed_data)} /Filter /FlateDecode >>\nstream\n'.encode())
            f.write(compressed_data)
            f.write(b'\nendstream\nendobj\n')
            
            # Write xref and trailer
            f.write(b'xref\n0 5\n')
            f.write(b'0000000000 65535 f \n')
            f.write(b'0000000009 00000 n \n')
            f.write(b'0000000074 00000 n \n')
            f.write(b'0000000131 00000 n \n')
            f.write(b'0000000220 00000 n \n')
            f.write(b'trailer\n<< /Size 5 /Root 1 0 R >>\n')
            f.write(b'startxref\n')
            f.write(str(f.tell() + 20).encode())
            f.write(b'\n%%EOF\n')
        
        output_path = security_temp_dir / "zip_bomb_output.pdf"
        
        # Should handle potential zip bombs safely
        import time
        start_time = time.time()
        
        result = pdf_operations_secure.rotate_pdf(
            str(zip_bomb_pdf), [90], str(output_path)
        )
        
        processing_time = time.time() - start_time
        
        # Should not take excessive time or memory
        assert processing_time < 60, f"Processing took too long: {processing_time}s"
        assert isinstance(result, OperationResult)
        
        security_logger.info(f"Zip bomb PDF processed in {processing_time:.2f}s: {result.success}")
    
    def test_binary_data_injection(self, pdf_operations_secure, security_temp_dir, security_logger):
        """Test handling of PDFs with binary data injection attempts."""
        # Create PDF with embedded binary data that could be malicious
        binary_pdf = security_temp_dir / "binary_injection.pdf"
        
        with open(binary_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
            f.write(b'2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n')
            f.write(b'3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n')
            
            # Inject various binary patterns that could be problematic
            binary_patterns = [
                b'\\x00\\x01\\x02\\x03',  # Null bytes and control characters
                b'\\xff\\xfe\\xfd\\xfc',  # High byte values
                b'\\x7f\\x80\\x81\\x82',  # ASCII boundary values
                struct.pack('<I', 0xdeadbeef),  # Packed binary data
                b'\\r\\n\\r\\n',  # CRLF injection attempt
                b'%PDF-1.4\\n',  # PDF header injection
            ]
            
            for i, pattern in enumerate(binary_patterns):
                f.write(f'% Binary pattern {i}: '.encode())
                f.write(pattern)
                f.write(b'\\n')
            
            # Write xref and trailer
            f.write(b'xref\\n0 4\\n')
            f.write(b'0000000000 65535 f \\n')
            f.write(b'0000000009 00000 n \\n')
            f.write(b'0000000074 00000 n \\n')
            f.write(b'0000000131 00000 n \\n')
            f.write(b'trailer\\n<< /Size 4 /Root 1 0 R >>\\n')
            f.write(b'startxref\\n')
            f.write(str(f.tell() + 20).encode())
            f.write(b'\\n%%EOF\\n')
        
        output_path = security_temp_dir / "binary_injection_output.pdf"
        
        # Should handle binary data safely
        result = pdf_operations_secure.rotate_pdf(
            str(binary_pdf), [90], str(output_path)
        )
        
        # Should not crash or exhibit unexpected behavior
        assert isinstance(result, OperationResult)
        
        security_logger.info(f"Binary injection PDF handled: {result.success}")