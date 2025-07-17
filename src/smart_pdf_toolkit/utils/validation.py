"""
Input validation utilities.
"""

import os
from typing import List, Union, Optional
from pathlib import Path
from ..core.exceptions import ValidationError


class Validator:
    """Input validation utilities."""
    
    @staticmethod
    def validate_file_exists(file_path: Union[str, Path]) -> None:
        """Validate that a file exists.
        
        Args:
            file_path: Path to file
            
        Raises:
            ValidationError: If file doesn't exist
        """
        if not os.path.exists(file_path):
            raise ValidationError(f"File does not exist: {file_path}")
        
        if not os.path.isfile(file_path):
            raise ValidationError(f"Path is not a file: {file_path}")
    
    @staticmethod
    def validate_pdf_file(file_path: Union[str, Path]) -> None:
        """Validate that a file is a PDF.
        
        Args:
            file_path: Path to PDF file
            
        Raises:
            ValidationError: If file is not a valid PDF
        """
        Validator.validate_file_exists(file_path)
        
        path = Path(file_path)
        if path.suffix.lower() != '.pdf':
            raise ValidationError(f"File is not a PDF: {file_path}")
        
        if path.stat().st_size == 0:
            raise ValidationError(f"PDF file is empty: {file_path}")
    
    @staticmethod
    def validate_output_directory(directory: Union[str, Path]) -> None:
        """Validate that output directory is writable.
        
        Args:
            directory: Directory path
            
        Raises:
            ValidationError: If directory is not writable
        """
        dir_path = Path(directory)
        
        if dir_path.exists() and not dir_path.is_dir():
            raise ValidationError(f"Output path is not a directory: {directory}")
        
        # Try to create directory if it doesn't exist
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValidationError(f"Cannot create output directory {directory}: {str(e)}")
        
        # Check if directory is writable
        if not os.access(dir_path, os.W_OK):
            raise ValidationError(f"Output directory is not writable: {directory}")
    
    @staticmethod
    def validate_page_range(page_range: tuple, max_pages: int) -> None:
        """Validate page range.
        
        Args:
            page_range: Tuple of (start_page, end_page)
            max_pages: Maximum number of pages in document
            
        Raises:
            ValidationError: If page range is invalid
        """
        if not isinstance(page_range, tuple) or len(page_range) != 2:
            raise ValidationError("Page range must be a tuple of (start_page, end_page)")
        
        start_page, end_page = page_range
        
        if not isinstance(start_page, int) or not isinstance(end_page, int):
            raise ValidationError("Page numbers must be integers")
        
        if start_page < 1 or end_page < 1:
            raise ValidationError("Page numbers must be positive")
        
        if start_page > max_pages or end_page > max_pages:
            raise ValidationError(f"Page numbers cannot exceed document length ({max_pages})")
        
        if start_page > end_page:
            raise ValidationError("Start page cannot be greater than end page")
    
    @staticmethod
    def validate_page_list(pages: List[int], max_pages: int) -> None:
        """Validate list of page numbers.
        
        Args:
            pages: List of page numbers
            max_pages: Maximum number of pages in document
            
        Raises:
            ValidationError: If page list is invalid
        """
        if not isinstance(pages, list):
            raise ValidationError("Pages must be a list of integers")
        
        if not pages:
            raise ValidationError("Page list cannot be empty")
        
        for page in pages:
            if not isinstance(page, int):
                raise ValidationError("All page numbers must be integers")
            
            if page < 1 or page > max_pages:
                raise ValidationError(f"Page number {page} is out of range (1-{max_pages})")
    
    @staticmethod
    def validate_rotation_angle(angle: int) -> None:
        """Validate rotation angle.
        
        Args:
            angle: Rotation angle in degrees
            
        Raises:
            ValidationError: If angle is invalid
        """
        if angle not in [0, 90, 180, 270]:
            raise ValidationError("Rotation angle must be 0, 90, 180, or 270 degrees")
    
    @staticmethod
    def validate_compression_level(level: int) -> None:
        """Validate compression level.
        
        Args:
            level: Compression level (1-9)
            
        Raises:
            ValidationError: If level is invalid
        """
        if not isinstance(level, int) or level < 1 or level > 9:
            raise ValidationError("Compression level must be an integer between 1 and 9")
    
    @staticmethod
    def validate_image_format(format: str) -> None:
        """Validate image format.
        
        Args:
            format: Image format (png, jpg, jpeg, tiff)
            
        Raises:
            ValidationError: If format is invalid
        """
        valid_formats = ['png', 'jpg', 'jpeg', 'tiff', 'bmp']
        if format.lower() not in valid_formats:
            raise ValidationError(f"Invalid image format: {format}. Valid formats: {', '.join(valid_formats)}")
    
    @staticmethod
    def validate_file_size(file_path: Union[str, Path], max_size: Optional[int] = None) -> None:
        """Validate file size.
        
        Args:
            file_path: Path to file
            max_size: Maximum allowed file size in bytes
            
        Raises:
            ValidationError: If file is too large
        """
        if max_size is None:
            from ..core.config import config_manager
            config = config_manager.load_config()
            max_size = config.max_file_size
        
        file_size = os.path.getsize(file_path)
        if file_size > max_size:
            raise ValidationError(f"File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)")


# Convenience functions for common validations
def validate_file_exists(file_path: Union[str, Path]) -> None:
    """Validate that a file exists."""
    Validator.validate_file_exists(file_path)


def validate_pdf_file(file_path: Union[str, Path]) -> None:
    """Validate that a file is a PDF."""
    Validator.validate_pdf_file(file_path)


def validate_output_directory(directory: Union[str, Path]) -> None:
    """Validate that output directory is writable."""
    Validator.validate_output_directory(directory)


def validate_page_range(page_range: tuple, max_pages: int) -> None:
    """Validate page range."""
    Validator.validate_page_range(page_range, max_pages)


def validate_page_list(pages: List[int], max_pages: int) -> None:
    """Validate list of page numbers."""
    Validator.validate_page_list(pages, max_pages)


def validate_rotation_angle(angle: int) -> None:
    """Validate rotation angle."""
    Validator.validate_rotation_angle(angle)


def validate_compression_level(level: int) -> None:
    """Validate compression level."""
    Validator.validate_compression_level(level)


def validate_image_format(format: str) -> None:
    """Validate image format."""
    Validator.validate_image_format(format)


def validate_file_size(file_path: Union[str, Path], max_size: Optional[int] = None) -> None:
    """Validate file size."""
    Validator.validate_file_size(file_path, max_size)