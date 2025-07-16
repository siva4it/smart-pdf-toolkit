"""
Base interfaces and abstract classes for all major components.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class JobStatus(Enum):
    """Status enumeration for batch jobs."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OperationResult:
    """Standard result format for all operations."""
    success: bool
    message: str
    output_files: List[str]
    execution_time: float
    warnings: List[str]
    errors: List[str]


@dataclass
class PDFDocument:
    """Represents a PDF document with metadata."""
    path: str
    page_count: int
    file_size: int
    creation_date: datetime
    modification_date: datetime
    author: str
    title: str
    is_encrypted: bool
    permissions: Dict[str, bool]


@dataclass
class BatchJob:
    """Represents a batch processing job."""
    job_id: str
    operation: str
    status: JobStatus
    total_files: int
    processed_files: int
    failed_files: int
    created_at: datetime
    completed_at: Optional[datetime]
    results: List[OperationResult]


class IPDFOperations(ABC):
    """Interface for PDF manipulation operations."""
    
    @abstractmethod
    def merge_pdfs(self, input_files: List[str], output_file: str) -> OperationResult:
        """Merge multiple PDF files into a single document."""
        pass
    
    @abstractmethod
    def split_pdf(self, input_file: str, page_ranges: List[tuple]) -> OperationResult:
        """Split a PDF into separate documents based on page ranges."""
        pass
    
    @abstractmethod
    def rotate_pages(self, input_file: str, page_rotations: Dict[int, int]) -> OperationResult:
        """Rotate specific pages by specified degrees."""
        pass
    
    @abstractmethod
    def extract_pages(self, input_file: str, pages: List[int]) -> OperationResult:
        """Extract specific pages from a PDF."""
        pass
    
    @abstractmethod
    def reorder_pages(self, input_file: str, new_order: List[int]) -> OperationResult:
        """Reorder pages in a PDF document."""
        pass


class IContentExtractor(ABC):
    """Interface for content extraction operations."""
    
    @abstractmethod
    def extract_text(self, pdf_path: str, preserve_layout: bool = True) -> OperationResult:
        """Extract text content from PDF."""
        pass
    
    @abstractmethod
    def extract_images(self, pdf_path: str, output_dir: str) -> OperationResult:
        """Extract images from PDF."""
        pass
    
    @abstractmethod
    def extract_tables(self, pdf_path: str, format: str = 'csv') -> OperationResult:
        """Extract tables from PDF."""
        pass
    
    @abstractmethod
    def extract_metadata(self, pdf_path: str) -> OperationResult:
        """Extract metadata from PDF."""
        pass
    
    @abstractmethod
    def extract_links(self, pdf_path: str) -> OperationResult:
        """Extract links from PDF."""
        pass


class IOCRProcessor(ABC):
    """Interface for OCR operations."""
    
    @abstractmethod
    def perform_ocr(self, pdf_path: str, languages: List[str] = None) -> OperationResult:
        """Perform OCR on a PDF document."""
        pass
    
    @abstractmethod
    def detect_language(self, text: str) -> str:
        """Detect the language of text content."""
        pass
    
    @abstractmethod
    def get_confidence_scores(self, ocr_result: Any) -> Dict[int, float]:
        """Get confidence scores for OCR results."""
        pass


class IFormatConverter(ABC):
    """Interface for format conversion operations."""
    
    @abstractmethod
    def pdf_to_images(self, pdf_path: str, format: str, quality: int) -> OperationResult:
        """Convert PDF to images."""
        pass
    
    @abstractmethod
    def images_to_pdf(self, image_paths: List[str], output_path: str) -> OperationResult:
        """Convert images to PDF."""
        pass
    
    @abstractmethod
    def pdf_to_office(self, pdf_path: str, target_format: str) -> OperationResult:
        """Convert PDF to Office formats."""
        pass
    
    @abstractmethod
    def html_to_pdf(self, html_content: str, output_path: str) -> OperationResult:
        """Convert HTML to PDF."""
        pass
    
    @abstractmethod
    def office_to_pdf(self, input_path: str, output_path: str) -> OperationResult:
        """Convert Office documents to PDF."""
        pass


class ISecurityManager(ABC):
    """Interface for PDF security operations."""
    
    @abstractmethod
    def add_password(self, pdf_path: str, user_pwd: str, owner_pwd: str = None) -> OperationResult:
        """Add password protection to PDF."""
        pass
    
    @abstractmethod
    def remove_password(self, pdf_path: str, password: str) -> OperationResult:
        """Remove password protection from PDF."""
        pass
    
    @abstractmethod
    def set_permissions(self, pdf_path: str, permissions: Dict[str, bool]) -> OperationResult:
        """Set permissions for PDF document."""
        pass
    
    @abstractmethod
    def add_watermark(self, pdf_path: str, watermark_config: Dict[str, Any]) -> OperationResult:
        """Add watermark to PDF."""
        pass


class IOptimizationEngine(ABC):
    """Interface for PDF optimization operations."""
    
    @abstractmethod
    def compress_pdf(self, pdf_path: str, compression_level: int) -> OperationResult:
        """Compress PDF file."""
        pass
    
    @abstractmethod
    def optimize_for_web(self, pdf_path: str) -> OperationResult:
        """Optimize PDF for web viewing."""
        pass
    
    @abstractmethod
    def optimize_images(self, pdf_path: str, quality: int) -> OperationResult:
        """Optimize images within PDF."""
        pass


class IAIServices(ABC):
    """Interface for AI-powered features."""
    
    @abstractmethod
    def summarize_document(self, pdf_path: str, summary_length: int) -> OperationResult:
        """Generate document summary."""
        pass
    
    @abstractmethod
    def answer_question(self, pdf_path: str, question: str) -> OperationResult:
        """Answer questions about document content."""
        pass
    
    @abstractmethod
    def analyze_content(self, pdf_path: str) -> OperationResult:
        """Analyze document content for topics and themes."""
        pass
    
    @abstractmethod
    def classify_document(self, pdf_path: str) -> OperationResult:
        """Classify document based on content."""
        pass
    
    @abstractmethod
    def translate_content(self, pdf_path: str, target_language: str, preserve_formatting: bool = True) -> OperationResult:
        """Translate PDF content while preserving formatting."""
        pass


class IBatchProcessor(ABC):
    """Interface for batch processing operations."""
    
    @abstractmethod
    def create_batch_job(self, operation: str, files: List[str], params: Dict[str, Any]) -> BatchJob:
        """Create a new batch processing job."""
        pass
    
    @abstractmethod
    def get_batch_status(self, job_id: str) -> BatchJob:
        """Get status of a batch job."""
        pass
    
    @abstractmethod
    def cancel_batch_job(self, job_id: str) -> bool:
        """Cancel a running batch job."""
        pass


class IPlugin(ABC):
    """Base interface for plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with configuration."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass