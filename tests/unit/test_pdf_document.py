"""
Unit tests for PDF document model and validation.
"""

import os
import tempfile
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from smart_pdf_toolkit.core.pdf_document import (
    PDFDocumentValidator,
    PDFDocumentFactory,
    validate_pdf_files
)
from smart_pdf_toolkit.core.interfaces import PDFDocument
from smart_pdf_toolkit.core.exceptions import (
    ValidationError,
    PDFProcessingError
)


class TestPDFDocumentValidator:
    """Test cases for PDFDocumentValidator."""
    
    def test_validate_pdf_file_empty_path(self):
        """Test validation with empty file path."""
        with pytest.raises(ValidationError, match="File path cannot be empty"):
            PDFDocumentValidator.validate_pdf_file("")
    
    def test_validate_pdf_file_nonexistent(self):
        """Test validation with non-existent file."""
        with pytest.raises(ValidationError, match="File does not exist"):
            PDFDocumentValidator.validate_pdf_file("nonexistent.pdf")
    
    def test_validate_pdf_file_directory(self):
        """Test validation with directory path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValidationError, match="Path is not a file"):
                PDFDocumentValidator.validate_pdf_file(temp_dir)
    
    def test_validate_pdf_file_wrong_extension(self):
        """Test validation with non-PDF file."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"Not a PDF")
            temp_file.close()  # Close file before validation
            
            try:
                with pytest.raises(ValidationError, match="File is not a PDF"):
                    PDFDocumentValidator.validate_pdf_file(temp_file.name)
            finally:
                try:
                    os.unlink(temp_file.name)
                except (OSError, PermissionError):
                    pass  # Ignore cleanup errors on Windows
    
    @patch('smart_pdf_toolkit.core.pdf_document.fitz.open')
    def test_validate_pdf_file_invalid_pdf(self, mock_fitz_open):
        """Test validation with invalid PDF content."""
        # Create a temporary file with PDF extension but invalid content
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"Not a real PDF")
            temp_file.close()  # Close file before validation
            
            # Mock fitz to raise an exception
            mock_fitz_open.side_effect = Exception("Invalid PDF")
            
            try:
                with pytest.raises(ValidationError, match="Failed to validate PDF file"):
                    PDFDocumentValidator.validate_pdf_file(temp_file.name)
            finally:
                try:
                    os.unlink(temp_file.name)
                except (OSError, PermissionError):
                    pass  # Ignore cleanup errors on Windows
    
    @patch('smart_pdf_toolkit.core.pdf_document.fitz.open')
    def test_validate_pdf_file_valid(self, mock_fitz_open):
        """Test validation with valid PDF file."""
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"%PDF-1.4")  # Minimal PDF header
            temp_file.close()  # Close file before validation
            
            # Mock fitz document
            mock_doc = MagicMock()
            mock_doc.is_pdf = True
            mock_fitz_open.return_value = mock_doc
            
            try:
                result = PDFDocumentValidator.validate_pdf_file(temp_file.name)
                assert result is True
                mock_doc.close.assert_called_once()
            finally:
                try:
                    os.unlink(temp_file.name)
                except (OSError, PermissionError):
                    pass  # Ignore cleanup errors on Windows
    
    @patch('smart_pdf_toolkit.core.pdf_document.fitz.open')
    def test_check_pdf_integrity_valid(self, mock_fitz_open):
        """Test PDF integrity check with valid file."""
        mock_doc = MagicMock()
        mock_doc.needs_pass = False
        mock_doc.page_count = 3
        mock_doc.xref_length.return_value = 10
        
        # Mock pages
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Sample text"
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc
        
        result = PDFDocumentValidator.check_pdf_integrity("test.pdf")
        
        assert result['is_valid'] is True
        assert result['is_encrypted'] is False
        assert result['is_damaged'] is False
        assert result['page_count'] == 3
        assert result['has_xref_errors'] is False
        assert len(result['errors']) == 0
    
    @patch('smart_pdf_toolkit.core.pdf_document.fitz.open')
    def test_check_pdf_integrity_encrypted(self, mock_fitz_open):
        """Test PDF integrity check with encrypted file."""
        mock_doc = MagicMock()
        mock_doc.needs_pass = True
        mock_doc.page_count = 2
        mock_doc.xref_length.return_value = 5
        mock_fitz_open.return_value = mock_doc
        
        result = PDFDocumentValidator.check_pdf_integrity("encrypted.pdf")
        
        assert result['is_encrypted'] is True
    
    @patch('smart_pdf_toolkit.core.pdf_document.fitz.open')
    def test_check_pdf_integrity_damaged(self, mock_fitz_open):
        """Test PDF integrity check with damaged file."""
        mock_doc = MagicMock()
        mock_doc.needs_pass = False
        mock_doc.page_count = 2
        mock_doc.xref_length.return_value = 5
        
        # Mock damaged page
        mock_page = MagicMock()
        mock_page.get_text.side_effect = Exception("Page damaged")
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc
        
        result = PDFDocumentValidator.check_pdf_integrity("damaged.pdf")
        
        assert result['is_damaged'] is True
        assert len(result['errors']) > 0
        assert "Damaged page detected" in result['errors'][0]
    
    @patch('smart_pdf_toolkit.core.pdf_document.os.stat')
    @patch('smart_pdf_toolkit.core.pdf_document.fitz.open')
    def test_extract_metadata(self, mock_fitz_open, mock_stat):
        """Test metadata extraction from PDF."""
        # Mock file stats
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 1024
        mock_stat.return_value = mock_stat_result
        
        # Mock PDF document
        mock_doc = MagicMock()
        mock_doc.metadata = {
            'title': 'Test Document',
            'author': 'Test Author',
            'subject': 'Test Subject',
            'creator': 'Test Creator',
            'producer': 'Test Producer',
            'creationDate': 'D:20240101120000',
            'modDate': 'D:20240102130000',
            'keywords': 'test, pdf'
        }
        mock_doc.page_count = 5
        mock_doc.needs_pass = False
        mock_fitz_open.return_value = mock_doc
        
        result = PDFDocumentValidator.extract_metadata("test.pdf")
        
        assert result['title'] == 'Test Document'
        assert result['author'] == 'Test Author'
        assert result['file_size'] == 1024
        assert result['page_count'] == 5
        assert result['is_encrypted'] is False
        assert isinstance(result['permissions'], dict)
    
    @patch('smart_pdf_toolkit.core.pdf_document.fitz.open')
    def test_extract_metadata_error(self, mock_fitz_open):
        """Test metadata extraction error handling."""
        mock_fitz_open.side_effect = Exception("Cannot open file")
        
        with pytest.raises(PDFProcessingError, match="Failed to extract metadata"):
            PDFDocumentValidator.extract_metadata("error.pdf")


