"""
Content extraction implementation for Smart PDF Toolkit.
Provides text, image, table, metadata, and link extraction from PDF documents.
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass

import fitz  # PyMuPDF
import pdfplumber
from PIL import Image

from .interfaces import IContentExtractor, OperationResult
from .exceptions import PDFProcessingError, ValidationError, FileOperationError
from ..utils.validation import validate_pdf_file, validate_output_directory
from ..utils.file_utils import ensure_directory_exists, get_unique_filename


@dataclass
class TextExtractionResult:
    """Result of text extraction operation."""
    text: str
    page_count: int
    word_count: int
    character_count: int
    extraction_method: str
    layout_preserved: bool
    metadata: Dict[str, Any]


@dataclass
class ImageExtractionResult:
    """Result of image extraction operation."""
    image_files: List[str]
    image_count: int
    total_size_bytes: int
    formats_used: List[str]
    metadata: Dict[str, Any]


@dataclass
class TableExtractionResult:
    """Result of table extraction operation."""
    table_files: List[str]
    table_count: int
    format: str
    metadata: Dict[str, Any]


@dataclass
class MetadataResult:
    """Result of metadata extraction operation."""
    title: Optional[str]
    author: Optional[str]
    subject: Optional[str]
    creator: Optional[str]
    producer: Optional[str]
    creation_date: Optional[str]
    modification_date: Optional[str]
    keywords: Optional[str]
    page_count: int
    file_size: int
    is_encrypted: bool
    permissions: Dict[str, bool]
    additional_metadata: Dict[str, Any]


@dataclass
class LinkExtractionResult:
    """Result of link extraction operation."""
    internal_links: List[Dict[str, Any]]
    external_links: List[Dict[str, Any]]
    total_links: int
    metadata: Dict[str, Any]


class ContentExtractor(IContentExtractor):
    """
    Content extraction implementation using PyMuPDF and pdfplumber with fallback.
    
    This class provides comprehensive content extraction capabilities including:
    - Text extraction with layout preservation options
    - Image extraction in multiple formats
    - Table extraction with CSV/Excel output
    - Metadata extraction
    - Link extraction
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize ContentExtractor.
        
        Args:
            temp_dir: Temporary directory for intermediate files
        """
        self.temp_dir = temp_dir or os.path.join(os.getcwd(), "temp")
        self.logger = logging.getLogger(__name__)
        ensure_directory_exists(self.temp_dir)
    
    def extract_text(self, pdf_path: str, preserve_layout: bool = True, 
                    fallback_method: bool = True) -> OperationResult:
        """
        Extract text content from PDF using PyMuPDF with pdfplumber fallback.
        
        Args:
            pdf_path: Path to the PDF file
            preserve_layout: Whether to preserve text layout and formatting
            fallback_method: Whether to use pdfplumber as fallback if PyMuPDF fails
            
        Returns:
            OperationResult containing text extraction results
        """
        start_time = time.time()
        warnings = []
        errors = []
        
        try:
            # Validate input
            validate_pdf_file(pdf_path)
            
            # Try PyMuPDF first
            try:
                result = self._extract_text_pymupdf(pdf_path, preserve_layout)
                extraction_method = "PyMuPDF"
                self.logger.info(f"Text extracted using PyMuPDF from {pdf_path}")
                
            except Exception as e:
                if not fallback_method:
                    raise PDFProcessingError(f"PyMuPDF text extraction failed: {str(e)}")
                
                warnings.append(f"PyMuPDF extraction failed, using pdfplumber fallback: {str(e)}")
                self.logger.warning(f"PyMuPDF failed, falling back to pdfplumber: {str(e)}")
                
                # Fallback to pdfplumber
                result = self._extract_text_pdfplumber(pdf_path, preserve_layout)
                extraction_method = "pdfplumber (fallback)"
            
            # Create output file
            output_file = self._save_text_result(pdf_path, result.text)
            
            execution_time = time.time() - start_time
            
            return OperationResult(
                success=True,
                message=f"Text extracted successfully using {extraction_method}. "
                       f"Extracted {result.word_count} words from {result.page_count} pages.",
                output_files=[output_file],
                execution_time=execution_time,
                warnings=warnings,
                errors=errors
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Text extraction failed: {str(e)}"
            self.logger.error(error_msg)
            
            return OperationResult(
                success=False,
                message=error_msg,
                output_files=[],
                execution_time=execution_time,
                warnings=warnings,
                errors=[error_msg]
            )
    
    def _extract_text_pymupdf(self, pdf_path: str, preserve_layout: bool) -> TextExtractionResult:
        """Extract text using PyMuPDF."""
        doc = fitz.open(pdf_path)
        text_parts = []
        page_count = len(doc)
        
        try:
            for page_num in range(page_count):
                page = doc[page_num]
                
                if preserve_layout:
                    # Use text blocks to preserve layout
                    blocks = page.get_text("dict")
                    page_text = self._process_text_blocks(blocks)
                else:
                    # Simple text extraction
                    page_text = page.get_text()
                
                if page_text.strip():
                    text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}\n")
            
            full_text = "\n".join(text_parts)
            word_count = len(full_text.split())
            character_count = len(full_text)
            
            return TextExtractionResult(
                text=full_text,
                page_count=page_count,
                word_count=word_count,
                character_count=character_count,
                extraction_method="PyMuPDF",
                layout_preserved=preserve_layout,
                metadata={
                    "pages_with_text": len([p for p in text_parts if p.strip()]),
                    "average_words_per_page": word_count / page_count if page_count > 0 else 0
                }
            )
            
        finally:
            doc.close()
    
    def _extract_text_pdfplumber(self, pdf_path: str, preserve_layout: bool) -> TextExtractionResult:
        """Extract text using pdfplumber."""
        text_parts = []
        page_count = 0
        
        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages):
                if preserve_layout:
                    # Use layout-aware extraction
                    page_text = page.extract_text(layout=True)
                else:
                    # Simple text extraction
                    page_text = page.extract_text()
                
                if page_text and page_text.strip():
                    text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}\n")
        
        full_text = "\n".join(text_parts)
        word_count = len(full_text.split())
        character_count = len(full_text)
        
        return TextExtractionResult(
            text=full_text,
            page_count=page_count,
            word_count=word_count,
            character_count=character_count,
            extraction_method="pdfplumber",
            layout_preserved=preserve_layout,
            metadata={
                "pages_with_text": len([p for p in text_parts if p.strip()]),
                "average_words_per_page": word_count / page_count if page_count > 0 else 0
            }
        )
    
    def _process_text_blocks(self, blocks_dict: Dict) -> str:
        """Process PyMuPDF text blocks to preserve layout."""
        text_parts = []
        
        for block in blocks_dict.get("blocks", []):
            if "lines" in block:  # Text block
                block_text = []
                for line in block["lines"]:
                    line_text = []
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text:
                            line_text.append(text)
                    if line_text:
                        block_text.append(" ".join(line_text))
                
                if block_text:
                    text_parts.append("\n".join(block_text))
        
        return "\n\n".join(text_parts)
    
    def _save_text_result(self, pdf_path: str, text: str) -> str:
        """Save extracted text to file."""
        pdf_name = Path(pdf_path).stem
        output_file = os.path.join(self.temp_dir, f"{pdf_name}_extracted_text.txt")
        output_file = get_unique_filename(output_file)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        return output_file
    
    def extract_images(self, pdf_path: str, output_dir: str, 
                      formats: Optional[List[str]] = None) -> OperationResult:
        """
        Extract images from PDF in multiple formats.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted images
            formats: List of image formats to support (PNG, JPEG, TIFF)
            
        Returns:
            OperationResult containing image extraction results
        """
        start_time = time.time()
        warnings = []
        errors = []
        
        if formats is None:
            formats = ['PNG', 'JPEG']
        
        try:
            # Validate inputs
            validate_pdf_file(pdf_path)
            validate_output_directory(output_dir)
            ensure_directory_exists(output_dir)
            
            doc = fitz.open(pdf_path)
            extracted_images = []
            total_size = 0
            formats_used = set()
            
            try:
                pdf_name = Path(pdf_path).stem
                
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    image_list = page.get_images()
                    
                    for img_index, img in enumerate(image_list):
                        try:
                            # Get image data
                            xref = img[0]
                            pix = fitz.Pixmap(doc, xref)
                            
                            # Skip if image is too small or invalid
                            if pix.width < 10 or pix.height < 10:
                                pix = None
                                continue
                            
                            # Determine format and filename
                            if pix.n - pix.alpha < 4:  # GRAY or RGB
                                img_format = 'PNG' if 'PNG' in formats else formats[0]
                                ext = 'png' if img_format == 'PNG' else 'jpg'
                            else:  # CMYK
                                img_format = 'JPEG' if 'JPEG' in formats else formats[0]
                                ext = 'jpg'
                            
                            filename = f"{pdf_name}_page{page_num+1}_img{img_index+1}.{ext}"
                            img_path = os.path.join(output_dir, filename)
                            img_path = get_unique_filename(img_path)
                            
                            # Save image
                            if img_format == 'PNG':
                                pix.save(img_path)
                            else:
                                # Convert to RGB for JPEG
                                if pix.n == 4:  # CMYK
                                    pix = fitz.Pixmap(fitz.csRGB, pix)
                                pix.save(img_path)
                            
                            extracted_images.append(img_path)
                            total_size += os.path.getsize(img_path)
                            formats_used.add(img_format)
                            
                            pix = None  # Free memory
                            
                        except Exception as e:
                            warning_msg = f"Failed to extract image {img_index+1} from page {page_num+1}: {str(e)}"
                            warnings.append(warning_msg)
                            self.logger.warning(warning_msg)
            
            finally:
                doc.close()
            
            execution_time = time.time() - start_time
            
            if extracted_images:
                return OperationResult(
                    success=True,
                    message=f"Successfully extracted {len(extracted_images)} images. "
                           f"Total size: {total_size / 1024:.1f} KB",
                    output_files=extracted_images,
                    execution_time=execution_time,
                    warnings=warnings,
                    errors=errors
                )
            else:
                return OperationResult(
                    success=True,
                    message="No images found in the PDF document.",
                    output_files=[],
                    execution_time=execution_time,
                    warnings=warnings,
                    errors=errors
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Image extraction failed: {str(e)}"
            self.logger.error(error_msg)
            
            return OperationResult(
                success=False,
                message=error_msg,
                output_files=[],
                execution_time=execution_time,
                warnings=warnings,
                errors=[error_msg]
            )
    
    def extract_tables(self, pdf_path: str, format: str = 'csv', 
                      output_dir: Optional[str] = None) -> OperationResult:
        """
        Extract tables from PDF using pdfplumber.
        
        Args:
            pdf_path: Path to the PDF file
            format: Output format ('csv' or 'excel')
            output_dir: Directory to save table files (uses temp_dir if None)
            
        Returns:
            OperationResult containing table extraction results
        """
        start_time = time.time()
        warnings = []
        errors = []
        
        if output_dir is None:
            output_dir = self.temp_dir
        
        try:
            # Validate inputs
            validate_pdf_file(pdf_path)
            if format not in ['csv', 'excel']:
                raise ValidationError(f"Unsupported format: {format}. Use 'csv' or 'excel'.")
            
            ensure_directory_exists(output_dir)
            
            extracted_tables = []
            pdf_name = Path(pdf_path).stem
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        tables = page.extract_tables()
                        
                        for table_index, table in enumerate(tables):
                            if not table or len(table) < 2:  # Skip empty or single-row tables
                                continue
                            
                            # Create filename
                            if format == 'csv':
                                filename = f"{pdf_name}_page{page_num+1}_table{table_index+1}.csv"
                                table_path = os.path.join(output_dir, filename)
                                table_path = get_unique_filename(table_path)
                                
                                # Save as CSV
                                import csv
                                with open(table_path, 'w', newline='', encoding='utf-8') as csvfile:
                                    writer = csv.writer(csvfile)
                                    for row in table:
                                        # Clean None values
                                        cleaned_row = [cell if cell is not None else '' for cell in row]
                                        writer.writerow(cleaned_row)
                            
                            else:  # excel
                                filename = f"{pdf_name}_page{page_num+1}_table{table_index+1}.xlsx"
                                table_path = os.path.join(output_dir, filename)
                                table_path = get_unique_filename(table_path)
                                
                                # Save as Excel
                                try:
                                    import openpyxl
                                    from openpyxl import Workbook
                                    
                                    wb = Workbook()
                                    ws = wb.active
                                    ws.title = f"Table_Page_{page_num+1}"
                                    
                                    for row_index, row in enumerate(table, 1):
                                        for col_index, cell in enumerate(row, 1):
                                            ws.cell(row=row_index, column=col_index, 
                                                   value=cell if cell is not None else '')
                                    
                                    wb.save(table_path)
                                    
                                except ImportError:
                                    warnings.append("openpyxl not available, falling back to CSV format")
                                    # Fallback to CSV
                                    table_path = table_path.replace('.xlsx', '.csv')
                                    import csv
                                    with open(table_path, 'w', newline='', encoding='utf-8') as csvfile:
                                        writer = csv.writer(csvfile)
                                        for row in table:
                                            cleaned_row = [cell if cell is not None else '' for cell in row]
                                            writer.writerow(cleaned_row)
                            
                            extracted_tables.append(table_path)
                    
                    except Exception as e:
                        warning_msg = f"Failed to extract tables from page {page_num+1}: {str(e)}"
                        warnings.append(warning_msg)
                        self.logger.warning(warning_msg)
            
            execution_time = time.time() - start_time
            
            if extracted_tables:
                return OperationResult(
                    success=True,
                    message=f"Successfully extracted {len(extracted_tables)} tables in {format} format.",
                    output_files=extracted_tables,
                    execution_time=execution_time,
                    warnings=warnings,
                    errors=errors
                )
            else:
                return OperationResult(
                    success=True,
                    message="No tables found in the PDF document.",
                    output_files=[],
                    execution_time=execution_time,
                    warnings=warnings,
                    errors=errors
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Table extraction failed: {str(e)}"
            self.logger.error(error_msg)
            
            return OperationResult(
                success=False,
                message=error_msg,
                output_files=[],
                execution_time=execution_time,
                warnings=warnings,
                errors=[error_msg]
            )
    
    def extract_metadata(self, pdf_path: str) -> OperationResult:
        """
        Extract metadata from PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            OperationResult containing metadata extraction results
        """
        start_time = time.time()
        warnings = []
        errors = []
        
        try:
            # Validate input
            validate_pdf_file(pdf_path)
            
            doc = fitz.open(pdf_path)
            
            try:
                # Get basic metadata
                metadata = doc.metadata
                page_count = len(doc)
                file_size = os.path.getsize(pdf_path)
                is_encrypted = doc.needs_pass
                
                # Get permissions
                permissions = {
                    'print': not doc.is_pdf or doc.permissions & fitz.PDF_PERM_PRINT != 0,
                    'modify': not doc.is_pdf or doc.permissions & fitz.PDF_PERM_MODIFY != 0,
                    'copy': not doc.is_pdf or doc.permissions & fitz.PDF_PERM_COPY != 0,
                    'annotate': not doc.is_pdf or doc.permissions & fitz.PDF_PERM_ANNOTATE != 0,
                }
                
                # Create metadata result
                result = MetadataResult(
                    title=metadata.get('title'),
                    author=metadata.get('author'),
                    subject=metadata.get('subject'),
                    creator=metadata.get('creator'),
                    producer=metadata.get('producer'),
                    creation_date=metadata.get('creationDate'),
                    modification_date=metadata.get('modDate'),
                    keywords=metadata.get('keywords'),
                    page_count=page_count,
                    file_size=file_size,
                    is_encrypted=bool(is_encrypted),
                    permissions=permissions,
                    additional_metadata={k: v for k, v in metadata.items() 
                                       if k not in ['title', 'author', 'subject', 'creator', 
                                                   'producer', 'creationDate', 'modDate', 'keywords']}
                )
                
                # Save metadata to file
                output_file = self._save_metadata_result(pdf_path, result)
                
            finally:
                doc.close()
            
            execution_time = time.time() - start_time
            
            return OperationResult(
                success=True,
                message=f"Successfully extracted metadata. Document has {page_count} pages, "
                       f"size: {file_size / 1024:.1f} KB",
                output_files=[output_file],
                execution_time=execution_time,
                warnings=warnings,
                errors=errors
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Metadata extraction failed: {str(e)}"
            self.logger.error(error_msg)
            
            return OperationResult(
                success=False,
                message=error_msg,
                output_files=[],
                execution_time=execution_time,
                warnings=warnings,
                errors=[error_msg]
            )
    
    def extract_links(self, pdf_path: str) -> OperationResult:
        """
        Extract links from PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            OperationResult containing link extraction results
        """
        start_time = time.time()
        warnings = []
        errors = []
        
        try:
            # Validate input
            validate_pdf_file(pdf_path)
            
            doc = fitz.open(pdf_path)
            internal_links = []
            external_links = []
            
            try:
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    links = page.get_links()
                    
                    for link in links:
                        link_info = {
                            'page': page_num + 1,
                            'rect': link.get('from', {}),
                            'type': link.get('kind', 'unknown')
                        }
                        
                        if link.get('uri'):  # External link
                            link_info['url'] = link['uri']
                            external_links.append(link_info)
                        elif link.get('page') is not None:  # Internal link
                            link_info['target_page'] = link['page'] + 1
                            link_info['target_rect'] = link.get('to', {})
                            internal_links.append(link_info)
                
                # Create result
                result = LinkExtractionResult(
                    internal_links=internal_links,
                    external_links=external_links,
                    total_links=len(internal_links) + len(external_links),
                    metadata={
                        'internal_count': len(internal_links),
                        'external_count': len(external_links)
                    }
                )
                
                # Save links to file
                output_file = self._save_links_result(pdf_path, result)
                
            finally:
                doc.close()
            
            execution_time = time.time() - start_time
            
            return OperationResult(
                success=True,
                message=f"Successfully extracted {result.total_links} links "
                       f"({len(internal_links)} internal, {len(external_links)} external).",
                output_files=[output_file],
                execution_time=execution_time,
                warnings=warnings,
                errors=errors
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Link extraction failed: {str(e)}"
            self.logger.error(error_msg)
            
            return OperationResult(
                success=False,
                message=error_msg,
                output_files=[],
                execution_time=execution_time,
                warnings=warnings,
                errors=[error_msg]
            )
    
    def _save_metadata_result(self, pdf_path: str, metadata: MetadataResult) -> str:
        """Save metadata to JSON file."""
        import json
        
        pdf_name = Path(pdf_path).stem
        output_file = os.path.join(self.temp_dir, f"{pdf_name}_metadata.json")
        output_file = get_unique_filename(output_file)
        
        # Convert metadata to dict for JSON serialization
        metadata_dict = {
            'title': metadata.title,
            'author': metadata.author,
            'subject': metadata.subject,
            'creator': metadata.creator,
            'producer': metadata.producer,
            'creation_date': metadata.creation_date,
            'modification_date': metadata.modification_date,
            'keywords': metadata.keywords,
            'page_count': metadata.page_count,
            'file_size': metadata.file_size,
            'is_encrypted': metadata.is_encrypted,
            'permissions': metadata.permissions,
            'additional_metadata': metadata.additional_metadata
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, indent=2, ensure_ascii=False)
        
        return output_file
    
    def _save_links_result(self, pdf_path: str, links: LinkExtractionResult) -> str:
        """Save links to JSON file."""
        import json
        
        pdf_name = Path(pdf_path).stem
        output_file = os.path.join(self.temp_dir, f"{pdf_name}_links.json")
        output_file = get_unique_filename(output_file)
        
        # Convert links to dict for JSON serialization
        links_dict = {
            'internal_links': links.internal_links,
            'external_links': links.external_links,
            'total_links': links.total_links,
            'metadata': links.metadata
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(links_dict, f, indent=2, ensure_ascii=False)
        
        return output_file