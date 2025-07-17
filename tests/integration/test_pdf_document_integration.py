"""
Integration tests for PDF document functionality with real PDF files.
"""

import os
import tempfile
import pytest
from datetime import datetime

from smart_pdf_toolkit.core.pdf_document import (
    PDFDocumentValidator,
    PDFDocumentFactory,
    validate_pdf_files
)
from smart_pdf_toolkit.core.interfaces import PDFDocument
from smart_pdf_toolkit.core.exceptions import ValidationError


def create_minimal_pdf(file_path: str):
    """Create a minimal valid PDF file for testing."""
    # This creates a very basic PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj

xref
0 4
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000100 00000 n 
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
157
%%EOF"""
    
    with open(file_path, 'wb') as f:
        f.write(pdf_content)


class TestPDFDocumentIntegration:
    """Integration tests with real PDF files."""
    
    def test_validate_real_pdf_file(self):
        """Test validation with a real PDF file."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            create_minimal_pdf(temp_file.name)
            
            try:
                result = PDFDocumentValidator.validate_pdf_file(temp_file.name)
                assert result is True
            finally:
                try:
                    os.unlink(temp_file.name)
                except (OSError, PermissionError):
                    pass
    
    def test_check_real_pdf_integrity(self):
        """Test integrity check with a real PDF file."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            create_minimal_pdf(temp_file.name)
            
            try:
                result = PDFDocumentValidator.check_pdf_integrity(temp_file.name)
                
                assert result['is_valid'] is True
                assert result['is_encrypted'] == False
                assert result['page_count'] >= 0
                assert isinstance(result['warnings'], list)
                assert isinstance(result['errors'], list)
            finally:
                try:
                    os.unlink(temp_file.name)
                except (OSError, PermissionError):
                    pass
    
    def test_extract_real_pdf_metadata(self):
        """Test metadata extraction from a real PDF file."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            create_minimal_pdf(temp_file.name)
            
            try:
                result = PDFDocumentValidator.extract_metadata(temp_file.name)
                
                assert isinstance(result, dict)
                assert 'page_count' in result
                assert 'file_size' in result
                assert 'is_encrypted' in result
                assert 'permissions' in result
                assert result['file_size'] > 0
            finally:
                try:
                    os.unlink(temp_file.name)
                except (OSError, PermissionError):
                    pass
    
    def test_create_pdf_document_from_real_file(self):
        """Test creating PDFDocument from a real PDF file."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            create_minimal_pdf(temp_file.name)
            
            try:
                pdf_doc = PDFDocumentFactory.create_from_file(temp_file.name)
                
                assert isinstance(pdf_doc, PDFDocument)
                assert pdf_doc.path == str(temp_file.name)
                assert pdf_doc.page_count >= 0
                assert pdf_doc.file_size > 0
                assert isinstance(pdf_doc.creation_date, datetime)
                assert isinstance(pdf_doc.modification_date, datetime)
                assert isinstance(pdf_doc.permissions, dict)
            finally:
                try:
                    os.unlink(temp_file.name)
                except (OSError, PermissionError):
                    pass
    
    def test_validate_multiple_real_pdf_files(self):
        """Test validating multiple real PDF files."""
        temp_files = []
        
        try:
            # Create multiple test PDF files
            for i in range(3):
                temp_file = tempfile.NamedTemporaryFile(suffix=f'_test_{i}.pdf', delete=False)
                create_minimal_pdf(temp_file.name)
                temp_files.append(temp_file.name)
                temp_file.close()
            
            # Add one invalid file
            invalid_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
            invalid_file.write(b"Not a PDF")
            invalid_file.close()
            temp_files.append(invalid_file.name)
            
            result = validate_pdf_files(temp_files)
            
            assert len(result['valid_files']) == 3
            assert len(result['invalid_files']) == 1
            assert len(result['errors']) == 1
            
        finally:
            # Clean up all temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except (OSError, PermissionError):
                    pass


if __name__ == "__main__":
    pytest.main([__file__])