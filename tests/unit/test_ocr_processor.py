"""
Unit tests for OCR processor functionality.
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import pytest

from smart_pdf_toolkit.core.ocr_processor import OCRProcessor, OCRResult
from smart_pdf_toolkit.core.exceptions import OCRError
from smart_pdf_toolkit.core.interfaces import OperationResult


class TestOCRProcessor(unittest.TestCase):
    """Test cases for OCRProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock tesseract installation check
        with patch('smart_pdf_toolkit.core.ocr_processor.pytesseract.get_tesseract_version'):
            self.processor = OCRProcessor()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a simple test image
        self.test_image = Image.new('RGB', (100, 50), color='white')
        
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('smart_pdf_toolkit.core.ocr_processor.pytesseract.get_tesseract_version')
    def test_init_success(self, mock_version):
        """Test successful initialization."""
        mock_version.return_value = "5.0.0"
        
        config = {
            'default_languages': ['eng', 'fra'],
            'preprocessing_enabled': False,
            'confidence_threshold': 70.0
        }
        
        processor = OCRProcessor(config)
        
        self.assertEqual(processor.default_languages, ['eng', 'fra'])
        self.assertFalse(processor.preprocessing_enabled)
        self.assertEqual(processor.confidence_threshold, 70.0)
    
    @patch('smart_pdf_toolkit.core.ocr_processor.pytesseract.get_tesseract_version')
    def test_init_tesseract_not_found(self, mock_version):
        """Test initialization when tesseract is not found."""
        mock_version.side_effect = Exception("Tesseract not found")
        
        with self.assertRaises(OCRError) as context:
            OCRProcessor()
        
        self.assertIn("Tesseract not found", str(context.exception))
    
    def test_detect_language_english(self):
        """Test language detection for English text."""
        english_text = "This is a sample English text for testing language detection."
        
        with patch('smart_pdf_toolkit.core.ocr_processor.detect') as mock_detect:
            mock_detect.return_value = 'en'
            
            result = self.processor.detect_language(english_text)
            
            self.assertEqual(result, 'en')
            mock_detect.assert_called_once()
    
    def test_detect_language_empty_text(self):
        """Test language detection with empty text."""
        result = self.processor.detect_language("")
        self.assertEqual(result, 'unknown')
        
        result = self.processor.detect_language("   ")
        self.assertEqual(result, 'unknown')
    
    def test_detect_language_short_text(self):
        """Test language detection with very short text."""
        result = self.processor.detect_language("Hi")
        self.assertEqual(result, 'unknown')
    
    def test_detect_language_exception(self):
        """Test language detection when detection fails."""
        with patch('smart_pdf_toolkit.core.ocr_processor.detect') as mock_detect:
            from langdetect.lang_detect_exception import LangDetectException
            mock_detect.side_effect = LangDetectException("Detection failed", "")
            
            result = self.processor.detect_language("Some text")
            
            self.assertEqual(result, 'unknown')
    
    def test_get_confidence_scores(self):
        """Test getting confidence scores from OCR result."""
        ocr_result = OCRResult(
            text="Sample text",
            confidence_scores={1: 85.5, 2: 92.3},
            detected_language='en',
            page_count=2,
            processing_time=1.5,
            warnings=[]
        )
        
        scores = self.processor.get_confidence_scores(ocr_result)
        
        self.assertEqual(scores, {1: 85.5, 2: 92.3})
    
    def test_get_confidence_scores_invalid_input(self):
        """Test getting confidence scores with invalid input."""
        scores = self.processor.get_confidence_scores("invalid")
        self.assertEqual(scores, {})
    
    @patch('smart_pdf_toolkit.core.ocr_processor.fitz.open')
    def test_extract_pdf_images_success(self, mock_fitz_open):
        """Test successful PDF image extraction."""
        # Mock PyMuPDF document
        mock_doc = Mock()
        mock_page = Mock()
        mock_pixmap = Mock()
        
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.load_page.return_value = mock_page
        mock_page.get_pixmap.return_value = mock_pixmap
        mock_pixmap.tobytes.return_value = b'fake_png_data'
        mock_fitz_open.return_value = mock_doc
        
        # Mock PIL Image
        with patch('smart_pdf_toolkit.core.ocr_processor.Image.open') as mock_image_open:
            mock_image = Mock()
            mock_image.copy.return_value = self.test_image
            mock_image_open.return_value = mock_image
            
            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp_file = MagicMock()
                mock_temp_file.name = '/tmp/test.png'
                mock_temp_file.__enter__ = Mock(return_value=mock_temp_file)
                mock_temp_file.__exit__ = Mock(return_value=None)
                mock_temp.return_value = mock_temp_file
                
                with patch('os.unlink'):
                    images = self.processor._extract_pdf_images('test.pdf')
                    
                    self.assertEqual(len(images), 1)
                    mock_doc.close.assert_called_once()
    
    @patch('smart_pdf_toolkit.core.ocr_processor.fitz.open')
    def test_extract_pdf_images_failure(self, mock_fitz_open):
        """Test PDF image extraction failure."""
        mock_fitz_open.side_effect = Exception("Failed to open PDF")
        
        with self.assertRaises(OCRError) as context:
            self.processor._extract_pdf_images('test.pdf')
        
        self.assertIn("Failed to extract images", str(context.exception))
    
    def test_preprocess_image(self):
        """Test image preprocessing."""
        # Create a test image
        test_image = Image.new('RGB', (500, 300), color='gray')
        
        processed = self.processor._preprocess_image(test_image)
        
        # Should be converted to grayscale
        self.assertEqual(processed.mode, 'L')
        
        # Should be resized to at least 1000px on larger dimension
        width, height = processed.size
        self.assertTrue(width >= 1000 or height >= 1000)
    
    def test_preprocess_image_exception(self):
        """Test image preprocessing with exception."""
        # Mock an image that will cause preprocessing to fail
        mock_image = Mock()
        mock_image.mode = 'RGB'
        mock_image.convert.side_effect = Exception("Conversion failed")
        
        # Should return original image on failure
        result = self.processor._preprocess_image(mock_image)
        self.assertEqual(result, mock_image)
    
    def test_extract_text_and_confidence(self):
        """Test text and confidence extraction from OCR data."""
        ocr_data = {
            'text': ['', 'Hello', '', 'World', '!', ''],
            'conf': [-1, 85, 0, 92, 78, -1]
        }
        
        text, confidence = self.processor._extract_text_and_confidence(ocr_data)
        
        self.assertEqual(text, 'Hello World !')
        self.assertAlmostEqual(confidence, (85 + 92 + 78) / 3, places=1)
    
    def test_extract_text_and_confidence_no_text(self):
        """Test text extraction when no valid text is found."""
        ocr_data = {
            'text': ['', '', ''],
            'conf': [-1, 0, -1]
        }
        
        text, confidence = self.processor._extract_text_and_confidence(ocr_data)
        
        self.assertEqual(text, '')
        self.assertEqual(confidence, 0.0)
    
    @patch('builtins.open', create=True)
    def test_save_ocr_result(self, mock_open):
        """Test saving OCR result to file."""
        ocr_result = OCRResult(
            text="Sample OCR text",
            confidence_scores={1: 85.5},
            detected_language='en',
            page_count=1,
            processing_time=1.5,
            warnings=['Warning message']
        )
        
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        with patch('os.path.dirname') as mock_dirname, \
             patch('os.path.join') as mock_join, \
             patch('os.remove'):
            
            mock_dirname.return_value = '/test/dir'
            mock_join.return_value = '/test/dir/test_ocr.txt'
            
            result_path = self.processor._save_ocr_result('/test/dir/test.pdf', ocr_result)
            
            self.assertEqual(result_path, '/test/dir/test_ocr.txt')
            mock_file.write.assert_called()
    
    @patch('builtins.open', create=True)
    def test_save_ocr_result_permission_error(self, mock_open):
        """Test saving OCR result when original directory is not writable."""
        ocr_result = OCRResult(
            text="Sample OCR text",
            confidence_scores={1: 85.5},
            detected_language='en',
            page_count=1,
            processing_time=1.5,
            warnings=[]
        )
        
        # First open call (test write) should fail, second should succeed
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__ = Mock(return_value=Mock())
        mock_context_manager.__exit__ = Mock(return_value=None)
        mock_open.side_effect = [PermissionError("Permission denied"), mock_context_manager]
        
        with patch('os.path.dirname') as mock_dirname, \
             patch('os.path.join') as mock_join, \
             patch('tempfile.gettempdir') as mock_tempdir, \
             patch('os.remove'):
            
            mock_dirname.return_value = '/readonly/dir'
            mock_tempdir.return_value = '/tmp'
            mock_join.side_effect = ['/readonly/dir/test_ocr.txt', '/readonly/dir/.test_write', '/tmp/test_ocr.txt']
            
            result_path = self.processor._save_ocr_result('/readonly/dir/test.pdf', ocr_result)
            
            self.assertEqual(result_path, '/tmp/test_ocr.txt')
    
    @patch('smart_pdf_toolkit.core.ocr_processor.validate_file_exists')
    @patch('smart_pdf_toolkit.core.ocr_processor.validate_pdf_file')
    def test_perform_ocr_invalid_file(self, mock_validate_pdf, mock_validate_exists):
        """Test OCR with invalid file."""
        mock_validate_exists.side_effect = FileNotFoundError("File not found")
        
        result = self.processor.perform_ocr('nonexistent.pdf')
        
        self.assertFalse(result.success)
        self.assertIn("File not found", result.errors[0])
    
    @patch('smart_pdf_toolkit.core.ocr_processor.validate_file_exists')
    @patch('smart_pdf_toolkit.core.ocr_processor.validate_pdf_file')
    def test_perform_ocr_no_images(self, mock_validate_pdf, mock_validate_exists):
        """Test OCR when PDF contains no images."""
        with patch.object(self.processor, '_extract_pdf_images') as mock_extract:
            mock_extract.return_value = []
            
            result = self.processor.perform_ocr('test.pdf')
            
            self.assertFalse(result.success)
            self.assertIn("No images found", result.message)
    
    @patch('smart_pdf_toolkit.core.ocr_processor.validate_file_exists')
    @patch('smart_pdf_toolkit.core.ocr_processor.validate_pdf_file')
    @patch('smart_pdf_toolkit.core.ocr_processor.pytesseract.image_to_data')
    def test_perform_ocr_success(self, mock_ocr, mock_validate_pdf, mock_validate_exists):
        """Test successful OCR processing."""
        # Mock OCR data
        mock_ocr.return_value = {
            'text': ['Hello', 'World'],
            'conf': [85, 92]
        }
        
        with patch.object(self.processor, '_extract_pdf_images') as mock_extract, \
             patch.object(self.processor, '_preprocess_image') as mock_preprocess, \
             patch.object(self.processor, '_save_ocr_result') as mock_save, \
             patch.object(self.processor, 'detect_language') as mock_detect_lang:
            
            mock_extract.return_value = [self.test_image]
            mock_preprocess.return_value = self.test_image
            mock_save.return_value = '/tmp/test_ocr.txt'
            mock_detect_lang.return_value = 'en'
            
            result = self.processor.perform_ocr('test.pdf')
            
            self.assertTrue(result.success)
            self.assertEqual(len(result.output_files), 1)
            self.assertIn("OCR completed successfully", result.message)


