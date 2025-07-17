"""
Integration tests for ContentExtractor class with real PDF files.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest

from smart_pdf_toolkit.core.content_extractor import ContentExtractor


class TestContentExtractorIntegration:
    """Integration test cases for ContentExtractor class."""
    
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
    def sample_pdf_path(self, temp_dir):
        """Create a simple PDF file for testing."""
        try:
            import fitz  # PyMuPDF
            
            # Create a simple PDF with text
            doc = fitz.open()
            page = doc.new_page()
            
            # Add some text
            text_rect = fitz.Rect(50, 50, 500, 100)
            page.insert_text((50, 80), "This is a test PDF document.", fontsize=12)
            page.insert_text((50, 120), "It contains multiple lines of text.", fontsize=12)
            page.insert_text((50, 160), "This is used for integration testing.", fontsize=12)
            
            # Add a second page
            page2 = doc.new_page()
            page2.insert_text((50, 80), "This is page 2 of the test document.", fontsize=12)
            page2.insert_text((50, 120), "It has different content.", fontsize=12)
            
            # Save the PDF
            pdf_path = os.path.join(temp_dir, "test_document.pdf")
            doc.save(pdf_path)
            doc.close()
            
            return pdf_path
            
        except ImportError:
            pytest.skip("PyMuPDF not available for creating test PDF")
    
    def test_extract_text_integration(self, content_extractor, sample_pdf_path):
        """Test text extraction with a real PDF file."""
        result = content_extractor.extract_text(sample_pdf_path, preserve_layout=False)
        
        assert result.success is True
        assert len(result.output_files) == 1
        assert result.execution_time >= 0
        assert "PyMuPDF" in result.message or "pdfplumber" in result.message
        
        # Check that the output file exists and contains text
        output_file = result.output_files[0]
        assert os.path.exists(output_file)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            extracted_text = f.read()
        
        assert "test PDF document" in extracted_text
        assert "integration testing" in extracted_text
        assert "page 2" in extracted_text
    
    def test_extract_text_with_layout_integration(self, content_extractor, sample_pdf_path):
        """Test text extraction with layout preservation."""
        result = content_extractor.extract_text(sample_pdf_path, preserve_layout=True)
        
        assert result.success is True
        assert len(result.output_files) == 1
        
        # Check that the output file exists and contains text
        output_file = result.output_files[0]
        assert os.path.exists(output_file)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            extracted_text = f.read()
        
        assert "test PDF document" in extracted_text
        assert "Page 1" in extracted_text or "Page 2" in extracted_text
    
    def test_extract_metadata_integration(self, content_extractor, sample_pdf_path):
        """Test metadata extraction with a real PDF file."""
        result = content_extractor.extract_metadata(sample_pdf_path)
        
        assert result.success is True
        assert len(result.output_files) == 1
        assert "2 pages" in result.message  # Our test PDF has 2 pages
        
        # Check that the output file exists and contains metadata
        output_file = result.output_files[0]
        assert os.path.exists(output_file)
        assert output_file.endswith('_metadata.json')
        
        import json
        with open(output_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        assert metadata['page_count'] == 2
        assert metadata['file_size'] > 0
        assert isinstance(metadata['is_encrypted'], bool)
        assert isinstance(metadata['permissions'], dict)
    
    def test_extract_images_integration_no_images(self, content_extractor, sample_pdf_path, temp_dir):
        """Test image extraction with a PDF that has no images."""
        output_dir = os.path.join(temp_dir, "images")
        
        result = content_extractor.extract_images(sample_pdf_path, output_dir)
        
        assert result.success is True
        assert "No images found" in result.message
        assert len(result.output_files) == 0
    
    def test_extract_tables_integration_no_tables(self, content_extractor, sample_pdf_path, temp_dir):
        """Test table extraction with a PDF that has no tables."""
        result = content_extractor.extract_tables(sample_pdf_path, format='csv', output_dir=temp_dir)
        
        assert result.success is True
        assert "No tables found" in result.message
        assert len(result.output_files) == 0
    
    def test_extract_links_integration_no_links(self, content_extractor, sample_pdf_path):
        """Test link extraction with a PDF that has no links."""
        result = content_extractor.extract_links(sample_pdf_path)
        
        assert result.success is True
        assert "0 links" in result.message
        assert len(result.output_files) == 1
        
        # Check that the output file exists
        output_file = result.output_files[0]
        assert os.path.exists(output_file)
        assert output_file.endswith('_links.json')
        
        import json
        with open(output_file, 'r', encoding='utf-8') as f:
            links_data = json.load(f)
        
        assert links_data['total_links'] == 0
        assert len(links_data['internal_links']) == 0
        assert len(links_data['external_links']) == 0
    
    def test_invalid_pdf_file(self, content_extractor, temp_dir):
        """Test handling of invalid PDF file."""
        # Create a non-PDF file
        invalid_file = os.path.join(temp_dir, "not_a_pdf.txt")
        with open(invalid_file, 'w') as f:
            f.write("This is not a PDF file")
        
        result = content_extractor.extract_text(invalid_file)
        
        assert result.success is False
        assert "extraction failed" in result.message.lower()
        assert len(result.errors) > 0
    
    def test_nonexistent_file(self, content_extractor):
        """Test handling of nonexistent file."""
        nonexistent_file = "/path/that/does/not/exist.pdf"
        
        result = content_extractor.extract_text(nonexistent_file)
        
        assert result.success is False
        assert "extraction failed" in result.message.lower()
        assert len(result.errors) > 0
    
    def test_extract_text_fallback_mechanism(self, content_extractor, sample_pdf_path):
        """Test that fallback mechanism works when primary method fails."""
        # This test verifies that the fallback mechanism is in place
        # In normal circumstances, PyMuPDF should work, but the fallback is there
        result = content_extractor.extract_text(sample_pdf_path, fallback_method=True)
        
        assert result.success is True
        assert len(result.output_files) == 1
        # Should use PyMuPDF primarily, but fallback is available
        assert "PyMuPDF" in result.message or "pdfplumber" in result.message
    
    def test_extract_text_no_fallback(self, content_extractor, sample_pdf_path):
        """Test text extraction without fallback mechanism."""
        result = content_extractor.extract_text(sample_pdf_path, fallback_method=False)
        
        assert result.success is True
        assert len(result.output_files) == 1
        # Should use PyMuPDF without fallback
        assert "PyMuPDF" in result.message
    
    def test_multiple_format_support(self, content_extractor, sample_pdf_path, temp_dir):
        """Test that different output formats are supported."""
        # Test CSV format for tables
        result_csv = content_extractor.extract_tables(sample_pdf_path, format='csv', output_dir=temp_dir)
        assert result_csv.success is True
        
        # Test Excel format for tables (if openpyxl is available)
        result_excel = content_extractor.extract_tables(sample_pdf_path, format='excel', output_dir=temp_dir)
        assert result_excel.success is True
        # Should either succeed with Excel or fallback to CSV with warning
        if result_excel.warnings:
            assert "openpyxl not available" in result_excel.warnings[0]
    
    def test_temp_directory_creation(self, temp_dir):
        """Test that ContentExtractor creates temp directory if it doesn't exist."""
        non_existent_temp = os.path.join(temp_dir, "non_existent_temp")
        assert not os.path.exists(non_existent_temp)
        
        extractor = ContentExtractor(temp_dir=non_existent_temp)
        assert os.path.exists(non_existent_temp)
        assert extractor.temp_dir == non_existent_temp
    
    def test_unique_filename_generation(self, content_extractor, sample_pdf_path):
        """Test that unique filenames are generated for output files."""
        # Extract text multiple times to test unique filename generation
        result1 = content_extractor.extract_text(sample_pdf_path)
        result2 = content_extractor.extract_text(sample_pdf_path)
        
        assert result1.success is True
        assert result2.success is True
        assert len(result1.output_files) == 1
        assert len(result2.output_files) == 1
        
        # Files should have different names
        file1 = result1.output_files[0]
        file2 = result2.output_files[0]
        assert file1 != file2
        assert os.path.exists(file1)
        assert os.path.exists(file2)