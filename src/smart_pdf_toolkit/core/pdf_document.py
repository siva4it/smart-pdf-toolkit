"""
PDF Document model and validation functionality.
"""

import os
import fitz  # PyMuPDF
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from .interfaces import PDFDocument
from .exceptions import ValidationError, FileOperationError, PDFProcessingError


class PDFDocumentValidator:
    """Validates PDF files and extracts metadata."""
    
    @staticmethod
    def validate_pdf_file(file_path: str) -> bool:
        """
        Validate if a file is a valid PDF.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            True if valid PDF, False otherwise
            
        Raises:
            ValidationError: If file validation fails
        """
        if not file_path:
            raise ValidationError("File path cannot be empty")
        
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            raise ValidationError(f"File does not exist: {file_path}")
        
        # Check if it's a file (not directory)
        if not path.is_file():
            raise ValidationError(f"Path is not a file: {file_path}")
        
        # Check file extension
        if path.suffix.lower() != '.pdf':
            raise ValidationError(f"File is not a PDF: {file_path}")
        
        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            raise ValidationError(f"File is not readable: {file_path}")
        
        # Try to open with PyMuPDF to validate PDF structure
        try:
            doc = fitz.open(file_path)
            if doc.is_pdf:
                doc.close()
                return True
            else:
                doc.close()
                raise ValidationError(f"File is not a valid PDF: {file_path}")
        except Exception as e:
            raise ValidationError(f"Failed to validate PDF file: {str(e)}")
    
    @staticmethod
    def check_pdf_integrity(file_path: str) -> Dict[str, Any]:
        """
        Check PDF file integrity and return detailed information.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary with integrity check results
            
        Raises:
            PDFProcessingError: If integrity check fails
        """
        try:
            doc = fitz.open(file_path)
            
            integrity_info = {
                'is_valid': True,
                'is_encrypted': doc.needs_pass,
                'is_damaged': False,
                'page_count': doc.page_count,
                'has_xref_errors': False,
                'warnings': [],
                'errors': []
            }
            
            # Check for damaged pages
            try:
                for page_num in range(doc.page_count):
                    page = doc[page_num]
                    # Try to get page content to check if page is accessible
                    _ = page.get_text()
            except Exception as e:
                integrity_info['is_damaged'] = True
                integrity_info['errors'].append(f"Damaged page detected: {str(e)}")
            
            # Check for XRef errors (common in corrupted PDFs)
            if doc.xref_length() == 0:
                integrity_info['has_xref_errors'] = True
                integrity_info['warnings'].append("XRef table issues detected")
            
            doc.close()
            return integrity_info
            
        except Exception as e:
            raise PDFProcessingError(f"Failed to check PDF integrity: {str(e)}")
    
    @staticmethod
    def extract_metadata(file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing PDF metadata
            
        Raises:
            PDFProcessingError: If metadata extraction fails
        """
        try:
            doc = fitz.open(file_path)
            metadata = doc.metadata
            
            # Get file system information
            file_stat = os.stat(file_path)
            
            extracted_metadata = {
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'creator': metadata.get('creator', ''),
                'producer': metadata.get('producer', ''),
                'creation_date': metadata.get('creationDate', ''),
                'modification_date': metadata.get('modDate', ''),
                'keywords': metadata.get('keywords', ''),
                'file_size': file_stat.st_size,
                'page_count': doc.page_count,
                'is_encrypted': doc.needs_pass,
                'permissions': PDFDocumentValidator._extract_permissions(doc)
            }
            
            doc.close()
            return extracted_metadata
            
        except Exception as e:
            raise PDFProcessingError(f"Failed to extract metadata: {str(e)}")
    
    @staticmethod
    def _extract_permissions(doc: fitz.Document) -> Dict[str, bool]:
        """Extract permission information from PDF document."""
        try:
            permissions = {
                'print': True,
                'modify': True,
                'copy': True,
                'annotate': True,
                'form': True,
                'accessibility': True,
                'assemble': True,
                'print_high_quality': True
            }
            
            # If document is encrypted, check actual permissions
            if doc.needs_pass:
                # Note: Without password, we can't determine exact permissions
                # This would need to be enhanced when password is provided
                permissions = {key: False for key in permissions}
            
            return permissions
        except Exception:
            # Return default permissions if extraction fails
            return {
                'print': True,
                'modify': True,
                'copy': True,
                'annotate': True,
                'form': True,
                'accessibility': True,
                'assemble': True,
                'print_high_quality': True
            }


class PDFDocumentFactory:
    """Factory class for creating PDFDocument instances."""
    
    @staticmethod
    def create_from_file(file_path: str) -> PDFDocument:
        """
        Create a PDFDocument instance from a file path.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            PDFDocument instance
            
        Raises:
            ValidationError: If file validation fails
            PDFProcessingError: If document creation fails
        """
        # Validate the PDF file
        PDFDocumentValidator.validate_pdf_file(file_path)
        
        # Extract metadata
        metadata = PDFDocumentValidator.extract_metadata(file_path)
        
        # Parse dates
        creation_date = PDFDocumentFactory._parse_pdf_date(
            metadata.get('creation_date', '')
        )
        modification_date = PDFDocumentFactory._parse_pdf_date(
            metadata.get('modification_date', '')
        )
        
        # Create PDFDocument instance
        return PDFDocument(
            path=str(Path(file_path).resolve()),
            page_count=metadata['page_count'],
            file_size=metadata['file_size'],
            creation_date=creation_date,
            modification_date=modification_date,
            author=metadata.get('author', ''),
            title=metadata.get('title', ''),
            is_encrypted=metadata['is_encrypted'],
            permissions=metadata['permissions']
        )
    
    @staticmethod
    def _parse_pdf_date(date_string: str) -> datetime:
        """
        Parse PDF date string to datetime object.
        
        PDF dates are typically in format: D:YYYYMMDDHHmmSSOHH'mm'
        """
        if not date_string:
            return datetime.now()
        
        try:
            # Remove 'D:' prefix if present
            if date_string.startswith('D:'):
                date_string = date_string[2:]
            
            # Extract basic date components (YYYYMMDDHHMMSS)
            if len(date_string) >= 14:
                year = int(date_string[0:4])
                month = int(date_string[4:6])
                day = int(date_string[6:8])
                hour = int(date_string[8:10])
                minute = int(date_string[10:12])
                second = int(date_string[12:14])
                
                return datetime(year, month, day, hour, minute, second)
            elif len(date_string) >= 8:
                # Date only
                year = int(date_string[0:4])
                month = int(date_string[4:6])
                day = int(date_string[6:8])
                
                return datetime(year, month, day)
            else:
                return datetime.now()
                
        except (ValueError, IndexError):
            # If parsing fails, return current datetime
            return datetime.now()


def validate_pdf_files(file_paths: List[str]) -> Dict[str, Any]:
    """
    Validate multiple PDF files and return results.
    
    Args:
        file_paths: List of PDF file paths
        
    Returns:
        Dictionary with validation results for each file
    """
    results = {
        'valid_files': [],
        'invalid_files': [],
        'errors': {}
    }
    
    for file_path in file_paths:
        try:
            if PDFDocumentValidator.validate_pdf_file(file_path):
                results['valid_files'].append(file_path)
        except ValidationError as e:
            results['invalid_files'].append(file_path)
            results['errors'][file_path] = str(e)
        except Exception as e:
            results['invalid_files'].append(file_path)
            results['errors'][file_path] = f"Unexpected error: {str(e)}"
    
    return results