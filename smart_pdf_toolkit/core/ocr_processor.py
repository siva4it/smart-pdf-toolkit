"""
OCR processing module for extracting text from scanned PDFs.
"""

import os
import tempfile
import time
import re
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import fitz  # PyMuPDF
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

from .interfaces import IOCRProcessor, OperationResult
from .exceptions import OCRError
from ..utils.validation import validate_file_exists, validate_pdf_file


# Set seed for consistent language detection
DetectorFactory.seed = 0


class SearchMatch(NamedTuple):
    """Represents a search match in OCR text."""
    page_number: int
    start_position: int
    end_position: int
    matched_text: str
    context: str
    confidence: float


@dataclass
class QualityAssessment:
    """OCR quality assessment results."""
    overall_score: float
    page_scores: Dict[int, float]
    issues: List[str]
    suggestions: List[str]
    character_accuracy: float
    word_accuracy: float


@dataclass
class OCRResult:
    """Result of OCR processing."""
    text: str
    confidence_scores: Dict[int, float]
    detected_language: str
    page_count: int
    processing_time: float
    warnings: List[str]
    quality_assessment: Optional[QualityAssessment] = None


class OCRProcessor(IOCRProcessor):
    """OCR processor with tesseract integration."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize OCR processor with configuration."""
        self.config = config or {}
        self.default_languages = self.config.get('default_languages', ['eng'])
        self.preprocessing_enabled = self.config.get('preprocessing_enabled', True)
        self.confidence_threshold = self.config.get('confidence_threshold', 60.0)
        
        # Verify tesseract installation
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            raise OCRError(f"Tesseract not found or not properly installed: {e}")
    
    def perform_ocr(self, pdf_path: str, languages: List[str] = None) -> OperationResult:
        """
        Perform OCR on a PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            languages: List of language codes for OCR (e.g., ['eng', 'fra'])
            
        Returns:
            OperationResult with OCR text and metadata
        """
        start_time = time.time()
        
        try:
            # Validate input
            validate_file_exists(pdf_path)
            validate_pdf_file(pdf_path)
            
            # Use provided languages or defaults
            ocr_languages = languages or self.default_languages
            lang_string = '+'.join(ocr_languages)
            
            # Extract images from PDF
            images = self._extract_pdf_images(pdf_path)
            if not images:
                return OperationResult(
                    success=False,
                    message="No images found in PDF for OCR processing",
                    output_files=[],
                    execution_time=time.time() - start_time,
                    warnings=[],
                    errors=["PDF contains no extractable images"]
                )
            
            # Process each page
            all_text = []
            confidence_scores = {}
            warnings = []
            
            for page_num, image in enumerate(images, 1):
                try:
                    # Preprocess image if enabled
                    if self.preprocessing_enabled:
                        processed_image = self._preprocess_image(image)
                    else:
                        processed_image = image
                    
                    # Perform OCR with confidence data
                    ocr_data = pytesseract.image_to_data(
                        processed_image,
                        lang=lang_string,
                        output_type=pytesseract.Output.DICT
                    )
                    
                    # Extract text and calculate confidence
                    page_text, page_confidence = self._extract_text_and_confidence(ocr_data)
                    
                    if page_text.strip():
                        all_text.append(f"--- Page {page_num} ---\n{page_text}")
                        confidence_scores[page_num] = page_confidence
                    else:
                        warnings.append(f"No text extracted from page {page_num}")
                        confidence_scores[page_num] = 0.0
                        
                except Exception as e:
                    warnings.append(f"Error processing page {page_num}: {str(e)}")
                    confidence_scores[page_num] = 0.0
            
            # Combine all text
            full_text = '\n\n'.join(all_text)
            
            # Detect language if text was extracted
            detected_language = 'unknown'
            if full_text.strip():
                detected_language = self.detect_language(full_text)
            
            # Create OCR result
            ocr_result = OCRResult(
                text=full_text,
                confidence_scores=confidence_scores,
                detected_language=detected_language,
                page_count=len(images),
                processing_time=time.time() - start_time,
                warnings=warnings
            )
            
            # Save OCR result to temporary file
            output_file = self._save_ocr_result(pdf_path, ocr_result)
            
            return OperationResult(
                success=True,
                message=f"OCR completed successfully. Processed {len(images)} pages.",
                output_files=[output_file],
                execution_time=time.time() - start_time,
                warnings=warnings,
                errors=[]
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"OCR processing failed: {str(e)}",
                output_files=[],
                execution_time=time.time() - start_time,
                warnings=[],
                errors=[str(e)]
            )
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of text content.
        
        Args:
            text: Text content to analyze
            
        Returns:
            Language code (e.g., 'en', 'fr', 'de')
        """
        if not text or not text.strip():
            return 'unknown'
        
        try:
            # Use only first 1000 characters for detection to improve speed
            sample_text = text[:1000].strip()
            if len(sample_text) < 10:
                return 'unknown'
            
            detected = detect(sample_text)
            return detected
        except LangDetectException:
            return 'unknown'
        except Exception:
            return 'unknown'
    
    def get_confidence_scores(self, ocr_result: Any) -> Dict[int, float]:
        """
        Get confidence scores for OCR results.
        
        Args:
            ocr_result: OCR result object
            
        Returns:
            Dictionary mapping page numbers to confidence scores
        """
        if isinstance(ocr_result, OCRResult):
            return ocr_result.confidence_scores
        return {}
    
    def _extract_pdf_images(self, pdf_path: str) -> List[Image.Image]:
        """Extract images from PDF pages."""
        images = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Convert page to image
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR quality
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Convert to PIL Image
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                    temp_file.write(img_data)
                    temp_file.flush()
                    
                    image = Image.open(temp_file.name)
                    images.append(image.copy())
                    
                # Clean up temporary file
                os.unlink(temp_file.name)
            
            doc.close()
            
        except Exception as e:
            raise OCRError(f"Failed to extract images from PDF: {e}")
        
        return images
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR accuracy.
        
        Args:
            image: PIL Image to preprocess
            
        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # Apply slight blur to reduce noise
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            # Resize if image is too small (minimum 300 DPI equivalent)
            width, height = image.size
            if width < 1000 or height < 1000:
                scale_factor = max(1000 / width, 1000 / height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            # If preprocessing fails, return original image
            return image
    
    def _extract_text_and_confidence(self, ocr_data: Dict) -> Tuple[str, float]:
        """
        Extract text and calculate average confidence from OCR data.
        
        Args:
            ocr_data: OCR data dictionary from pytesseract
            
        Returns:
            Tuple of (extracted_text, average_confidence)
        """
        words = []
        confidences = []
        
        for i, conf in enumerate(ocr_data['conf']):
            if int(conf) > 0:  # Only include words with confidence > 0
                text = ocr_data['text'][i].strip()
                if text:
                    words.append(text)
                    confidences.append(float(conf))
        
        # Reconstruct text with proper spacing
        if not words:
            return "", 0.0
        
        # Simple text reconstruction (could be improved with layout analysis)
        text = ' '.join(words)
        
        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return text, avg_confidence
    
    def _save_ocr_result(self, pdf_path: str, ocr_result: OCRResult) -> str:
        """Save OCR result to a text file."""
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_file = f"{base_name}_ocr.txt"
        
        # Use temp directory if original directory is not writable
        try:
            output_dir = os.path.dirname(pdf_path)
            output_path = os.path.join(output_dir, output_file)
            
            # Test if directory is writable
            test_file = os.path.join(output_dir, '.test_write')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            
        except (OSError, PermissionError):
            # Use temp directory
            output_dir = tempfile.gettempdir()
            output_path = os.path.join(output_dir, output_file)
        
        # Write OCR result
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"OCR Results for: {os.path.basename(pdf_path)}\n")
            f.write(f"Processing Time: {ocr_result.processing_time:.2f} seconds\n")
            f.write(f"Detected Language: {ocr_result.detected_language}\n")
            f.write(f"Pages Processed: {ocr_result.page_count}\n")
            f.write(f"Average Confidence: {sum(ocr_result.confidence_scores.values()) / len(ocr_result.confidence_scores):.1f}%\n")
            f.write("\n" + "="*50 + "\n\n")
            f.write(ocr_result.text)
            
            if ocr_result.warnings:
                f.write("\n\n" + "="*50 + "\n")
                f.write("WARNINGS:\n")
                for warning in ocr_result.warnings:
                    f.write(f"- {warning}\n")
        
        return output_path