"""
Service dependencies for the FastAPI application.
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Optional
from fastapi import UploadFile
from functools import lru_cache

from .config import get_api_config, get_core_config
from .models import FileUploadResponse
from ..core.pdf_operations import PDFOperationsManager
from ..core.content_extractor import ContentExtractor
from ..core.ai_services import AIServices
from ..core.batch_processor import BatchProcessor
from ..core.security_manager import SecurityManager
from ..core.optimization_engine import OptimizationEngine
from ..core.format_converter import FormatConverter
from ..core.ocr_processor import OCRProcessor


class FileManager:
    """
    File management service for handling uploads and file operations.
    """
    
    def __init__(self, config):
        self.config = config
        self.uploaded_files: Dict[str, str] = {}  # file_id -> file_path mapping
        self.output_files: Dict[str, str] = {}    # file_id -> file_path mapping
    
    async def save_uploaded_file(self, file: UploadFile) -> FileUploadResponse:
        """
        Save an uploaded file and return file information.
        
        Args:
            file: Uploaded file
            
        Returns:
            File upload response
        """
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Create file path
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.pdf'
        file_path = os.path.join(self.config.upload_dir, f"{file_id}{file_extension}")
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Store file mapping
        self.uploaded_files[file_id] = file_path
        
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename or f"upload{file_extension}",
            size=len(content),
            content_type=file.content_type or "application/pdf",
            upload_time=datetime.now()
        )
    
    async def get_file_path(self, file_id: str) -> Optional[str]:
        """
        Get file path from file ID.
        
        Args:
            file_id: File identifier
            
        Returns:
            File path or None if not found
        """
        return self.uploaded_files.get(file_id) or self.output_files.get(file_id)
    
    async def get_output_path(self, filename: str) -> str:
        """
        Generate output file path.
        
        Args:
            filename: Output filename
            
        Returns:
            Full output file path
        """
        return os.path.join(self.config.output_dir, filename)
    
    async def register_output_file(self, file_path: str) -> str:
        """
        Register an output file and return its ID.
        
        Args:
            file_path: Path to output file
            
        Returns:
            File ID for the output file
        """
        file_id = str(uuid.uuid4())
        self.output_files[file_id] = file_path
        return file_id


# Service instances (singletons)
_file_manager = None
_pdf_operations_service = None
_content_extractor_service = None
_ai_services_service = None
_batch_processor_service = None
_security_manager_service = None
_optimization_engine_service = None
_format_converter_service = None
_ocr_processor_service = None


@lru_cache()
def get_file_manager() -> FileManager:
    """Get file manager service instance."""
    global _file_manager
    if _file_manager is None:
        config = get_api_config()
        _file_manager = FileManager(config)
    return _file_manager


@lru_cache()
def get_pdf_operations_service() -> PDFOperationsManager:
    """Get PDF operations service instance."""
    global _pdf_operations_service
    if _pdf_operations_service is None:
        _pdf_operations_service = PDFOperationsManager()
    return _pdf_operations_service


@lru_cache()
def get_content_extractor_service() -> ContentExtractor:
    """Get content extractor service instance."""
    global _content_extractor_service
    if _content_extractor_service is None:
        config = get_core_config()
        _content_extractor_service = ContentExtractor(temp_dir=config['temp_directory'])
    return _content_extractor_service


@lru_cache()
def get_ai_services_service() -> AIServices:
    """Get AI services service instance."""
    global _ai_services_service
    if _ai_services_service is None:
        config = get_core_config()
        _ai_services_service = AIServices(config)
    return _ai_services_service


@lru_cache()
def get_batch_processor_service() -> BatchProcessor:
    """Get batch processor service instance."""
    global _batch_processor_service
    if _batch_processor_service is None:
        config = get_core_config()
        _batch_processor_service = BatchProcessor(config)
    return _batch_processor_service


@lru_cache()
def get_security_manager_service() -> SecurityManager:
    """Get security manager service instance."""
    global _security_manager_service
    if _security_manager_service is None:
        config = get_core_config()
        _security_manager_service = SecurityManager(config)
    return _security_manager_service


@lru_cache()
def get_optimization_engine_service() -> OptimizationEngine:
    """Get optimization engine service instance."""
    global _optimization_engine_service
    if _optimization_engine_service is None:
        config = get_core_config()
        _optimization_engine_service = OptimizationEngine(config)
    return _optimization_engine_service


@lru_cache()
def get_format_converter_service() -> FormatConverter:
    """Get format converter service instance."""
    global _format_converter_service
    if _format_converter_service is None:
        config = get_core_config()
        _format_converter_service = FormatConverter(config)
    return _format_converter_service


@lru_cache()
def get_ocr_processor_service() -> OCRProcessor:
    """Get OCR processor service instance."""
    global _ocr_processor_service
    if _ocr_processor_service is None:
        config = get_core_config()
        _ocr_processor_service = OCRProcessor(config)
    return _ocr_processor_service