class TestPDFDocumentFactory:
    """Test cases for PDFDocumentFactory."""
    
    @patch('smart_pdf_toolkit.core.pdf_document.PDFDocumentValidator.validate_pdf_file')
    @patch('smart_pdf_toolkit.core.pdf_document.PDFDocumentValidator.extract_metadata')
    def test_create_from_file(self, mock_extract_metadata, mock_validate):
        """Test creating PDFDocument from file."""
        # Mock validation
        mock_validate.return_value = True
        
        # Mock metadata
        mock_extract_metadata.return_value = {
            'title': 'Test PDF',
            'author': 'Test Author',
            'page_count': 10,
            'file_size': 2048,
            'creation_date': 'D:20240101120000',
            'modification_date': 'D:20240102130000',
            'is_encrypted': False,
            'permissions': {'print': True, 'copy': True}
        }
        
        result = PDFDocumentFactory.create_from_file("test.pdf")
        
        assert isinstance(result, PDFDocument)
        assert result.title == 'Test PDF'
        assert result.author == 'Test Author'
        assert result.page_count == 10
        assert result.file_size == 2048
        assert result.is_encrypted is False
        assert isinstance(result.creation_date, datetime)
        assert isinstance(result.modification_date, datetime)
    
    def test_parse_pdf_date_full(self):
        """Test parsing full PDF date string."""
        date_string = "D:20240315143022"
        result = PDFDocumentFactory._parse_pdf_date(date_string)
        
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 15
        assert result.hour == 14
        assert result.minute == 30
        assert result.second == 22
    
    def test_parse_pdf_date_date_only(self):
        """Test parsing date-only PDF string."""
        date_string = "20240315"
        result = PDFDocumentFactory._parse_pdf_date(date_string)
        
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 15
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
    
    def test_parse_pdf_date_empty(self):
        """Test parsing empty date string."""
        result = PDFDocumentFactory._parse_pdf_date("")
        
        # Should return current datetime
        assert isinstance(result, datetime)
    
    def test_parse_pdf_date_invalid(self):
        """Test parsing invalid date string."""
        result = PDFDocumentFactory._parse_pdf_date("invalid_date")
        
        # Should return current datetime
        assert isinstance(result, datetime)


class TestValidatePDFFiles:
    """Test cases for validate_pdf_files function."""
    
    @patch('smart_pdf_toolkit.core.pdf_document.PDFDocumentValidator.validate_pdf_file')
    def test_validate_multiple_files_all_valid(self, mock_validate):
        """Test validating multiple valid PDF files."""
        mock_validate.return_value = True
        
        file_paths = ["file1.pdf", "file2.pdf", "file3.pdf"]
        result = validate_pdf_files(file_paths)
        
        assert len(result['valid_files']) == 3
        assert len(result['invalid_files']) == 0
        assert len(result['errors']) == 0
    
    @patch('smart_pdf_toolkit.core.pdf_document.PDFDocumentValidator.validate_pdf_file')
    def test_validate_multiple_files_mixed(self, mock_validate):
        """Test validating mix of valid and invalid PDF files."""
        def side_effect(file_path):
            if file_path == "invalid.pdf":
                raise ValidationError("Invalid PDF")
            return True
        
        mock_validate.side_effect = side_effect
        
        file_paths = ["valid1.pdf", "invalid.pdf", "valid2.pdf"]
        result = validate_pdf_files(file_paths)
        
        assert len(result['valid_files']) == 2
        assert len(result['invalid_files']) == 1
        assert "invalid.pdf" in result['errors']
        assert "Invalid PDF" in result['errors']["invalid.pdf"]
    
    @patch('smart_pdf_toolkit.core.pdf_document.PDFDocumentValidator.validate_pdf_file')
    def test_validate_multiple_files_unexpected_error(self, mock_validate):
        """Test handling unexpected errors during validation."""
        def side_effect(file_path):
            if file_path == "error.pdf":
                raise Exception("Unexpected error")
            return True
        
        mock_validate.side_effect = side_effect
        
        file_paths = ["valid.pdf", "error.pdf"]
        result = validate_pdf_files(file_paths)
        
        assert len(result['valid_files']) == 1
        assert len(result['invalid_files']) == 1
        assert "error.pdf" in result['errors']
        assert "Unexpected error" in result['errors']["error.pdf"]


if __name__ == "__main__":
    pytest.main([__file__])