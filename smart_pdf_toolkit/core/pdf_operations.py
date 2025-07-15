"""
PDF operations implementation for basic PDF manipulation tasks.
"""

import os
import time
import fitz  # PyMuPDF
from typing import List, Dict, Tuple
from pathlib import Path

from .interfaces import IPDFOperations, OperationResult
from .exceptions import PDFProcessingError, ValidationError, FileOperationError
from .pdf_document import PDFDocumentValidator


class PDFOperationsManager(IPDFOperations):
    """Implementation of basic PDF operations using PyMuPDF."""
    
    def __init__(self):
        """Initialize the PDF operations manager."""
        self.supported_rotations = [0, 90, 180, 270]
    
    def merge_pdfs(self, input_files: List[str], output_file: str) -> OperationResult:
        """
        Merge multiple PDF files into a single document.
        
        Args:
            input_files: List of paths to PDF files to merge
            output_file: Path for the output merged PDF file
            
        Returns:
            OperationResult with merge operation details
            
        Raises:
            ValidationError: If input validation fails
            PDFProcessingError: If merge operation fails
        """
        start_time = time.time()
        warnings = []
        errors = []
        
        try:
            # Validate inputs
            if not input_files:
                raise ValidationError("No input files provided for merge operation")
            
            if len(input_files) < 2:
                raise ValidationError("At least 2 PDF files are required for merge operation")
            
            if not output_file:
                raise ValidationError("Output file path is required")
            
            # Validate all input files
            for file_path in input_files:
                try:
                    PDFDocumentValidator.validate_pdf_file(file_path)
                except ValidationError as e:
                    errors.append(f"Invalid input file {file_path}: {str(e)}")
            
            if errors:
                raise ValidationError(f"Input validation failed: {'; '.join(errors)}")
            
            # Ensure output directory exists
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create merged document
            merged_doc = fitz.open()
            
            try:
                for file_path in input_files:
                    try:
                        source_doc = fitz.open(file_path)
                        merged_doc.insert_pdf(source_doc)
                        source_doc.close()
                    except Exception as e:
                        warnings.append(f"Warning processing {file_path}: {str(e)}")
                        continue
                
                # Save merged document
                merged_doc.save(output_file)
                merged_doc.close()
                
                # Verify output file was created
                if not os.path.exists(output_file):
                    raise FileOperationError("Failed to create output file")
                
                execution_time = time.time() - start_time
                
                return OperationResult(
                    success=True,
                    message=f"Successfully merged {len(input_files)} PDF files",
                    output_files=[output_file],
                    execution_time=execution_time,
                    warnings=warnings,
                    errors=[]
                )
                
            except Exception as e:
                merged_doc.close()
                raise PDFProcessingError(f"Failed to merge PDF files: {str(e)}")
                
        except (ValidationError, PDFProcessingError, FileOperationError):
            raise
        except Exception as e:
            execution_time = time.time() - start_time
            return OperationResult(
                success=False,
                message=f"Merge operation failed: {str(e)}",
                output_files=[],
                execution_time=execution_time,
                warnings=warnings,
                errors=[str(e)]
            )
    
    def split_pdf(self, input_file: str, page_ranges: List[Tuple[int, int]]) -> OperationResult:
        """
        Split a PDF into separate documents based on page ranges.
        
        Args:
            input_file: Path to the PDF file to split
            page_ranges: List of tuples (start_page, end_page) for each output file
                        Pages are 1-indexed
            
        Returns:
            OperationResult with split operation details
            
        Raises:
            ValidationError: If input validation fails
            PDFProcessingError: If split operation fails
        """
        start_time = time.time()
        warnings = []
        errors = []
        output_files = []
        
        try:
            # Validate inputs
            if not input_file:
                raise ValidationError("Input file path is required")
            
            if not page_ranges:
                raise ValidationError("Page ranges are required for split operation")
            
            # Validate input file
            PDFDocumentValidator.validate_pdf_file(input_file)
            
            # Open source document
            source_doc = fitz.open(input_file)
            total_pages = source_doc.page_count
            
            try:
                # Validate page ranges
                for i, (start_page, end_page) in enumerate(page_ranges):
                    if start_page < 1 or end_page < 1:
                        raise ValidationError(f"Page numbers must be >= 1 (range {i+1})")
                    
                    if start_page > total_pages or end_page > total_pages:
                        raise ValidationError(
                            f"Page range {i+1} ({start_page}-{end_page}) exceeds document pages ({total_pages})"
                        )
                    
                    if start_page > end_page:
                        raise ValidationError(f"Invalid page range {i+1}: start_page > end_page")
                
                # Create output files
                input_path = Path(input_file)
                base_name = input_path.stem
                output_dir = input_path.parent
                
                for i, (start_page, end_page) in enumerate(page_ranges):
                    try:
                        # Create new document for this range
                        output_doc = fitz.open()
                        
                        # Insert pages (convert to 0-indexed)
                        output_doc.insert_pdf(
                            source_doc, 
                            from_page=start_page - 1, 
                            to_page=end_page - 1
                        )
                        
                        # Generate output filename
                        output_file = output_dir / f"{base_name}_part_{i+1}_pages_{start_page}-{end_page}.pdf"
                        
                        # Save split document
                        output_doc.save(str(output_file))
                        output_doc.close()
                        
                        output_files.append(str(output_file))
                        
                    except Exception as e:
                        warnings.append(f"Failed to create split file {i+1}: {str(e)}")
                        continue
                
                source_doc.close()
                
                if not output_files:
                    raise PDFProcessingError("No split files were created successfully")
                
                execution_time = time.time() - start_time
                
                return OperationResult(
                    success=True,
                    message=f"Successfully split PDF into {len(output_files)} files",
                    output_files=output_files,
                    execution_time=execution_time,
                    warnings=warnings,
                    errors=[]
                )
                
            except (ValidationError, PDFProcessingError):
                source_doc.close()
                raise
            except Exception as e:
                source_doc.close()
                raise PDFProcessingError(f"Failed to split PDF: {str(e)}")
                
        except (ValidationError, PDFProcessingError):
            raise
        except Exception as e:
            execution_time = time.time() - start_time
            return OperationResult(
                success=False,
                message=f"Split operation failed: {str(e)}",
                output_files=output_files,
                execution_time=execution_time,
                warnings=warnings,
                errors=[str(e)]
            )
    
    def rotate_pages(self, input_file: str, page_rotations: Dict[int, int]) -> OperationResult:
        """
        Rotate specific pages by specified degrees.
        
        Args:
            input_file: Path to the PDF file
            page_rotations: Dictionary mapping page numbers (1-indexed) to rotation degrees
                           Supported rotations: 0, 90, 180, 270
            
        Returns:
            OperationResult with rotation operation details
            
        Raises:
            ValidationError: If input validation fails
            PDFProcessingError: If rotation operation fails
        """
        start_time = time.time()
        warnings = []
        errors = []
        
        try:
            # Validate inputs
            if not input_file:
                raise ValidationError("Input file path is required")
            
            if not page_rotations:
                raise ValidationError("Page rotations dictionary is required")
            
            # Validate input file
            PDFDocumentValidator.validate_pdf_file(input_file)
            
            # Open document
            doc = fitz.open(input_file)
            total_pages = doc.page_count
            
            try:
                # Validate page rotations
                for page_num, rotation in page_rotations.items():
                    if page_num < 1 or page_num > total_pages:
                        raise ValidationError(
                            f"Page number {page_num} is out of range (1-{total_pages})"
                        )
                    
                    if rotation not in self.supported_rotations:
                        raise ValidationError(
                            f"Unsupported rotation {rotation}. Supported: {self.supported_rotations}"
                        )
                
                # Apply rotations
                rotated_pages = []
                for page_num, rotation in page_rotations.items():
                    try:
                        page = doc[page_num - 1]  # Convert to 0-indexed
                        page.set_rotation(rotation)
                        rotated_pages.append(page_num)
                    except Exception as e:
                        warnings.append(f"Failed to rotate page {page_num}: {str(e)}")
                        continue
                
                if not rotated_pages:
                    raise PDFProcessingError("No pages were rotated successfully")
                
                # Create output filename
                input_path = Path(input_file)
                output_file = input_path.parent / f"{input_path.stem}_rotated{input_path.suffix}"
                
                # Save document with rotations
                doc.save(str(output_file))
                doc.close()
                
                execution_time = time.time() - start_time
                
                return OperationResult(
                    success=True,
                    message=f"Successfully rotated {len(rotated_pages)} pages",
                    output_files=[str(output_file)],
                    execution_time=execution_time,
                    warnings=warnings,
                    errors=[]
                )
                
            except (ValidationError, PDFProcessingError):
                doc.close()
                raise
            except Exception as e:
                doc.close()
                raise PDFProcessingError(f"Failed to rotate pages: {str(e)}")
                
        except (ValidationError, PDFProcessingError):
            raise
        except Exception as e:
            execution_time = time.time() - start_time
            return OperationResult(
                success=False,
                message=f"Rotation operation failed: {str(e)}",
                output_files=[],
                execution_time=execution_time,
                warnings=warnings,
                errors=[str(e)]
            )
    
    def extract_pages(self, input_file: str, pages: List[int]) -> OperationResult:
        """
        Extract specific pages from a PDF.
        
        Args:
            input_file: Path to the PDF file
            pages: List of page numbers to extract (1-indexed)
            
        Returns:
            OperationResult with extraction operation details
            
        Raises:
            ValidationError: If input validation fails
            PDFProcessingError: If extraction operation fails
        """
        start_time = time.time()
        warnings = []
        errors = []
        
        try:
            # Validate inputs
            if not input_file:
                raise ValidationError("Input file path is required")
            
            if not pages:
                raise ValidationError("Page list is required for extraction")
            
            # Validate input file
            PDFDocumentValidator.validate_pdf_file(input_file)
            
            # Open source document
            source_doc = fitz.open(input_file)
            total_pages = source_doc.page_count
            
            try:
                # Validate page numbers
                for page_num in pages:
                    if page_num < 1 or page_num > total_pages:
                        raise ValidationError(
                            f"Page number {page_num} is out of range (1-{total_pages})"
                        )
                
                # Remove duplicates and sort pages
                unique_pages = sorted(set(pages))
                
                # Create new document with extracted pages
                extracted_doc = fitz.open()
                
                for page_num in unique_pages:
                    try:
                        # Insert single page (convert to 0-indexed)
                        extracted_doc.insert_pdf(
                            source_doc,
                            from_page=page_num - 1,
                            to_page=page_num - 1
                        )
                    except Exception as e:
                        warnings.append(f"Failed to extract page {page_num}: {str(e)}")
                        continue
                
                # Generate output filename
                input_path = Path(input_file)
                pages_str = "_".join(map(str, unique_pages[:5]))  # Limit filename length
                if len(unique_pages) > 5:
                    pages_str += f"_and_{len(unique_pages)-5}_more"
                
                output_file = input_path.parent / f"{input_path.stem}_pages_{pages_str}{input_path.suffix}"
                
                # Save extracted document
                extracted_doc.save(str(output_file))
                extracted_doc.close()
                source_doc.close()
                
                execution_time = time.time() - start_time
                
                return OperationResult(
                    success=True,
                    message=f"Successfully extracted {len(unique_pages)} pages",
                    output_files=[str(output_file)],
                    execution_time=execution_time,
                    warnings=warnings,
                    errors=[]
                )
                
            except (ValidationError, PDFProcessingError):
                source_doc.close()
                raise
            except Exception as e:
                source_doc.close()
                raise PDFProcessingError(f"Failed to extract pages: {str(e)}")
                
        except (ValidationError, PDFProcessingError):
            raise
        except Exception as e:
            execution_time = time.time() - start_time
            return OperationResult(
                success=False,
                message=f"Page extraction failed: {str(e)}",
                output_files=[],
                execution_time=execution_time,
                warnings=warnings,
                errors=[str(e)]
            )
    
    def reorder_pages(self, input_file: str, new_order: List[int]) -> OperationResult:
        """
        Reorder pages in a PDF document.
        
        Args:
            input_file: Path to the PDF file
            new_order: List of page numbers in the desired order (1-indexed)
            
        Returns:
            OperationResult with reorder operation details
            
        Raises:
            ValidationError: If input validation fails
            PDFProcessingError: If reorder operation fails
        """
        start_time = time.time()
        warnings = []
        errors = []
        
        try:
            # Validate inputs
            if not input_file:
                raise ValidationError("Input file path is required")
            
            if not new_order:
                raise ValidationError("New page order is required")
            
            # Validate input file
            PDFDocumentValidator.validate_pdf_file(input_file)
            
            # Open source document
            source_doc = fitz.open(input_file)
            total_pages = source_doc.page_count
            
            try:
                # Validate new order
                if len(new_order) != total_pages:
                    raise ValidationError(
                        f"New order must contain all {total_pages} pages, got {len(new_order)}"
                    )
                
                for page_num in new_order:
                    if page_num < 1 or page_num > total_pages:
                        raise ValidationError(
                            f"Page number {page_num} is out of range (1-{total_pages})"
                        )
                
                # Check that all pages are included exactly once
                if set(new_order) != set(range(1, total_pages + 1)):
                    raise ValidationError("New order must contain each page exactly once")
                
                # Create new document with reordered pages
                reordered_doc = fitz.open()
                
                for page_num in new_order:
                    try:
                        # Insert page in new order (convert to 0-indexed)
                        reordered_doc.insert_pdf(
                            source_doc,
                            from_page=page_num - 1,
                            to_page=page_num - 1
                        )
                    except Exception as e:
                        warnings.append(f"Failed to reorder page {page_num}: {str(e)}")
                        continue
                
                # Generate output filename
                input_path = Path(input_file)
                output_file = input_path.parent / f"{input_path.stem}_reordered{input_path.suffix}"
                
                # Save reordered document
                reordered_doc.save(str(output_file))
                reordered_doc.close()
                source_doc.close()
                
                execution_time = time.time() - start_time
                
                return OperationResult(
                    success=True,
                    message=f"Successfully reordered {total_pages} pages",
                    output_files=[str(output_file)],
                    execution_time=execution_time,
                    warnings=warnings,
                    errors=[]
                )
                
            except (ValidationError, PDFProcessingError):
                source_doc.close()
                raise
            except Exception as e:
                source_doc.close()
                raise PDFProcessingError(f"Failed to reorder pages: {str(e)}")
                
        except (ValidationError, PDFProcessingError):
            raise
        except Exception as e:
            execution_time = time.time() - start_time
            return OperationResult(
                success=False,
                message=f"Page reorder failed: {str(e)}",
                output_files=[],
                execution_time=execution_time,
                warnings=warnings,
                errors=[str(e)]
            )