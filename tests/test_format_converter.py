"""
Unit tests for FormatConverter class.
Tests image conversion functionality with various formats and qualities.
"""

import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
import pytest
from PIL import Image
import fitz

from smart_pdf_toolkit.core.format_converter import FormatConverter
from smart_pdf_toolkit.core.interfaces import OperationResult
from smart_pdf_toolkit.core.exceptions import ConversionError
from smart_pdf_toolkit.core.config import ApplicationConfig


class TestFormatConverter:
    """Test suite for FormatConverter class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.converter = FormatConverter()
        
        # Create a simple test PDF
        self.test_pdf_path = os.path.join(self.temp_dir, "test.pdf")
        self._create_test_pdf(self.test_pdf_path)
        
        # Create test images
        self.test_images = []
        for i, format in enumerate(['PNG', 'JPEG']):
            img_path = os.path.join(self.temp_dir, f"test_image_{i}.{format.lower()}")
            self._create_test_image(img_path, format, (200, 300))
            self.test_images.append(img_path)
    
    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_pdf(self, path: str, pages: int = 3):
        """Create a simple test PDF with specified number of pages."""
        doc = fitz.open()
        for i in range(pages):
            page = doc.new_page()
            # Add some text to make the page visible
            text = f"Test Page {i + 1}"
            page.insert_text((100, 100), text, fontsize=20)
        doc.save(path)
        doc.close()
    
    def _create_test_image(self, path: str, format: str, size: tuple = (100, 100)):
        """Create a simple test image."""
        # Create a simple colored image
        if format.upper() == 'PNG':
            img = Image.new('RGBA', size, (255, 0, 0, 255))  # Red with alpha
        else:
            img = Image.new('RGB', size, (0, 255, 0))  # Green
        
        img.save(path, format=format.upper())
    
    def test_initialization(self):
        """Test FormatConverter initialization."""
        converter = FormatConverter()
        assert converter is not None
        assert converter.SUPPORTED_IMAGE_FORMATS == ['PNG', 'JPEG', 'TIFF', 'BMP', 'WEBP']
        assert converter.DEFAULT_DPI == 150
        assert converter.DEFAULT_QUALITY == 85
    
    def test_initialization_with_config(self):
        """Test FormatConverter initialization with custom config."""
        config = ApplicationConfig()
        converter = FormatConverter(config)
        assert converter.config == config
    
    def test_pdf_to_images_png_success(self):
        """Test successful PDF to PNG conversion."""
        output_dir = os.path.join(self.temp_dir, "output")
        
        result = self.converter.pdf_to_images(
            pdf_path=self.test_pdf_path,
            format='PNG',
            output_dir=output_dir
        )
        
        assert result.success is True
        assert len(result.output_files) == 3  # 3 pages
        assert result.execution_time > 0
        assert len(result.errors) == 0
        
        # Check that files were created
        for output_file in result.output_files:
            assert os.path.exists(output_file)
            assert output_file.endswith('.png')
    
    def test_pdf_to_images_jpeg_success(self):
        """Test successful PDF to JPEG conversion."""
        output_dir = os.path.join(self.temp_dir, "output")
        
        result = self.converter.pdf_to_images(
            pdf_path=self.test_pdf_path,
            format='JPEG',
            quality=90,
            output_dir=output_dir
        )
        
        assert result.success is True
        assert len(result.output_files) == 3
        
        # Check that files were created with correct format
        for output_file in result.output_files:
            assert os.path.exists(output_file)
            assert output_file.endswith('.jpeg')
    
    def test_pdf_to_images_with_page_range(self):
        """Test PDF to images conversion with specific page range."""
        output_dir = os.path.join(self.temp_dir, "output")
        
        result = self.converter.pdf_to_images(
            pdf_path=self.test_pdf_path,
            format='PNG',
            output_dir=output_dir,
            page_range=(1, 2)  # Pages 2-3 (0-indexed)
        )
        
        assert result.success is True
        assert len(result.output_files) == 2  # Only 2 pages
    
    def test_pdf_to_images_with_custom_dpi(self):
        """Test PDF to images conversion with custom DPI."""
        output_dir = os.path.join(self.temp_dir, "output")
        
        result = self.converter.pdf_to_images(
            pdf_path=self.test_pdf_path,
            format='PNG',
            dpi=300,
            output_dir=output_dir
        )
        
        assert result.success is True
        assert len(result.output_files) == 3
        
        # Higher DPI should result in larger images
        with Image.open(result.output_files[0]) as img:
            assert img.size[0] > 100  # Should be larger than default
    
    def test_pdf_to_images_invalid_format(self):
        """Test PDF to images conversion with invalid format."""
        result = self.converter.pdf_to_images(
            pdf_path=self.test_pdf_path,
            format='INVALID'
        )
        
        assert result.success is False
        assert "Unsupported format" in result.message
        assert len(result.errors) > 0
    
    def test_pdf_to_images_nonexistent_file(self):
        """Test PDF to images conversion with nonexistent PDF file."""
        result = self.converter.pdf_to_images(
            pdf_path="nonexistent.pdf",
            format='PNG'
        )
        
        assert result.success is False
        assert "PDF file not found" in result.message
        assert len(result.errors) > 0
    
    def test_pdf_to_images_quality_out_of_range(self):
        """Test PDF to images conversion with quality out of range."""
        output_dir = os.path.join(self.temp_dir, "output")
        
        result = self.converter.pdf_to_images(
            pdf_path=self.test_pdf_path,
            format='JPEG',
            quality=150,  # Out of range
            output_dir=output_dir
        )
        
        assert result.success is True  # Should still work with default quality
        assert len(result.warnings) > 0
        assert "Quality 150 out of range" in result.warnings[0]
    
    def test_pdf_to_images_dpi_out_of_range(self):
        """Test PDF to images conversion with DPI out of range."""
        output_dir = os.path.join(self.temp_dir, "output")
        
        result = self.converter.pdf_to_images(
            pdf_path=self.test_pdf_path,
            format='PNG',
            dpi=1000,  # Out of recommended range
            output_dir=output_dir
        )
        
        assert result.success is True  # Should still work with default DPI
        assert len(result.warnings) > 0
        assert "DPI 1000 out of recommended range" in result.warnings[0]
    
    def test_pdf_to_images_with_progress_callback(self):
        """Test PDF to images conversion with progress callback."""
        output_dir = os.path.join(self.temp_dir, "output")
        progress_calls = []
        
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        result = self.converter.pdf_to_images(
            pdf_path=self.test_pdf_path,
            format='PNG',
            output_dir=output_dir,
            progress_callback=progress_callback
        )
        
        assert result.success is True
        assert len(progress_calls) == 3  # One call per page
        assert progress_calls[-1] == (3, 3)  # Final call should be (3, 3)
    
    def test_images_to_pdf_success(self):
        """Test successful images to PDF conversion."""
        output_path = os.path.join(self.temp_dir, "output.pdf")
        
        result = self.converter.images_to_pdf(
            image_paths=self.test_images,
            output_path=output_path
        )
        
        assert result.success is True
        assert len(result.output_files) == 1
        assert result.output_files[0] == output_path
        assert os.path.exists(output_path)
        
        # Verify PDF was created correctly
        doc = fitz.open(output_path)
        assert doc.page_count == 2  # 2 test images
        doc.close()
    
    def test_images_to_pdf_with_page_size(self):
        """Test images to PDF conversion with custom page size."""
        output_path = os.path.join(self.temp_dir, "output.pdf")
        page_size = (612, 792)  # Letter size in points
        
        result = self.converter.images_to_pdf(
            image_paths=self.test_images,
            output_path=output_path,
            page_size=page_size
        )
        
        assert result.success is True
        assert os.path.exists(output_path)
        
        # Verify page size
        doc = fitz.open(output_path)
        page = doc[0]
        assert abs(page.rect.width - page_size[0]) < 1
        assert abs(page.rect.height - page_size[1]) < 1
        doc.close()
    
    def test_images_to_pdf_no_images(self):
        """Test images to PDF conversion with no images provided."""
        output_path = os.path.join(self.temp_dir, "output.pdf")
        
        result = self.converter.images_to_pdf(
            image_paths=[],
            output_path=output_path
        )
        
        assert result.success is False
        assert "No image paths provided" in result.message
    
    def test_images_to_pdf_nonexistent_images(self):
        """Test images to PDF conversion with nonexistent image files."""
        output_path = os.path.join(self.temp_dir, "output.pdf")
        
        result = self.converter.images_to_pdf(
            image_paths=["nonexistent1.png", "nonexistent2.jpg"],
            output_path=output_path
        )
        
        assert result.success is False
        assert "No valid image files found" in result.message
        assert len(result.errors) >= 1  # At least one error for the failure
    
    def test_images_to_pdf_mixed_valid_invalid(self):
        """Test images to PDF conversion with mix of valid and invalid images."""
        output_path = os.path.join(self.temp_dir, "output.pdf")
        mixed_images = self.test_images + ["nonexistent.png"]
        
        result = self.converter.images_to_pdf(
            image_paths=mixed_images,
            output_path=output_path
        )
        
        assert result.success is True  # Should succeed with valid images
        assert len(result.errors) == 1  # One error for missing file
        assert os.path.exists(output_path)
        
        # Should have 2 pages (from 2 valid images)
        doc = fitz.open(output_path)
        assert doc.page_count == 2
        doc.close()
    
    def test_images_to_pdf_with_progress_callback(self):
        """Test images to PDF conversion with progress callback."""
        output_path = os.path.join(self.temp_dir, "output.pdf")
        progress_calls = []
        
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        result = self.converter.images_to_pdf(
            image_paths=self.test_images,
            output_path=output_path,
            progress_callback=progress_callback
        )
        
        assert result.success is True
        assert len(progress_calls) == 2  # One call per image
        assert progress_calls[-1] == (2, 2)  # Final call should be (2, 2)
    
    def test_batch_convert_images_success(self):
        """Test successful batch conversion of PDFs to images."""
        # Create additional test PDFs
        pdf_paths = []
        for i in range(3):
            pdf_path = os.path.join(self.temp_dir, f"test_{i}.pdf")
            self._create_test_pdf(pdf_path, pages=2)
            pdf_paths.append(pdf_path)
        
        output_base_dir = os.path.join(self.temp_dir, "batch_output")
        
        result = self.converter.batch_convert_images(
            pdf_paths=pdf_paths,
            output_base_dir=output_base_dir,
            format='PNG'
        )
        
        assert result.success is True
        assert len(result.output_files) == 6  # 3 PDFs × 2 pages each
        assert "3/3 files successful" in result.message
        
        # Check that subdirectories were created
        for i in range(3):
            subdir = os.path.join(output_base_dir, f"test_{i}")
            assert os.path.exists(subdir)
    
    def test_batch_convert_images_with_progress_callback(self):
        """Test batch conversion with progress callback."""
        pdf_paths = [self.test_pdf_path]
        output_base_dir = os.path.join(self.temp_dir, "batch_output")
        progress_calls = []
        
        def progress_callback(current, total, current_file):
            progress_calls.append((current, total, current_file))
        
        result = self.converter.batch_convert_images(
            pdf_paths=pdf_paths,
            output_base_dir=output_base_dir,
            progress_callback=progress_callback
        )
        
        assert result.success is True
        assert len(progress_calls) == 1
        assert progress_calls[0] == (1, 1, self.test_pdf_path)
    
    def test_batch_convert_images_partial_failure(self):
        """Test batch conversion with some failures."""
        pdf_paths = [self.test_pdf_path, "nonexistent.pdf"]
        output_base_dir = os.path.join(self.temp_dir, "batch_output")
        
        result = self.converter.batch_convert_images(
            pdf_paths=pdf_paths,
            output_base_dir=output_base_dir
        )
        
        assert result.success is True  # Should succeed partially
        assert "1/2 files successful" in result.message
        assert len(result.errors) > 0  # Should have errors for failed file
    
    def test_pdf_to_office_docx_success(self):
        """Test successful PDF to DOCX conversion."""
        output_path = os.path.join(self.temp_dir, "output.docx")
        
        with patch('smart_pdf_toolkit.core.content_extractor.ContentExtractor') as mock_extractor_class:
            # Mock the content extractor
            mock_extractor = Mock()
            mock_extractor_class.return_value = mock_extractor
            
            # Mock successful text extraction
            mock_text_result = Mock()
            mock_text_result.success = True
            mock_text_result.content = "Sample extracted text\n\nAnother paragraph"
            mock_extractor.extract_text.return_value = mock_text_result
            
            # Mock image extraction (no images)
            mock_image_result = Mock()
            mock_image_result.success = False
            mock_image_result.output_files = []
            mock_extractor.extract_images.return_value = mock_image_result
            
            with patch('docx.Document') as mock_doc_class:
                mock_doc = Mock()
                mock_doc_class.return_value = mock_doc
                
                result = self.converter.pdf_to_office(
                    pdf_path=self.test_pdf_path,
                    target_format='docx',
                    output_path=output_path
                )
                
                assert result.success is True
                assert result.output_files == [output_path]
                assert "Successfully converted PDF to DOCX" in result.message
                mock_doc.save.assert_called_once_with(output_path)
    
    def test_pdf_to_office_xlsx_success(self):
        """Test successful PDF to XLSX conversion."""
        output_path = os.path.join(self.temp_dir, "output.xlsx")
        
        with patch('smart_pdf_toolkit.core.content_extractor.ContentExtractor') as mock_extractor_class:
            # Mock the content extractor
            mock_extractor = Mock()
            mock_extractor_class.return_value = mock_extractor
            
            # Mock successful table extraction
            mock_table_result = Mock()
            mock_table_result.success = True
            mock_table_result.tables = [
                [['Header1', 'Header2'], ['Data1', 'Data2']],
                [['Col1', 'Col2'], ['Val1', 'Val2']]
            ]
            mock_extractor.extract_tables.return_value = mock_table_result
            
            with patch('openpyxl.Workbook') as mock_wb_class:
                mock_wb = Mock()
                mock_ws = Mock()
                mock_wb.active = mock_ws
                mock_wb_class.return_value = mock_wb
                
                result = self.converter.pdf_to_office(
                    pdf_path=self.test_pdf_path,
                    target_format='xlsx',
                    output_path=output_path
                )
                
                assert result.success is True
                assert result.output_files == [output_path]
                assert "Successfully converted PDF to XLSX" in result.message
                mock_wb.save.assert_called_once_with(output_path)
    
    def test_pdf_to_office_invalid_format(self):
        """Test PDF to office conversion with invalid format."""
        result = self.converter.pdf_to_office(
            pdf_path=self.test_pdf_path,
            target_format='invalid'
        )
        
        assert result.success is False
        assert "Unsupported target format" in result.message
    
    def test_pdf_to_office_nonexistent_file(self):
        """Test PDF to office conversion with nonexistent file."""
        result = self.converter.pdf_to_office(
            pdf_path="nonexistent.pdf",
            target_format='docx'
        )
        
        assert result.success is False
        assert "PDF file not found" in result.message
    
    def test_pdf_to_office_missing_dependency(self):
        """Test PDF to office conversion with missing dependencies."""
        output_path = os.path.join(self.temp_dir, "output.docx")
        
        with patch('smart_pdf_toolkit.core.content_extractor.ContentExtractor'):
            with patch('docx.Document', side_effect=ImportError("python-docx not installed")):
                result = self.converter.pdf_to_office(
                    pdf_path=self.test_pdf_path,
                    target_format='docx',
                    output_path=output_path
                )
                
                assert result.success is False
                assert "python-docx library not installed" in result.message
    
    def test_office_to_pdf_docx_success(self):
        """Test successful DOCX to PDF conversion using LibreOffice."""
        input_path = os.path.join(self.temp_dir, "input.docx")
        output_path = os.path.join(self.temp_dir, "output.pdf")
        
        # Create a mock DOCX file
        with open(input_path, 'w') as f:
            f.write("mock docx content")
        
        with patch.object(self.converter, '_office_to_pdf_libreoffice') as mock_libreoffice:
            mock_libreoffice.return_value = {'success': True}
            
            result = self.converter.office_to_pdf(
                input_path=input_path,
                output_path=output_path
            )
            
            assert result.success is True
            assert result.output_files == [output_path]
            assert "Successfully converted Office document to PDF" in result.message
            mock_libreoffice.assert_called_once_with(input_path, output_path)
    
    def test_office_to_pdf_fallback_success(self):
        """Test successful Office to PDF conversion using fallback method."""
        input_path = os.path.join(self.temp_dir, "input.docx")
        output_path = os.path.join(self.temp_dir, "output.pdf")
        
        # Create a mock DOCX file
        with open(input_path, 'w') as f:
            f.write("mock docx content")
        
        with patch.object(self.converter, '_office_to_pdf_libreoffice') as mock_libreoffice:
            mock_libreoffice.return_value = {'success': False, 'warnings': [], 'errors': []}
            
            with patch.object(self.converter, '_docx_to_pdf_fallback') as mock_fallback:
                mock_fallback.return_value = {'success': True}
                
                result = self.converter.office_to_pdf(
                    input_path=input_path,
                    output_path=output_path
                )
                
                assert result.success is True
                mock_fallback.assert_called_once_with(input_path, output_path)
    
    def test_office_to_pdf_unsupported_format(self):
        """Test Office to PDF conversion with unsupported format."""
        input_path = os.path.join(self.temp_dir, "input.txt")
        
        # Create a text file
        with open(input_path, 'w') as f:
            f.write("text content")
        
        result = self.converter.office_to_pdf(input_path=input_path)
        
        assert result.success is False
        assert "Unsupported file format" in result.message
    
    def test_office_to_pdf_nonexistent_file(self):
        """Test Office to PDF conversion with nonexistent file."""
        result = self.converter.office_to_pdf(input_path="nonexistent.docx")
        
        assert result.success is False
        assert "Input file not found" in result.message
    
    def test_html_to_pdf_weasyprint_success(self):
        """Test successful HTML to PDF conversion using WeasyPrint."""
        html_content = "<html><body><h1>Test</h1><p>Content</p></body></html>"
        output_path = os.path.join(self.temp_dir, "output.pdf")
        
        with patch.object(self.converter, '_html_to_pdf_weasyprint') as mock_weasyprint:
            mock_weasyprint.return_value = {'success': True}
            
            result = self.converter.html_to_pdf(
                html_content=html_content,
                output_path=output_path
            )
            
            assert result.success is True
            assert result.output_files == [output_path]
            assert "Successfully converted HTML to PDF" in result.message
            mock_weasyprint.assert_called_once_with(html_content, output_path, None, None)
    
    def test_html_to_pdf_pdfkit_fallback(self):
        """Test HTML to PDF conversion using pdfkit fallback."""
        html_content = "<html><body><h1>Test</h1></body></html>"
        output_path = os.path.join(self.temp_dir, "output.pdf")
        
        with patch.object(self.converter, '_html_to_pdf_weasyprint') as mock_weasyprint:
            mock_weasyprint.return_value = {'success': False, 'warnings': [], 'errors': []}
            
            with patch.object(self.converter, '_html_to_pdf_pdfkit') as mock_pdfkit:
                mock_pdfkit.return_value = {'success': True}
                
                result = self.converter.html_to_pdf(
                    html_content=html_content,
                    output_path=output_path
                )
                
                assert result.success is True
                mock_pdfkit.assert_called_once_with(html_content, output_path, None)
    
    def test_html_to_pdf_with_css(self):
        """Test HTML to PDF conversion with CSS content."""
        html_content = "<html><body><h1>Test</h1></body></html>"
        css_content = "h1 { color: red; }"
        output_path = os.path.join(self.temp_dir, "output.pdf")
        
        with patch.object(self.converter, '_html_to_pdf_weasyprint') as mock_weasyprint:
            mock_weasyprint.return_value = {'success': True}
            
            result = self.converter.html_to_pdf(
                html_content=html_content,
                output_path=output_path,
                css_content=css_content
            )
            
            assert result.success is True
            mock_weasyprint.assert_called_once_with(html_content, output_path, css_content, None)
    
    def test_html_to_pdf_all_methods_fail(self):
        """Test HTML to PDF conversion when all methods fail."""
        html_content = "<html><body><h1>Test</h1></body></html>"
        output_path = os.path.join(self.temp_dir, "output.pdf")
        
        with patch.object(self.converter, '_html_to_pdf_weasyprint') as mock_weasyprint:
            mock_weasyprint.return_value = {'success': False, 'warnings': [], 'errors': []}
            
            with patch.object(self.converter, '_html_to_pdf_pdfkit') as mock_pdfkit:
                mock_pdfkit.return_value = {'success': False, 'warnings': [], 'errors': []}
                
                result = self.converter.html_to_pdf(
                    html_content=html_content,
                    output_path=output_path
                )
                
                assert result.success is False
                assert "All HTML to PDF conversion methods failed" in result.message
    
    def test_get_supported_formats(self):
        """Test getting supported formats."""
        formats = self.converter.get_supported_formats()
        
        assert 'pdf_to_image' in formats
        assert 'pdf_to_office' in formats
        assert 'office_to_pdf' in formats
        assert 'html_to_pdf' in formats
        
        assert formats['pdf_to_image'] == self.converter.SUPPORTED_IMAGE_FORMATS
        assert formats['pdf_to_office'] == ['docx', 'xlsx']
        assert formats['office_to_pdf'] == ['docx', 'xlsx', 'doc', 'xls']
        assert formats['html_to_pdf'] == ['html', 'htm']
    
    def test_validate_conversion_request_valid(self):
        """Test validation of valid conversion requests."""
        valid_conversions = [
            ('pdf', 'png'),
            ('pdf', 'docx'),
            ('docx', 'pdf'),
            ('html', 'pdf'),
            ('png', 'pdf')
        ]
        
        for source, target in valid_conversions:
            is_valid, error_msg = self.converter.validate_conversion_request(source, target)
            assert is_valid is True, f"Conversion {source} to {target} should be valid"
            assert error_msg == ""
    
    def test_validate_conversion_request_invalid(self):
        """Test validation of invalid conversion requests."""
        invalid_conversions = [
            ('txt', 'pdf'),
            ('pdf', 'mp3'),
            ('docx', 'png')
        ]
        
        for source, target in invalid_conversions:
            is_valid, error_msg = self.converter.validate_conversion_request(source, target)
            assert is_valid is False, f"Conversion {source} to {target} should be invalid"
            assert error_msg != ""
    
    def test_convert_file_pdf_to_image(self):
        """Test generic convert_file method for PDF to image."""
        output_path = os.path.join(self.temp_dir, "output.png")
        
        with patch.object(self.converter, 'pdf_to_images') as mock_pdf_to_images:
            mock_result = Mock()
            mock_result.success = True
            mock_pdf_to_images.return_value = mock_result
            
            result = self.converter.convert_file(
                input_path=self.test_pdf_path,
                output_path=output_path
            )
            
            assert result.success is True
            mock_pdf_to_images.assert_called_once()
    
    def test_convert_file_office_to_pdf(self):
        """Test generic convert_file method for Office to PDF."""
        input_path = os.path.join(self.temp_dir, "input.docx")
        output_path = os.path.join(self.temp_dir, "output.pdf")
        
        # Create mock input file
        with open(input_path, 'w') as f:
            f.write("mock content")
        
        with patch.object(self.converter, 'office_to_pdf') as mock_office_to_pdf:
            mock_result = Mock()
            mock_result.success = True
            mock_office_to_pdf.return_value = mock_result
            
            result = self.converter.convert_file(
                input_path=input_path,
                output_path=output_path
            )
            
            assert result.success is True
            mock_office_to_pdf.assert_called_once_with(
                input_path=input_path,
                output_path=output_path
            )
    
    def test_convert_file_html_to_pdf(self):
        """Test generic convert_file method for HTML to PDF."""
        input_path = os.path.join(self.temp_dir, "input.html")
        output_path = os.path.join(self.temp_dir, "output.pdf")
        
        # Create mock HTML file
        html_content = "<html><body><h1>Test</h1></body></html>"
        with open(input_path, 'w') as f:
            f.write(html_content)
        
        with patch.object(self.converter, 'html_to_pdf') as mock_html_to_pdf:
            mock_result = Mock()
            mock_result.success = True
            mock_html_to_pdf.return_value = mock_result
            
            result = self.converter.convert_file(
                input_path=input_path,
                output_path=output_path
            )
            
            assert result.success is True
            mock_html_to_pdf.assert_called_once()
    
    def test_convert_file_unsupported_conversion(self):
        """Test generic convert_file method with unsupported conversion."""
        input_path = os.path.join(self.temp_dir, "input.txt")
        output_path = os.path.join(self.temp_dir, "output.mp3")
        
        # Create mock input file
        with open(input_path, 'w') as f:
            f.write("text content")
        
        result = self.converter.convert_file(
            input_path=input_path,
            output_path=output_path
        )
        
        assert result.success is False
        assert "not supported" in result.message
    
    def test_convert_file_nonexistent_input(self):
        """Test generic convert_file method with nonexistent input."""
        result = self.converter.convert_file(
            input_path="nonexistent.pdf",
            output_path="output.png"
        )
        
        assert result.success is False
        assert "Input file not found" in result.message
    
    def test_supported_formats_validation(self):
        """Test that all supported formats work correctly."""
        output_dir = os.path.join(self.temp_dir, "format_test")
        
        for format in self.converter.SUPPORTED_IMAGE_FORMATS:
            result = self.converter.pdf_to_images(
                pdf_path=self.test_pdf_path,
                format=format,
                output_dir=output_dir
            )
            
            assert result.success is True, f"Format {format} should be supported"
            
            # Clean up for next iteration
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
    
    def test_image_quality_settings(self):
        """Test different image quality settings for JPEG."""
        output_dir = os.path.join(self.temp_dir, "quality_test")
        
        qualities = [10, 50, 90]
        file_sizes = []
        
        for quality in qualities:
            result = self.converter.pdf_to_images(
                pdf_path=self.test_pdf_path,
                format='JPEG',
                quality=quality,
                output_dir=output_dir
            )
            
            assert result.success is True
            
            # Check file size (higher quality should generally mean larger files)
            file_size = os.path.getsize(result.output_files[0])
            file_sizes.append(file_size)
            
            # Clean up for next iteration
            shutil.rmtree(output_dir)
        
        # Generally, higher quality should result in larger files
        # (though this isn't guaranteed for all images)
        assert len(file_sizes) == 3
    
    @patch('smart_pdf_toolkit.core.format_converter.fitz.open')
    def test_pdf_to_images_fitz_error(self, mock_fitz_open):
        """Test handling of PyMuPDF errors during PDF to images conversion."""
        mock_fitz_open.side_effect = Exception("PyMuPDF error")
        
        result = self.converter.pdf_to_images(
            pdf_path=self.test_pdf_path,
            format='PNG'
        )
        
        assert result.success is False
        assert "PDF to images conversion failed" in result.message
        assert len(result.errors) > 0
    
    @patch('smart_pdf_toolkit.core.format_converter.fitz.open')
    def test_images_to_pdf_fitz_error(self, mock_fitz_open):
        """Test handling of PyMuPDF errors during images to PDF conversion."""
        mock_fitz_open.side_effect = Exception("PyMuPDF error")
        
        output_path = os.path.join(self.temp_dir, "output.pdf")
        result = self.converter.images_to_pdf(
            image_paths=self.test_images,
            output_path=output_path
        )
        
        assert result.success is False
        assert "Images to PDF conversion failed" in result.message
        assert len(result.errors) > 0


class TestFormatConverterIntegration:
    """Integration tests for FormatConverter with real files."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.converter = FormatConverter()
    
    def teardown_method(self):
        """Clean up integration test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_round_trip_conversion(self):
        """Test converting PDF to images and back to PDF."""
        # Create original PDF
        original_pdf = os.path.join(self.temp_dir, "original.pdf")
        doc = fitz.open()
        for i in range(2):
            page = doc.new_page()
            page.insert_text((100, 100), f"Page {i + 1}", fontsize=20)
        doc.save(original_pdf)
        doc.close()
        
        # Convert PDF to images
        images_dir = os.path.join(self.temp_dir, "images")
        result1 = self.converter.pdf_to_images(
            pdf_path=original_pdf,
            format='PNG',
            output_dir=images_dir
        )
        
        assert result1.success is True
        assert len(result1.output_files) == 2
        
        # Convert images back to PDF
        final_pdf = os.path.join(self.temp_dir, "final.pdf")
        result2 = self.converter.images_to_pdf(
            image_paths=result1.output_files,
            output_path=final_pdf
        )
        
        assert result2.success is True
        assert os.path.exists(final_pdf)
        
        # Verify final PDF has correct number of pages
        doc = fitz.open(final_pdf)
        assert doc.page_count == 2
        doc.close()
    
    def test_different_image_formats_compatibility(self):
        """Test that different image formats can be mixed in images_to_pdf."""
        # Create images in different formats
        image_paths = []
        formats = ['PNG', 'JPEG']
        
        for i, format in enumerate(formats):
            img_path = os.path.join(self.temp_dir, f"test_{i}.{format.lower()}")
            if format == 'PNG':
                img = Image.new('RGBA', (100, 100), (255, 0, 0, 255))
            else:
                img = Image.new('RGB', (100, 100), (0, 255, 0))
            img.save(img_path, format=format)
            image_paths.append(img_path)
        
        # Convert mixed formats to PDF
        output_pdf = os.path.join(self.temp_dir, "mixed.pdf")
        result = self.converter.images_to_pdf(
            image_paths=image_paths,
            output_path=output_pdf
        )
        
        assert result.success is True
        assert os.path.exists(output_pdf)
        
        # Verify PDF
        doc = fitz.open(output_pdf)
        assert doc.page_count == 2
        doc.close()