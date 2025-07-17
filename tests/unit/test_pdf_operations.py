"""
Unit tests for PDF operations functionality.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from smart_pdf_toolkit.core.pdf_operations import PDFOperationsManager
from smart_pdf_toolkit.core.interfaces import OperationResult
from smart_pdf_toolkit.core.exceptions import (
    ValidationError,
    PDFProcessingError,
    FileOperationError
)


def create_mock_pdf_doc(page_count=3):
    """Create a mock PDF document for testing."""
    mock_doc = MagicMock()
    mock_doc.page_count = page_count
    mock_doc.close = MagicMock()
    mock_doc.save = MagicMock()
    mock_doc.insert_pdf = MagicMock()
    
    # Mock pages
    mock_pages = []
    for i in range(page_count):
        mock_page = MagicMock()
        mock_page.set_rotation = MagicMock()
        mock_pages.append(mock_page)
    
    mock_doc.__getitem__ = lambda self, index: mock_pages[index]
    
    return mock_doc


class TestPDFOperationsManager:
    """Test cases for PDFOperationsManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.operations_manager = PDFOperationsManager()
    
    def test_init(self):
        """Test PDFOperationsManager initialization."""
        assert self.operations_manager.supported_rotations == [0, 90, 180, 270]
    
    # Merge PDF Tests
    def test_merge_pdfs_empty_input_files(self):
        """Test merge with empty input files list."""
        with pytest.raises(ValidationError, match="No input files provided"):
            self.operations_manager.merge_pdfs([], "output.pdf")
    
    def test_merge_pdfs_single_file(self):
        """Test merge with only one input file."""
        with pytest.raises(ValidationError, match="At least 2 PDF files are required"):
            self.operations_manager.merge_pdfs(["file1.pdf"], "output.pdf")
    
    def test_merge_pdfs_no_output_file(self):
        """Test merge with no output file specified."""
        with pytest.raises(ValidationError, match="Output file path is required"):
            self.operations_manager.merge_pdfs(["file1.pdf", "file2.pdf"], "")
    
    @patch('smart_pdf_toolkit.core.pdf_operations.PDFDocumentValidator.validate_pdf_file')
    def test_merge_pdfs_invalid_input_file(self, mock_validate):
        """Test merge with invalid input file."""
        mock_validate.side_effect = [True, ValidationError("Invalid PDF")]
        
        with pytest.raises(ValidationError, match="Input validation failed"):
            self.operations_manager.merge_pdfs(["valid.pdf", "invalid.pdf"], "output.pdf")
    
    @patch('smart_pdf_toolkit.core.pdf_operations.os.path.exists')
    @patch('smart_pdf_toolkit.core.pdf_operations.fitz.open')
    @patch('smart_pdf_toolkit.core.pdf_operations.PDFDocumentValidator.validate_pdf_file')
    def test_merge_pdfs_success(self, mock_validate, mock_fitz_open, mock_exists):
        """Test successful PDF merge operation."""
        # Mock validation
        mock_validate.return_value = True
        
        # Mock file existence check
        mock_exists.return_value = True
        
        # Mock PDF documents
        mock_source1 = create_mock_pdf_doc(2)
        mock_source2 = create_mock_pdf_doc(3)
        mock_merged = create_mock_pdf_doc(0)
        
        def mock_open_side_effect(path=None):
            if path is None:  # New document
                return mock_merged
            elif "file1.pdf" in str(path):
                return mock_source1
            elif "file2.pdf" in str(path):
                return mock_source2
            return mock_merged
        
        mock_fitz_open.side_effect = mock_open_side_effect
        
        result = self.operations_manager.merge_pdfs(
            ["file1.pdf", "file2.pdf"], 
            "merged.pdf"
        )
        
        assert isinstance(result, OperationResult)
        assert result.success is True
        assert "Successfully merged 2 PDF files" in result.message
        assert result.output_files == ["merged.pdf"]
        assert result.execution_time >= 0
    
    # Split PDF Tests
    def test_split_pdf_no_input_file(self):
        """Test split with no input file."""
        with pytest.raises(ValidationError, match="Input file path is required"):
            self.operations_manager.split_pdf("", [(1, 2)])
    
    def test_split_pdf_no_page_ranges(self):
        """Test split with no page ranges."""
        with pytest.raises(ValidationError, match="Page ranges are required"):
            self.operations_manager.split_pdf("input.pdf", [])
    
    @patch('smart_pdf_toolkit.core.pdf_operations.PDFDocumentValidator.validate_pdf_file')
    def test_split_pdf_invalid_input_file(self, mock_validate):
        """Test split with invalid input file."""
        mock_validate.side_effect = ValidationError("Invalid PDF")
        
        with pytest.raises(ValidationError, match="Invalid PDF"):
            self.operations_manager.split_pdf("invalid.pdf", [(1, 2)])
    
    @patch('smart_pdf_toolkit.core.pdf_operations.fitz.open')
    @patch('smart_pdf_toolkit.core.pdf_operations.PDFDocumentValidator.validate_pdf_file')
    def test_split_pdf_invalid_page_ranges(self, mock_validate, mock_fitz_open):
        """Test split with invalid page ranges."""
        mock_validate.return_value = True
        mock_doc = create_mock_pdf_doc(5)
        mock_fitz_open.return_value = mock_doc
        
        # Test page number < 1
        with pytest.raises(ValidationError, match="Page numbers must be >= 1"):
            self.operations_manager.split_pdf("input.pdf", [(0, 2)])
        
        # Test page number > total pages
        with pytest.raises(ValidationError, match="exceeds document pages"):
            self.operations_manager.split_pdf("input.pdf", [(1, 10)])
        
        # Test start_page > end_page
        with pytest.raises(ValidationError, match="start_page > end_page"):
            self.operations_manager.split_pdf("input.pdf", [(3, 1)])
    
    @patch('smart_pdf_toolkit.core.pdf_operations.fitz.open')
    @patch('smart_pdf_toolkit.core.pdf_operations.PDFDocumentValidator.validate_pdf_file')
    def test_split_pdf_success(self, mock_validate, mock_fitz_open):
        """Test successful PDF split operation."""
        mock_validate.return_value = True
        
        # Mock source document
        mock_source = create_mock_pdf_doc(10)
        
        # Mock output documents
        mock_output1 = create_mock_pdf_doc(0)
        mock_output2 = create_mock_pdf_doc(0)
        
        def mock_open_side_effect(path=None):
            if path and "input.pdf" in str(path):
                return mock_source
            else:  # New document
                return mock_output1 if mock_fitz_open.call_count <= 2 else mock_output2
        
        mock_fitz_open.side_effect = mock_open_side_effect
        
        result = self.operations_manager.split_pdf(
            "input.pdf", 
            [(1, 3), (4, 6)]
        )
        
        assert isinstance(result, OperationResult)
        assert result.success is True
        assert "Successfully split PDF into 2 files" in result.message
        assert len(result.output_files) == 2
        assert result.execution_time >= 0
    
    # Rotate Pages Tests
    def test_rotate_pages_no_input_file(self):
        """Test rotate with no input file."""
        with pytest.raises(ValidationError, match="Input file path is required"):
            self.operations_manager.rotate_pages("", {1: 90})
    
    def test_rotate_pages_no_rotations(self):
        """Test rotate with no page rotations."""
        with pytest.raises(ValidationError, match="Page rotations dictionary is required"):
            self.operations_manager.rotate_pages("input.pdf", {})
    
    @patch('smart_pdf_toolkit.core.pdf_operations.fitz.open')
    @patch('smart_pdf_toolkit.core.pdf_operations.PDFDocumentValidator.validate_pdf_file')
    def test_rotate_pages_invalid_page_number(self, mock_validate, mock_fitz_open):
        """Test rotate with invalid page number."""
        mock_validate.return_value = True
        mock_doc = create_mock_pdf_doc(5)
        mock_fitz_open.return_value = mock_doc
        
        with pytest.raises(ValidationError, match="Page number 10 is out of range"):
            self.operations_manager.rotate_pages("input.pdf", {10: 90})
    
    @patch('smart_pdf_toolkit.core.pdf_operations.fitz.open')
    @patch('smart_pdf_toolkit.core.pdf_operations.PDFDocumentValidator.validate_pdf_file')
    def test_rotate_pages_invalid_rotation(self, mock_validate, mock_fitz_open):
        """Test rotate with invalid rotation angle."""
        mock_validate.return_value = True
        mock_doc = create_mock_pdf_doc(5)
        mock_fitz_open.return_value = mock_doc
        
        with pytest.raises(ValidationError, match="Unsupported rotation 45"):
            self.operations_manager.rotate_pages("input.pdf", {1: 45})
    
    @patch('smart_pdf_toolkit.core.pdf_operations.fitz.open')
    @patch('smart_pdf_toolkit.core.pdf_operations.PDFDocumentValidator.validate_pdf_file')
    def test_rotate_pages_success(self, mock_validate, mock_fitz_open):
        """Test successful page rotation operation."""
        mock_validate.return_value = True
        mock_doc = create_mock_pdf_doc(5)
        mock_fitz_open.return_value = mock_doc
        
        result = self.operations_manager.rotate_pages(
            "input.pdf", 
            {1: 90, 3: 180}
        )
        
        assert isinstance(result, OperationResult)
        assert result.success is True
        assert "Successfully rotated 2 pages" in result.message
        assert len(result.output_files) == 1
        assert result.execution_time >= 0
    
    # Extract Pages Tests
    def test_extract_pages_no_input_file(self):
        """Test extract with no input file."""
        with pytest.raises(ValidationError, match="Input file path is required"):
            self.operations_manager.extract_pages("", [1, 2])
    
    def test_extract_pages_no_pages(self):
        """Test extract with no pages specified."""
        with pytest.raises(ValidationError, match="Page list is required"):
            self.operations_manager.extract_pages("input.pdf", [])
    
    @patch('smart_pdf_toolkit.core.pdf_operations.fitz.open')
    @patch('smart_pdf_toolkit.core.pdf_operations.PDFDocumentValidator.validate_pdf_file')
    def test_extract_pages_invalid_page_number(self, mock_validate, mock_fitz_open):
        """Test extract with invalid page number."""
        mock_validate.return_value = True
        mock_doc = create_mock_pdf_doc(5)
        mock_fitz_open.return_value = mock_doc
        
        with pytest.raises(ValidationError, match="Page number 10 is out of range"):
            self.operations_manager.extract_pages("input.pdf", [1, 10])
    
    @patch('smart_pdf_toolkit.core.pdf_operations.fitz.open')
    @patch('smart_pdf_toolkit.core.pdf_operations.PDFDocumentValidator.validate_pdf_file')
    def test_extract_pages_success(self, mock_validate, mock_fitz_open):
        """Test successful page extraction operation."""
        mock_validate.return_value = True
        
        # Mock source document
        mock_source = create_mock_pdf_doc(10)
        
        # Mock extracted document
        mock_extracted = create_mock_pdf_doc(0)
        
        def mock_open_side_effect(path=None):
            if path and "input.pdf" in str(path):
                return mock_source
            else:  # New document
                return mock_extracted
        
        mock_fitz_open.side_effect = mock_open_side_effect
        
        result = self.operations_manager.extract_pages(
            "input.pdf", 
            [1, 3, 5, 3]  # Include duplicate to test deduplication
        )
        
        assert isinstance(result, OperationResult)
        assert result.success is True
        assert "Successfully extracted 3 pages" in result.message  # Deduplicated
        assert len(result.output_files) == 1
        assert result.execution_time >= 0
    
    # Reorder Pages Tests
    def test_reorder_pages_no_input_file(self):
        """Test reorder with no input file."""
        with pytest.raises(ValidationError, match="Input file path is required"):
            self.operations_manager.reorder_pages("", [1, 2, 3])
    
    def test_reorder_pages_no_order(self):
        """Test reorder with no new order specified."""
        with pytest.raises(ValidationError, match="New page order is required"):
            self.operations_manager.reorder_pages("input.pdf", [])
    
    @patch('smart_pdf_toolkit.core.pdf_operations.fitz.open')
    @patch('smart_pdf_toolkit.core.pdf_operations.PDFDocumentValidator.validate_pdf_file')
    def test_reorder_pages_wrong_count(self, mock_validate, mock_fitz_open):
        """Test reorder with wrong number of pages."""
        mock_validate.return_value = True
        mock_doc = create_mock_pdf_doc(5)
        mock_fitz_open.return_value = mock_doc
        
        with pytest.raises(ValidationError, match="New order must contain all 5 pages"):
            self.operations_manager.reorder_pages("input.pdf", [1, 2, 3])
    
    @patch('smart_pdf_toolkit.core.pdf_operations.fitz.open')
    @patch('smart_pdf_toolkit.core.pdf_operations.PDFDocumentValidator.validate_pdf_file')
    def test_reorder_pages_invalid_page_number(self, mock_validate, mock_fitz_open):
        """Test reorder with invalid page number."""
        mock_validate.return_value = True
        mock_doc = create_mock_pdf_doc(3)
        mock_fitz_open.return_value = mock_doc
        
        with pytest.raises(ValidationError, match="Page number 5 is out of range"):
            self.operations_manager.reorder_pages("input.pdf", [1, 2, 5])
    
    @patch('smart_pdf_toolkit.core.pdf_operations.fitz.open')
    @patch('smart_pdf_toolkit.core.pdf_operations.PDFDocumentValidator.validate_pdf_file')
    def test_reorder_pages_duplicate_pages(self, mock_validate, mock_fitz_open):
        """Test reorder with duplicate pages."""
        mock_validate.return_value = True
        mock_doc = create_mock_pdf_doc(3)
        mock_fitz_open.return_value = mock_doc
        
        with pytest.raises(ValidationError, match="must contain each page exactly once"):
            self.operations_manager.reorder_pages("input.pdf", [1, 1, 2])
    
    @patch('smart_pdf_toolkit.core.pdf_operations.fitz.open')
    @patch('smart_pdf_toolkit.core.pdf_operations.PDFDocumentValidator.validate_pdf_file')
    def test_reorder_pages_success(self, mock_validate, mock_fitz_open):
        """Test successful page reorder operation."""
        mock_validate.return_value = True
        
        # Mock source document
        mock_source = create_mock_pdf_doc(3)
        
        # Mock reordered document
        mock_reordered = create_mock_pdf_doc(0)
        
        def mock_open_side_effect(path=None):
            if path and "input.pdf" in str(path):
                return mock_source
            else:  # New document
                return mock_reordered
        
        mock_fitz_open.side_effect = mock_open_side_effect
        
        result = self.operations_manager.reorder_pages(
            "input.pdf", 
            [3, 1, 2]  # Reverse order
        )
        
        assert isinstance(result, OperationResult)
        assert result.success is True
        assert "Successfully reordered 3 pages" in result.message
        assert len(result.output_files) == 1
        assert result.execution_time >= 0


if __name__ == "__main__":
    pytest.main([__file__])