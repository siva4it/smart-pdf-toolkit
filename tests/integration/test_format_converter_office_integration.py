"""
Integration tests for FormatConverter office document conversion functionality.
Tests real conversion scenarios with actual dependencies.
"""

import os
import tempfile
import shutil
import pytest
from unittest.mock import patch, Mock
import fitz

from smart_pdf_toolkit.core.format_converter import FormatConverter
from smart_pdf_toolkit.core.exceptions import ConversionError


class TestFormatConverterOfficeIntegration:
    """Integration tests for office document conversion."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.converter = FormatConverter()
        
        # Create a test PDF with text content
        self.test_pdf_path = os.path.join(self.temp_dir, "test.pdf")
        self._create_test_pdf_with_content()
    
    def teardown_method(self):
        """Clean up integration test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_pdf_with_content(self):
        """Create a test PDF with rich content for conversion testing."""
        doc = fitz.open()
        
        # Page 1: Text content
        page1 = doc.new_page()
        page1.insert_text((50, 100), "Test Document Title", fontsize=24)
        page1.insert_text((50, 150), "This is a sample paragraph with some text content.", fontsize=12)
        page1.insert_text((50, 180), "Another paragraph with different content.", fontsize=12)
        
        # Page 2: More structured content
        page2 = doc.new_page()
        page2.insert_text((50, 100), "Chapter 1: Introduction", fontsize=18)
        page2.insert_text((50, 140), "This chapter introduces the main concepts.", fontsize=12)
        page2.insert_text((50, 170), "Key points:", fontsize=12)
        page2.insert_text((70, 200), "• Point one", fontsize=12)
        page2.insert_text((70, 220), "• Point two", fontsize=12)
        page2.insert_text((70, 240), "• Point three", fontsize=12)
        
        doc.save(self.test_pdf_path)
        doc.close()
    
    def test_pdf_to_docx_integration_with_mocked_dependencies(self):
        """Test PDF to DOCX conversion with mocked dependencies."""
        output_path = os.path.join(self.temp_dir, "output.docx")
        
        # Mock the dependencies to avoid requiring actual installation
        with patch('smart_pdf_toolkit.core.format_converter.ContentExtractor') as mock_extractor_class:
            mock_extractor = Mock()
            mock_extractor_class.return_value = mock_extractor
            
            # Mock successful text extraction
            mock_text_result = Mock()
            mock_text_result.success = True
            mock_text_result.content = "Test Document Title\n\nThis is extracted content from the PDF."
            mock_extractor.extract_text.return_value = mock_text_result
            
            # Mock image extraction (no images)
            mock_image_result = Mock()
            mock_image_result.success = False
            mock_image_result.output_files = []
            mock_extractor.extract_images.return_value = mock_image_result
            
            with patch('docx.Document') as mock_doc_class:
                mock_doc = Mock()
                mock_heading = Mock()
                mock_paragraph = Mock()
                
                mock_doc.add_heading.return_value = mock_heading
                mock_doc.add_paragraph.return_value = mock_paragraph
                mock_doc_class.return_value = mock_doc
                
                result = self.converter.pdf_to_office(
                    pdf_path=self.test_pdf_path,
                    target_format='docx',
                    output_path=output_path
                )
                
                # Verify the conversion was successful
                assert result.success is True
                assert result.output_files == [output_path]
                assert "Successfully converted PDF to DOCX" in result.message
                
                # Verify the document was created and saved
                mock_doc.save.assert_called_once_with(output_path)
                
                # Verify content was added to the document
                mock_doc.add_heading.assert_called()
                mock_doc.add_paragraph.assert_called()
    
    def test_pdf_to_xlsx_integration_with_mocked_dependencies(self):
        """Test PDF to XLSX conversion with mocked dependencies."""
        output_path = os.path.join(self.temp_dir, "output.xlsx")
        
        with patch('smart_pdf_toolkit.core.format_converter.ContentExtractor') as mock_extractor_class:
            mock_extractor = Mock()
            mock_extractor_class.return_value = mock_extractor
            
            # Mock table extraction with sample data
            mock_table_result = Mock()
            mock_table_result.success = True
            mock_table_result.tables = [
                [['Name', 'Age', 'City'], ['John', '25', 'New York'], ['Jane', '30', 'Boston']],
                [['Product', 'Price'], ['Widget A', '$10'], ['Widget B', '$15']]
            ]
            mock_extractor.extract_tables.return_value = mock_table_result
            
            with patch('openpyxl.Workbook') as mock_wb_class:
                mock_wb = Mock()
                mock_ws = Mock()
                mock_cell = Mock()
                
                mock_wb.active = mock_ws
                mock_ws.cell.return_value = mock_cell
                mock_wb_class.return_value = mock_wb
                
                result = self.converter.pdf_to_office(
                    pdf_path=self.test_pdf_path,
                    target_format='xlsx',
                    output_path=output_path
                )
                
                # Verify the conversion was successful
                assert result.success is True
                assert result.output_files == [output_path]
                assert "Successfully converted PDF to XLSX" in result.message
                
                # Verify the workbook was saved
                mock_wb.save.assert_called_once_with(output_path)
                
                # Verify cells were populated
                assert mock_ws.cell.call_count > 0
    
    def test_office_to_pdf_libreoffice_integration(self):
        """Test Office to PDF conversion using LibreOffice (mocked)."""
        input_path = os.path.join(self.temp_dir, "input.docx")
        output_path = os.path.join(self.temp_dir, "output.pdf")
        
        # Create a mock DOCX file
        with open(input_path, 'wb') as f:
            f.write(b"Mock DOCX content")
        
        with patch('subprocess.run') as mock_subprocess:
            with patch('shutil.which', return_value='libreoffice'):
                # Mock successful LibreOffice conversion
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stderr = ""
                mock_subprocess.return_value = mock_result
                
                # Mock the expected PDF output file
                expected_pdf = os.path.join(self.temp_dir, "input.pdf")
                with open(expected_pdf, 'wb') as f:
                    f.write(b"Mock PDF content")
                
                with patch('shutil.move') as mock_move:
                    result = self.converter.office_to_pdf(
                        input_path=input_path,
                        output_path=output_path
                    )
                    
                    assert result.success is True
                    assert result.output_files == [output_path]
                    assert "Successfully converted Office document to PDF" in result.message
                    
                    # Verify LibreOffice was called
                    mock_subprocess.assert_called_once()
                    args = mock_subprocess.call_args[0][0]
                    assert 'libreoffice' in args[0] or 'soffice' in args[0]
                    assert '--headless' in args
                    assert '--convert-to' in args
                    assert 'pdf' in args
    
    def test_office_to_pdf_fallback_docx_integration(self):
        """Test Office to PDF conversion using fallback method for DOCX."""
        input_path = os.path.join(self.temp_dir, "input.docx")
        output_path = os.path.join(self.temp_dir, "output.pdf")
        
        # Create a mock DOCX file
        with open(input_path, 'wb') as f:
            f.write(b"Mock DOCX content")
        
        # Mock LibreOffice failure
        with patch.object(self.converter, '_office_to_pdf_libreoffice') as mock_libreoffice:
            mock_libreoffice.return_value = {
                'success': False, 
                'error': 'LibreOffice not found',
                'warnings': [],
                'errors': []
            }
            
            # Mock successful fallback conversion
            with patch('docx.Document') as mock_doc_class:
                with patch('reportlab.platypus.SimpleDocTemplate') as mock_pdf_doc:
                    mock_doc = Mock()
                    mock_doc.paragraphs = [Mock(text="Sample paragraph", style=Mock(name="Normal"))]
                    mock_doc_class.return_value = mock_doc
                    
                    mock_pdf = Mock()
                    mock_pdf_doc.return_value = mock_pdf
                    
                    result = self.converter.office_to_pdf(
                        input_path=input_path,
                        output_path=output_path
                    )
                    
                    assert result.success is True
                    assert result.output_files == [output_path]
                    
                    # Verify fallback method was used
                    mock_pdf.build.assert_called_once()
    
    def test_html_to_pdf_weasyprint_integration(self):
        """Test HTML to PDF conversion using WeasyPrint (mocked)."""
        html_content = """
        <html>
        <head><title>Test Document</title></head>
        <body>
            <h1>Main Title</h1>
            <p>This is a paragraph with some content.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </body>
        </html>
        """
        css_content = "h1 { color: blue; } p { font-size: 14px; }"
        output_path = os.path.join(self.temp_dir, "output.pdf")
        
        with patch('weasyprint.HTML') as mock_html_class:
            with patch('weasyprint.CSS') as mock_css_class:
                mock_html = Mock()
                mock_css = Mock()
                mock_html_class.return_value = mock_html
                mock_css_class.return_value = mock_css
                
                result = self.converter.html_to_pdf(
                    html_content=html_content,
                    output_path=output_path,
                    css_content=css_content
                )
                
                assert result.success is True
                assert result.output_files == [output_path]
                assert "Successfully converted HTML to PDF" in result.message
                
                # Verify WeasyPrint was used correctly
                mock_html_class.assert_called_once_with(string=html_content, base_url=None)
                mock_css_class.assert_called_once_with(string=css_content)
                mock_html.write_pdf.assert_called_once_with(output_path, stylesheets=[mock_css])
    
    def test_html_to_pdf_pdfkit_fallback_integration(self):
        """Test HTML to PDF conversion using pdfkit fallback (mocked)."""
        html_content = "<html><body><h1>Test</h1><p>Content</p></body></html>"
        output_path = os.path.join(self.temp_dir, "output.pdf")
        
        # Mock WeasyPrint failure
        with patch.object(self.converter, '_html_to_pdf_weasyprint') as mock_weasyprint:
            mock_weasyprint.return_value = {
                'success': False,
                'error': 'WeasyPrint not available',
                'warnings': [],
                'errors': []
            }
            
            # Mock successful pdfkit conversion
            with patch('pdfkit.from_string') as mock_pdfkit:
                with patch('tempfile.NamedTemporaryFile'):
                    result = self.converter.html_to_pdf(
                        html_content=html_content,
                        output_path=output_path
                    )
                    
                    assert result.success is True
                    assert result.output_files == [output_path]
                    
                    # Verify pdfkit was called
                    mock_pdfkit.assert_called_once()
                    args, kwargs = mock_pdfkit.call_args
                    assert args[0] == html_content
                    assert args[1] == output_path
    
    def test_convert_file_generic_method_integration(self):
        """Test the generic convert_file method with various conversions."""
        # Test PDF to image conversion
        output_image = os.path.join(self.temp_dir, "output.png")
        
        result = self.converter.convert_file(
            input_path=self.test_pdf_path,
            output_path=output_image
        )
        
        assert result.success is True
        assert len(result.output_files) > 0
        
        # Test HTML to PDF conversion (mocked)
        html_file = os.path.join(self.temp_dir, "input.html")
        pdf_output = os.path.join(self.temp_dir, "html_output.pdf")
        
        with open(html_file, 'w') as f:
            f.write("<html><body><h1>Test HTML</h1></body></html>")
        
        with patch.object(self.converter, 'html_to_pdf') as mock_html_to_pdf:
            mock_result = Mock()
            mock_result.success = True
            mock_result.output_files = [pdf_output]
            mock_html_to_pdf.return_value = mock_result
            
            result = self.converter.convert_file(
                input_path=html_file,
                output_path=pdf_output
            )
            
            assert result.success is True
            mock_html_to_pdf.assert_called_once()
    
    def test_format_validation_integration(self):
        """Test format validation with various file types."""
        # Test supported conversions
        supported_tests = [
            ('pdf', 'png', True),
            ('pdf', 'docx', True),
            ('docx', 'pdf', True),
            ('html', 'pdf', True),
            ('jpeg', 'pdf', True)
        ]
        
        for source, target, expected in supported_tests:
            is_valid, error_msg = self.converter.validate_conversion_request(source, target)
            assert is_valid == expected, f"Validation failed for {source} to {target}"
            if expected:
                assert error_msg == ""
            else:
                assert error_msg != ""
        
        # Test unsupported conversions
        unsupported_tests = [
            ('txt', 'pdf', False),
            ('pdf', 'mp4', False),
            ('docx', 'jpg', False)
        ]
        
        for source, target, expected in unsupported_tests:
            is_valid, error_msg = self.converter.validate_conversion_request(source, target)
            assert is_valid == expected, f"Validation failed for {source} to {target}"
            assert error_msg != ""
    
    def test_error_handling_integration(self):
        """Test error handling in various scenarios."""
        # Test with nonexistent input file
        result = self.converter.pdf_to_office(
            pdf_path="nonexistent.pdf",
            target_format='docx'
        )
        assert result.success is False
        assert "PDF file not found" in result.message
        
        # Test with invalid target format
        result = self.converter.pdf_to_office(
            pdf_path=self.test_pdf_path,
            target_format='invalid'
        )
        assert result.success is False
        assert "Unsupported target format" in result.message
        
        # Test office to PDF with unsupported file
        txt_file = os.path.join(self.temp_dir, "test.txt")
        with open(txt_file, 'w') as f:
            f.write("Plain text content")
        
        result = self.converter.office_to_pdf(input_path=txt_file)
        assert result.success is False
        assert "Unsupported file format" in result.message
    
    def test_dependency_error_handling(self):
        """Test handling of missing dependencies."""
        output_path = os.path.join(self.temp_dir, "output.docx")
        
        # Test missing python-docx dependency
        with patch('docx.Document', side_effect=ImportError("No module named 'docx'")):
            with patch('smart_pdf_toolkit.core.format_converter.ContentExtractor'):
                result = self.converter.pdf_to_office(
                    pdf_path=self.test_pdf_path,
                    target_format='docx',
                    output_path=output_path
                )
                
                assert result.success is False
                assert "python-docx library not installed" in result.message
        
        # Test missing openpyxl dependency
        with patch('openpyxl.Workbook', side_effect=ImportError("No module named 'openpyxl'")):
            with patch('smart_pdf_toolkit.core.format_converter.ContentExtractor'):
                result = self.converter.pdf_to_office(
                    pdf_path=self.test_pdf_path,
                    target_format='xlsx',
                    output_path=output_path
                )
                
                assert result.success is False
                assert "openpyxl library not installed" in result.message
        
        # Test missing WeasyPrint dependency
        html_content = "<html><body><h1>Test</h1></body></html>"
        pdf_output = os.path.join(self.temp_dir, "output.pdf")
        
        with patch('weasyprint.HTML', side_effect=ImportError("No module named 'weasyprint'")):
            with patch.object(self.converter, '_html_to_pdf_pdfkit') as mock_pdfkit:
                mock_pdfkit.return_value = {'success': False, 'warnings': [], 'errors': []}
                
                result = self.converter.html_to_pdf(
                    html_content=html_content,
                    output_path=pdf_output
                )
                
                assert result.success is False
                assert "All HTML to PDF conversion methods failed" in result.message


if __name__ == '__main__':
    pytest.main([__file__])