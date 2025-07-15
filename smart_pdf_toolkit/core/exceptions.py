"""
Core exception hierarchy for Smart PDF Toolkit.
"""

from typing import Optional, Dict, Any


class PDFToolkitError(Exception):
    """Base exception for all toolkit errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class PDFProcessingError(PDFToolkitError):
    """Errors during PDF processing operations."""
    pass


class SecurityError(PDFToolkitError):
    """Errors related to PDF security operations."""
    pass


class ConversionError(PDFToolkitError):
    """Errors during format conversion."""
    pass


class OCRError(PDFToolkitError):
    """Errors during OCR processing."""
    pass


class AIServiceError(PDFToolkitError):
    """Errors from AI service integration."""
    pass


class ConfigurationError(PDFToolkitError):
    """Errors related to configuration management."""
    pass


class PluginError(PDFToolkitError):
    """Errors related to plugin system."""
    pass


class ValidationError(PDFToolkitError):
    """Errors during input validation."""
    pass


class FileOperationError(PDFToolkitError):
    """Errors during file operations."""
    pass