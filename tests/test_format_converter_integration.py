"""
Integration tests for FormatConverter with the broader system.
Tests integration with other components and real-world scenarios.
"""

import os
import tempfile
import shutil
from pathlib import Path
import fitz
from PIL import Image

from smart_pdf_toolkit.core.format_converter import FormatConverter
from smart_pdf_toolkit.core.pdf_operations import PDFOperationsManager
from smart_pdf_toolkit.core.content_extractor import ContentExtractor


class TestFormatConverterIntegration:
    """Integration tests for FormatConverter with other system components."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.converter = FormatConverter()
        self.pdf_ops = PDFOperationsManager()
        self.extractor = ContentExtractor()
        
        # Create a complex test PDF with multiple pages and content
        self.test_pdf_path = os.path.join(self.temp_dir, "complex_test.pdf")
        self._create_complex_test_pdf(self.test_pdf_path)
    
    def teardown_method(self):
        """Clean up integration test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_complex_test_pdf(self, path: str):
        """Create a complex test PDF with text, shapes, and multiple pages."""
        doc = fitz.open()
        
        # Page 1: Text content
        page1 = doc.new_page()
        page1.insert_text((50, 100), "Page 1: Main Content", fontsize=24)
        page1.insert_text((50, 150), "This is a test document with multiple pages.", fontsize=12)
        page1.insert_text((50, 180), "It contains various types of content for testing.", fontsize=12)
        
        # Add a rectangle
        rect = fitz.Rect(50, 200, 200, 250)
        page1.draw_rect(rect, color=(1, 0, 0), width=2)
        
        # Page 2: More content
        page2 = doc.new_page()
        page2.insert_text((50, 100), "Page 2: Additional Content", fontsize=24)
        page2.insert_text((50, 150), "This page has different content.", fontsize=12)
        
        # Add a circle
        center = fitz.Point(150, 200)
        page2.draw_circle(center, 30, color=(0, 1, 0), width=2)
        
        # Page 3: Final page
        page3 = doc.new_page()
        page3.insert_text((50, 100), "Page 3: Final Page", fontsize=24)
        page3.insert_text((50, 150), "This is the last page of the test document.", fontsize=12)
        
        doc.save(path)
        doc.close()
    
    def test_pdf_operations_with_format_conversion(self):
        """Test combining PDF operations with format conversion."""
        # First, split the PDF using PDFOperationsManager
        split_result = self.pdf_ops.split_pdf(
            input_file=self.test_pdf_path,
            page_ranges=[(1, 2), (3, 3)]  # Pages 1-2 and page 3 (1-indexed)
        )
        
        assert split_result.success is True
        assert len(split_result.output_files) == 2
        
        # Convert each split PDF to images
        all_images = []
        for pdf_file in split_result.output_files:
            images_dir = os.path.join(self.temp_dir, f"images_{Path(pdf_file).stem}")
            
            convert_result = self.converter.pdf_to_images(
                pdf_path=pdf_file,
                format='PNG',
                output_dir=images_dir
            )
            
            assert convert_result.success is True
            all_images.extend(convert_result.output_files)
        
        # Should have 3 images total (2 from first split + 1 from second split)
        assert len(all_images) == 3
        
        # Verify all image files exist and are valid
        for img_path in all_images:
            assert os.path.exists(img_path)
            with Image.open(img_path) as img:
                assert img.size[0] > 0 and img.size[1] > 0
    
    def test_content_extraction_with_format_conversion(self):
        """Test extracting content and then converting to images."""
        # Extract text content first
        text_result = self.extractor.extract_text(self.test_pdf_path)
        assert text_result.success is True
        
        # Convert to images with high quality for OCR potential
        images_dir = os.path.join(self.temp_dir, "high_quality_images")
        convert_result = self.converter.pdf_to_images(
            pdf_path=self.test_pdf_path,
            format='PNG',
            dpi=300,  # High DPI for better text clarity
            output_dir=images_dir
        )
        
        assert convert_result.success is True
        assert len(convert_result.output_files) == 3  # 3 pages
        
        # Verify high-quality images were created
        for img_path in convert_result.output_files:
            with Image.open(img_path) as img:
                # High DPI should result in larger images
                assert img.size[0] > 400  # Should be reasonably large
                assert img.size[1] > 400
    
    def test_batch_conversion_workflow(self):
        """Test a complete batch conversion workflow."""
        # Create multiple test PDFs
        pdf_files = []
        for i in range(3):
            pdf_path = os.path.join(self.temp_dir, f"batch_test_{i}.pdf")
            doc = fitz.open()
            for j in range(2):  # 2 pages each
                page = doc.new_page()
                page.insert_text((50, 100), f"PDF {i}, Page {j + 1}", fontsize=20)
            doc.save(pdf_path)
            doc.close()
            pdf_files.append(pdf_path)
        
        # Batch convert all PDFs to images
        batch_output_dir = os.path.join(self.temp_dir, "batch_output")
        
        batch_result = self.converter.batch_convert_images(
            pdf_paths=pdf_files,
            output_base_dir=batch_output_dir,
            format='JPEG',
            quality=80
        )
        
        assert batch_result.success is True
        assert len(batch_result.output_files) == 6  # 3 PDFs × 2 pages each
        
        # Verify directory structure
        for i in range(3):
            subdir = os.path.join(batch_output_dir, f"batch_test_{i}")
            assert os.path.exists(subdir)
            
            # Should have 2 JPEG files in each subdirectory
            jpeg_files = [f for f in os.listdir(subdir) if f.endswith('.jpeg')]
            assert len(jpeg_files) == 2
    
    def test_round_trip_with_pdf_operations(self):
        """Test converting to images and back, then performing PDF operations."""
        # Convert original PDF to images
        images_dir = os.path.join(self.temp_dir, "round_trip_images")
        to_images_result = self.converter.pdf_to_images(
            pdf_path=self.test_pdf_path,
            format='PNG',
            output_dir=images_dir
        )
        
        assert to_images_result.success is True
        assert len(to_images_result.output_files) == 3
        
        # Convert images back to PDF
        reconstructed_pdf = os.path.join(self.temp_dir, "reconstructed.pdf")
        to_pdf_result = self.converter.images_to_pdf(
            image_paths=to_images_result.output_files,
            output_path=reconstructed_pdf
        )
        
        assert to_pdf_result.success is True
        assert os.path.exists(reconstructed_pdf)
        
        # Now perform PDF operations on the reconstructed PDF
        # Test merging with original
        merged_pdf = os.path.join(self.temp_dir, "merged.pdf")
        merge_result = self.pdf_ops.merge_pdfs(
            input_files=[self.test_pdf_path, reconstructed_pdf],
            output_file=merged_pdf
        )
        
        assert merge_result.success is True
        assert os.path.exists(merged_pdf)
        
        # Verify merged PDF has 6 pages (3 original + 3 reconstructed)
        doc = fitz.open(merged_pdf)
        assert doc.page_count == 6
        doc.close()
    
    def test_format_conversion_with_different_page_sizes(self):
        """Test format conversion with PDFs of different page sizes."""
        # Create PDFs with different page sizes
        pdf_files = []
        page_sizes = [
            (612, 792),   # Letter
            (595, 842),   # A4
            (792, 1224),  # Tabloid
        ]
        
        for i, (width, height) in enumerate(page_sizes):
            pdf_path = os.path.join(self.temp_dir, f"size_test_{i}.pdf")
            doc = fitz.open()
            page = doc.new_page(width=width, height=height)
            page.insert_text((50, 100), f"Page size: {width}x{height}", fontsize=16)
            doc.save(pdf_path)
            doc.close()
            pdf_files.append(pdf_path)
        
        # Convert each to images
        all_images = []
        for pdf_path in pdf_files:
            images_dir = os.path.join(self.temp_dir, f"size_images_{Path(pdf_path).stem}")
            
            result = self.converter.pdf_to_images(
                pdf_path=pdf_path,
                format='PNG',
                dpi=150,
                output_dir=images_dir
            )
            
            assert result.success is True
            all_images.extend(result.output_files)
        
        # Convert all images back to a single PDF with consistent page size
        combined_pdf = os.path.join(self.temp_dir, "combined_sizes.pdf")
        result = self.converter.images_to_pdf(
            image_paths=all_images,
            output_path=combined_pdf,
            page_size=(612, 792),  # Force Letter size
            fit_to_page=True,
            maintain_aspect_ratio=True
        )
        
        assert result.success is True
        assert os.path.exists(combined_pdf)
        
        # Verify all pages have the same size
        doc = fitz.open(combined_pdf)
        assert doc.page_count == 3
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            # Allow small tolerance for floating point precision
            assert abs(page.rect.width - 612) < 1
            assert abs(page.rect.height - 792) < 1
        
        doc.close()
    
    def test_error_handling_integration(self):
        """Test error handling when integrating with other components."""
        # Try to convert a corrupted PDF
        corrupted_pdf = os.path.join(self.temp_dir, "corrupted.pdf")
        with open(corrupted_pdf, 'w') as f:
            f.write("This is not a valid PDF file")
        
        # Format converter should handle the error gracefully
        result = self.converter.pdf_to_images(
            pdf_path=corrupted_pdf,
            format='PNG'
        )
        
        assert result.success is False
        assert len(result.errors) > 0
        
        # Try to use PDF operations on the result (should also fail with exception)
        from smart_pdf_toolkit.core.exceptions import ValidationError
        
        try:
            split_result = self.pdf_ops.split_pdf(
                input_file=corrupted_pdf,
                page_ranges=[(1, 1)]  # Use 1-indexed pages
            )
            # If we get here, the operation didn't fail as expected
            assert False, "Expected ValidationError to be raised"
        except ValidationError:
            # This is expected - the PDF operations should raise an exception for invalid files
            pass
    
    def test_memory_efficiency_with_large_batch(self):
        """Test memory efficiency when processing multiple files."""
        # Create several test PDFs
        pdf_files = []
        for i in range(5):  # Moderate number for testing
            pdf_path = os.path.join(self.temp_dir, f"memory_test_{i}.pdf")
            doc = fitz.open()
            # Create multiple pages to increase memory usage
            for j in range(3):
                page = doc.new_page()
                page.insert_text((50, 100), f"PDF {i}, Page {j + 1}", fontsize=20)
                # Add some shapes to increase complexity
                for k in range(10):
                    rect = fitz.Rect(50 + k * 20, 200, 70 + k * 20, 220)
                    page.draw_rect(rect, color=(k/10, 0, 1-k/10))
            doc.save(pdf_path)
            doc.close()
            pdf_files.append(pdf_path)
        
        # Process all files in batch
        batch_output_dir = os.path.join(self.temp_dir, "memory_test_output")
        
        result = self.converter.batch_convert_images(
            pdf_paths=pdf_files,
            output_base_dir=batch_output_dir,
            format='PNG'
        )
        
        assert result.success is True
        assert len(result.output_files) == 15  # 5 PDFs × 3 pages each
        
        # Verify all files were created successfully
        for output_file in result.output_files:
            assert os.path.exists(output_file)
            # Verify file is not empty
            assert os.path.getsize(output_file) > 0