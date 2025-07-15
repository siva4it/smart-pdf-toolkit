"""
Smart PDF Toolkit - A comprehensive Python application for PDF manipulation and analysis.
"""

__version__ = "0.1.0"
__author__ = "Smart PDF Toolkit Team"
__description__ = "Comprehensive PDF processing toolkit with AI-powered features"

# Core imports
from .core.config import config_manager, ApplicationConfig, PluginConfig
from .core.exceptions import (
    PDFToolkitError, PDFProcessingError, SecurityError, ConversionError,
    OCRError, AIServiceError, ConfigurationError, PluginError,
    ValidationError, FileOperationError
)
from .core.interfaces import (
    OperationResult, PDFDocument, BatchJob, JobStatus,
    IPDFOperations, IContentExtractor, IOCRProcessor, IFormatConverter,
    ISecurityManager, IOptimizationEngine, IAIServices, IBatchProcessor, IPlugin
)

# Utility imports
from .utils.file_utils import FileManager
from .utils.logging_utils import setup_logging, get_logger
from .utils.validation import Validator

# Plugin system
from .plugins.base import plugin_manager

__all__ = [
    # Version info
    '__version__', '__author__', '__description__',
    
    # Configuration
    'config_manager', 'ApplicationConfig', 'PluginConfig',
    
    # Exceptions
    'PDFToolkitError', 'PDFProcessingError', 'SecurityError', 'ConversionError',
    'OCRError', 'AIServiceError', 'ConfigurationError', 'PluginError',
    'ValidationError', 'FileOperationError',
    
    # Interfaces and data structures
    'OperationResult', 'PDFDocument', 'BatchJob', 'JobStatus',
    'IPDFOperations', 'IContentExtractor', 'IOCRProcessor', 'IFormatConverter',
    'ISecurityManager', 'IOptimizationEngine', 'IAIServices', 'IBatchProcessor', 'IPlugin',
    
    # Utilities
    'FileManager', 'setup_logging', 'get_logger', 'Validator',
    
    # Plugin system
    'plugin_manager'
]