class TestOCRProcessorIntegration(unittest.TestCase):
    """Integration tests for OCR processor."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        # Mock tesseract installation check
        with patch('smart_pdf_toolkit.core.ocr_processor.pytesseract.get_tesseract_version'):
            self.processor = OCRProcessor()
    
    @patch('smart_pdf_toolkit.core.ocr_processor.pytesseract.get_tesseract_version')
    def test_full_ocr_workflow_mock(self, mock_version):
        """Test full OCR workflow with mocked dependencies."""
        mock_version.return_value = "5.0.0"
        
        # This test would require actual PDF files and tesseract installation
        # For now, we'll test the workflow with mocks
        
        with patch('smart_pdf_toolkit.core.ocr_processor.validate_file_exists'), \
             patch('smart_pdf_toolkit.core.ocr_processor.validate_pdf_file'), \
             patch.object(self.processor, '_extract_pdf_images') as mock_extract, \
             patch('smart_pdf_toolkit.core.ocr_processor.pytesseract.image_to_data') as mock_ocr, \
             patch.object(self.processor, '_save_ocr_result') as mock_save:
            
            # Setup mocks
            test_image = Image.new('RGB', (100, 50), color='white')
            mock_extract.return_value = [test_image]
            mock_ocr.return_value = {
                'text': ['Sample', 'OCR', 'text'],
                'conf': [85, 90, 88]
            }
            mock_save.return_value = '/tmp/test_ocr.txt'
            
            result = self.processor.perform_ocr('test.pdf', languages=['eng'])
            
            self.assertTrue(result.success)
            self.assertGreater(result.execution_time, 0)
            mock_extract.assert_called_once_with('test.pdf')
            mock_ocr.assert_called_once()
            mock_save.assert_called_once()


if __name__ == '__main__':
    unittest.main()