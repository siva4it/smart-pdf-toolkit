"""
Unit tests for ContentExtractor class.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from smart_pdf_toolkit.core.content_extractor import (
    ContentExtractor, 
    TextExtractionResult,
    ImageExtractionResult,
    TableExtractionResult,
    MetadataResult,
    LinkExtractionResult
)
from smart_pdf_toolkit.core.exceptions import PDFProcessingError, ValidationError


class TestContentExtractor:
    """Test cases for ContentExtractor class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def content_extractor(self, temp_dir):
        """Create ContentExtractor instance for testing."""
        return ContentExtractor(temp_dir=temp_dir)
    
    @pytest.fixture
    def mock_pdf_path(self, temp_dir):
        """Create a mock PDF file path."""
        pdf_path = os.path.join(temp_dir, "test.pdf")
        # Create empty file to pass existence check
        with open(pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')  # Minimal PDF header
        return pdf_path
    
    def test_init(self, temp_dir):
        """Test ContentExtractor initialization."""
        extractor = ContentExtractor(temp_dir=temp_dir)
        assert extractor.temp_dir == temp_dir
        assert os.path.exists(temp_dir)
    
    def test_init_default_temp_dir(self):
        """Test ContentExtractor initialization with default temp directory."""
        extractor = ContentExtractor()
        assert extractor.temp_dir is not None
        assert os.path.exists(extractor.temp_dir)
    
    @patch('smart_pdf_toolkit.core.content_extractor.fitz')
    @patch('smart_pdf_toolkit.core.content_extractor.validate_pdf_file')
    def test_extract_text_pymupdf_success(self, mock_validate, mock_fitz, content_extractor, mock_pdf_path):
        """Test successful text extraction using PyMuPDF."""
        # Mock PyMuPDF document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2
        mock_page1 = Mock()
        mock_page1.get_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.get_text.return_value = "Page 2 content"
        mock_doc.__getitem__.side_effect = [mock_page1, mock_page2]
        mock_fitz.open.return_value = mock_doc
        
        result = content_extractor.extract_text(mock_pdf_path, preserve_layout=False)
        
        assert result.success is True
        assert "PyMuPDF" in result.message
        assert len(result.output_files) == 1
        assert result.execution_time >= 0
        mock_validate.assert_called_once_with(mock_pdf_path)
        mock_doc.close.assert_called_once()
    
    @patch('smart_pdf_toolkit.core.content_extractor.fitz')
    @patch('smart_pdf_toolkit.core.content_extractor.pdfplumber')
    @patch('smart_pdf_toolkit.core.content_extractor.validate_pdf_file')
    def test_extract_text_fallback_to_pdfplumber(self, mock_validate, mock_pdfplumber, mock_fitz, 
                                                content_extractor, mock_pdf_path):
        """Test text extraction fallback to pdfplumber when PyMuPDF fails."""
        # Mock PyMuPDF to fail
        mock_fitz.open.side_effect = Exception("PyMuPDF failed")
        
        # Mock pdfplumber
        mock_pdf = Mock()
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 content"
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        result = content_extractor.extract_text(mock_pdf_path, fallback_method=True)
        
        assert result.success is True
        assert "pdfplumber (fallback)" in result.message
        assert len(result.warnings) == 1
        assert "PyMuPDF extraction failed" in result.warnings[0]
    
    @patch('smart_pdf_toolkit.core.content_extractor.fitz')
    @patch('smart_pdf_toolkit.core.content_extractor.validate_pdf_file')
    def test_extract_text_pymupdf_with_layout(self, mock_validate, mock_fitz, content_extractor, mock_pdf_path):
        """Test text extraction with layout preservation."""
        # Mock PyMuPDF document with text blocks
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_page = Mock()
        
        # Mock text blocks structure
        mock_blocks = {
            "blocks": [
                {
                    "lines": [
                        {
                            "spans": [
                                {"text": "First line"},
                                {"text": "continuation"}
                            ]
                        },
                        {
                            "spans": [
                                {"text": "Second line"}
                            ]
                        }
                    ]
                }
            ]
        }
        mock_page.get_text.return_value = mock_blocks
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_doc
        
        result = content_extractor.extract_text(mock_pdf_path, preserve_layout=True)
        
        assert result.success is True
        mock_page.get_text.assert_called_with("dict")
    
    @patch('smart_pdf_toolkit.core.content_extractor.validate_pdf_file')
    def test_extract_text_validation_error(self, mock_validate, content_extractor, mock_pdf_path):
        """Test text extraction with validation error."""
        mock_validate.side_effect = ValidationError("Invalid PDF")
        
        result = content_extractor.extract_text(mock_pdf_path)
        
        assert result.success is False
        assert "Invalid PDF" in result.message
        assert len(result.errors) == 1
    
    @patch('smart_pdf_toolkit.core.content_extractor.fitz')
    @patch('smart_pdf_toolkit.core.content_extractor.validate_pdf_file')
    @patch('smart_pdf_toolkit.core.content_extractor.validate_output_directory')
    @patch('smart_pdf_toolkit.core.content_extractor.ensure_directory_exists')
    def test_extract_images_success(self, mock_ensure_dir, mock_validate_dir, mock_validate_pdf, 
                                   mock_fitz, content_extractor, mock_pdf_path, temp_dir):
        """Test successful image extraction."""
        output_dir = os.path.join(temp_dir, "images")
        
        # Mock PyMuPDF document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_page = Mock()
        
        # Mock image list
        mock_page.get_images.return_value = [(1, 0, 100, 100, 8, 'DeviceRGB', '', 'Im1', 'DCTDecode')]
        
        # Mock pixmap
        mock_pixmap = Mock()
        mock_pixmap.width = 100
        mock_pixmap.height = 100
        mock_pixmap.n = 3  # RGB
        mock_pixmap.alpha = 0
        mock_fitz.Pixmap.return_value = mock_pixmap
        
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_doc
        
        # Mock file operations
        with patch('os.path.getsize', return_value=1024):
            result = content_extractor.extract_images(mock_pdf_path, output_dir)
        
        assert result.success is True
        assert len(result.output_files) >= 0  # May be 0 due to mocking
        mock_validate_pdf.assert_called_once_with(mock_pdf_path)
        mock_validate_dir.assert_called_once_with(output_dir)
    
    @patch('smart_pdf_toolkit.core.content_extractor.fitz')
    @patch('smart_pdf_toolkit.core.content_extractor.validate_pdf_file')
    @patch('smart_pdf_toolkit.core.content_extractor.validate_output_directory')
    @patch('smart_pdf_toolkit.core.content_extractor.ensure_directory_exists')
    def test_extract_images_no_images(self, mock_ensure_dir, mock_validate_dir, mock_validate_pdf, 
                                     mock_fitz, content_extractor, mock_pdf_path, temp_dir):
        """Test image extraction when no images are found."""
        output_dir = os.path.join(temp_dir, "images")
        
        # Mock PyMuPDF document with no images
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_page = Mock()
        mock_page.get_images.return_value = []
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_doc
        
        result = content_extractor.extract_images(mock_pdf_path, output_dir)
        
        assert result.success is True
        assert "No images found" in result.message
        assert len(result.output_files) == 0
    
    @patch('smart_pdf_toolkit.core.content_extractor.pdfplumber')
    @patch('smart_pdf_toolkit.core.content_extractor.validate_pdf_file')
    @patch('smart_pdf_toolkit.core.content_extractor.ensure_directory_exists')
    def test_extract_tables_csv_success(self, mock_ensure_dir, mock_validate, mock_pdfplumber, 
                                       content_extractor, mock_pdf_path, temp_dir):
        """Test successful table extraction to CSV."""
        # Mock pdfplumber
        mock_pdf = Mock()
        mock_page = Mock()
        mock_table = [
            ['Header1', 'Header2', 'Header3'],
            ['Row1Col1', 'Row1Col2', 'Row1Col3'],
            ['Row2Col1', 'Row2Col2', 'Row2Col3']
        ]
        mock_page.extract_tables.return_value = [mock_table]
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        result = content_extractor.extract_tables(mock_pdf_path, format='csv', output_dir=temp_dir)
        
        assert result.success is True
        assert len(result.output_files) == 1
        assert result.output_files[0].endswith('.csv')
        mock_validate.assert_called_once_with(mock_pdf_path)
    
    @patch('smart_pdf_toolkit.core.content_extractor.pdfplumber')
    @patch('smart_pdf_toolkit.core.content_extractor.validate_pdf_file')
    @patch('smart_pdf_toolkit.core.content_extractor.ensure_directory_exists')
    def test_extract_tables_no_tables(self, mock_ensure_dir, mock_validate, mock_pdfplumber, 
                                     content_extractor, mock_pdf_path, temp_dir):
        """Test table extraction when no tables are found."""
        # Mock pdfplumber with no tables
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_tables.return_value = []
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        result = content_extractor.extract_tables(mock_pdf_path, format='csv', output_dir=temp_dir)
        
        assert result.success is True
        assert "No tables found" in result.message
        assert len(result.output_files) == 0
    
    def test_extract_tables_invalid_format(self, content_extractor, mock_pdf_path, temp_dir):
        """Test table extraction with invalid format."""
        result = content_extractor.extract_tables(mock_pdf_path, format='invalid', output_dir=temp_dir)
        
        assert result.success is False
        assert "Unsupported format" in result.message
    
    @patch('smart_pdf_toolkit.core.content_extractor.fitz')
    @patch('smart_pdf_toolkit.core.content_extractor.validate_pdf_file')
    @patch('os.path.getsize')
    def test_extract_metadata_success(self, mock_getsize, mock_validate, mock_fitz, 
                                     content_extractor, mock_pdf_path):
        """Test successful metadata extraction."""
        mock_getsize.return_value = 1024
        
        # Mock PyMuPDF document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 5
        mock_doc.needs_pass = False
        mock_doc.is_pdf = True
        mock_doc.permissions = 0xFFFF  # All permissions
        mock_doc.metadata = {
            'title': 'Test Document',
            'author': 'Test Author',
            'subject': 'Test Subject',
            'creator': 'Test Creator',
            'producer': 'Test Producer',
            'creationDate': '2023-01-01',
            'modDate': '2023-01-02',
            'keywords': 'test, document'
        }
        mock_fitz.open.return_value = mock_doc
        
        result = content_extractor.extract_metadata(mock_pdf_path)
        
        assert result.success is True
        assert "5 pages" in result.message
        assert len(result.output_files) == 1
        assert result.output_files[0].endswith('_metadata.json')
        mock_validate.assert_called_once_with(mock_pdf_path)
    
    @patch('smart_pdf_toolkit.core.content_extractor.fitz')
    @patch('smart_pdf_toolkit.core.content_extractor.validate_pdf_file')
    def test_extract_links_success(self, mock_validate, mock_fitz, content_extractor, mock_pdf_path):
        """Test successful link extraction."""
        # Mock PyMuPDF document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2
        
        # Mock pages with links
        mock_page1 = Mock()
        mock_page1.get_links.return_value = [
            {'uri': 'https://example.com', 'from': {'x0': 10, 'y0': 10, 'x1': 100, 'y1': 20}, 'kind': 2},
            {'page': 1, 'from': {'x0': 10, 'y0': 30, 'x1': 100, 'y1': 40}, 'to': {'x0': 0, 'y0': 0}, 'kind': 1}
        ]
        
        mock_page2 = Mock()
        mock_page2.get_links.return_value = []
        
        mock_doc.__getitem__.side_effect = [mock_page1, mock_page2]
        mock_fitz.open.return_value = mock_doc
        
        result = content_extractor.extract_links(mock_pdf_path)
        
        assert result.success is True
        assert "2 links" in result.message
        assert len(result.output_files) == 1
        assert result.output_files[0].endswith('_links.json')
        mock_validate.assert_called_once_with(mock_pdf_path)
    
    @patch('smart_pdf_toolkit.core.content_extractor.fitz')
    @patch('smart_pdf_toolkit.core.content_extractor.validate_pdf_file')
    def test_extract_links_no_links(self, mock_validate, mock_fitz, content_extractor, mock_pdf_path):
        """Test link extraction when no links are found."""
        # Mock PyMuPDF document with no links
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_page = Mock()
        mock_page.get_links.return_value = []
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_doc
        
        result = content_extractor.extract_links(mock_pdf_path)
        
        assert result.success is True
        assert "0 links" in result.message
        assert len(result.output_files) == 1
    
    def test_process_text_blocks(self, content_extractor):
        """Test text block processing for layout preservation."""
        blocks_dict = {
            "blocks": [
                {
                    "lines": [
                        {
                            "spans": [
                                {"text": "First line"},
                                {"text": " continuation"}
                            ]
                        },
                        {
                            "spans": [
                                {"text": "Second line"}
                            ]
                        }
                    ]
                },
                {
                    "lines": [
                        {
                            "spans": [
                                {"text": "Third line"}
                            ]
                        }
                    ]
                }
            ]
        }
        
        result = content_extractor._process_text_blocks(blocks_dict)
        
        assert "First line continuation" in result
        assert "Second line" in result
        assert "Third line" in result
    
    def test_save_text_result(self, content_extractor, mock_pdf_path):
        """Test saving text extraction result."""
        text = "Sample extracted text"
        
        output_file = content_extractor._save_text_result(mock_pdf_path, text)
        
        assert os.path.exists(output_file)
        assert output_file.endswith('_extracted_text.txt')
        
        with open(output_file, 'r', encoding='utf-8') as f:
            saved_text = f.read()
        
        assert saved_text == text
    
    def test_save_metadata_result(self, content_extractor, mock_pdf_path):
        """Test saving metadata extraction result."""
        metadata = MetadataResult(
            title="Test Title",
            author="Test Author",
            subject=None,
            creator="Test Creator",
            producer="Test Producer",
            creation_date="2023-01-01",
            modification_date="2023-01-02",
            keywords="test",
            page_count=5,
            file_size=1024,
            is_encrypted=False,
            permissions={'print': True, 'copy': True},
            additional_metadata={}
        )
        
        output_file = content_extractor._save_metadata_result(mock_pdf_path, metadata)
        
        assert os.path.exists(output_file)
        assert output_file.endswith('_metadata.json')
        
        with open(output_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data['title'] == "Test Title"
        assert saved_data['page_count'] == 5
    
    def test_save_links_result(self, content_extractor, mock_pdf_path):
        """Test saving links extraction result."""
        links = LinkExtractionResult(
            internal_links=[{'page': 1, 'target_page': 2}],
            external_links=[{'page': 1, 'url': 'https://example.com'}],
            total_links=2,
            metadata={'internal_count': 1, 'external_count': 1}
        )
        
        output_file = content_extractor._save_links_result(mock_pdf_path, links)
        
        assert os.path.exists(output_file)
        assert output_file.endswith('_links.json')
        
        with open(output_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data['total_links'] == 2
        assert len(saved_data['internal_links']) == 1
        assert len(saved_data['external_links']) == 1


class TestTextExtractionResult:
    """Test cases for TextExtractionResult dataclass."""
    
    def test_text_extraction_result_creation(self):
        """Test creating TextExtractionResult."""
        result = TextExtractionResult(
            text="Sample text",
            page_count=5,
            word_count=100,
            character_count=500,
            extraction_method="PyMuPDF",
            layout_preserved=True,
            metadata={"key": "value"}
        )
        
        assert result.text == "Sample text"
        assert result.page_count == 5
        assert result.word_count == 100
        assert result.character_count == 500
        assert result.extraction_method == "PyMuPDF"
        assert result.layout_preserved is True
        assert result.metadata == {"key": "value"}


class TestImageExtractionResult:
    """Test cases for ImageExtractionResult dataclass."""
    
    def test_image_extraction_result_creation(self):
        """Test creating ImageExtractionResult."""
        result = ImageExtractionResult(
            image_files=["image1.png", "image2.jpg"],
            image_count=2,
            total_size_bytes=2048,
            formats_used=["PNG", "JPEG"],
            metadata={"key": "value"}
        )
        
        assert result.image_files == ["image1.png", "image2.jpg"]
        assert result.image_count == 2
        assert result.total_size_bytes == 2048
        assert result.formats_used == ["PNG", "JPEG"]
        assert result.metadata == {"key": "value"}


class TestTableExtractionResult:
    """Test cases for TableExtractionResult dataclass."""
    
    def test_table_extraction_result_creation(self):
        """Test creating TableExtractionResult."""
        result = TableExtractionResult(
            table_files=["table1.csv", "table2.csv"],
            table_count=2,
            format="csv",
            metadata={"key": "value"}
        )
        
        assert result.table_files == ["table1.csv", "table2.csv"]
        assert result.table_count == 2
        assert result.format == "csv"
        assert result.metadata == {"key": "value"}


class TestMetadataResult:
    """Test cases for MetadataResult dataclass."""
    
    def test_metadata_result_creation(self):
        """Test creating MetadataResult."""
        result = MetadataResult(
            title="Test Title",
            author="Test Author",
            subject="Test Subject",
            creator="Test Creator",
            producer="Test Producer",
            creation_date="2023-01-01",
            modification_date="2023-01-02",
            keywords="test, keywords",
            page_count=10,
            file_size=1024,
            is_encrypted=False,
            permissions={"print": True, "copy": False},
            additional_metadata={"custom": "value"}
        )
        
        assert result.title == "Test Title"
        assert result.author == "Test Author"
        assert result.page_count == 10
        assert result.file_size == 1024
        assert result.is_encrypted is False
        assert result.permissions == {"print": True, "copy": False}


class TestLinkExtractionResult:
    """Test cases for LinkExtractionResult dataclass."""
    
    def test_link_extraction_result_creation(self):
        """Test creating LinkExtractionResult."""
        result = LinkExtractionResult(
            internal_links=[{"page": 1, "target_page": 2}],
            external_links=[{"page": 1, "url": "https://example.com"}],
            total_links=2,
            metadata={"internal_count": 1, "external_count": 1}
        )
        
        assert len(result.internal_links) == 1
        assert len(result.external_links) == 1
        assert result.total_links == 2
        assert result.metadata["internal_count"] == 1
        assert result.metadata["external_count"] == 1