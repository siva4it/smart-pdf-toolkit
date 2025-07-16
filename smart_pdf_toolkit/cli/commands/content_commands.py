"""
Content extraction CLI commands.
"""

import click
from pathlib import Path
from typing import Optional, List
import logging

from ...core.content_extraction import ContentExtractor
from ...core.ocr_processor import OCRProcessor
from ...core.exceptions import PDFToolkitError
from ..utils import validate_pdf_file, get_output_path, show_progress

logger = logging.getLogger(__name__)


@click.group()
def extract():
    """Content extraction operations."""
    pass


@extract.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(),
              help='Output text file path')
@click.option('--pages', '-p', 
              help='Pages to extract (e.g., "1,3,5-7")')
@click.option('--preserve-layout', is_flag=True,
              help='Preserve text layout and formatting')
@click.option('--include-metadata', is_flag=True,
              help='Include document metadata in output')
@click.pass_context
def text(ctx, file: str, output: Optional[str], pages: Optional[str], 
         preserve_layout: bool, include_metadata: bool):
    """
    Extract text content from a PDF file.
    
    FILE: PDF file to extract text from
    
    Examples:
        smart-pdf extract text document.pdf
        smart-pdf extract text document.pdf --pages "1-5" -o extracted.txt
        smart-pdf extract text document.pdf --preserve-layout
    """
    config = ctx.obj['config']
    
    try:
        # Validate input file
        pdf_file = validate_pdf_file(file)
        
        # Determine output path
        if not output:
            base_name = Path(pdf_file).stem
            output = get_output_path(config.output_dir, f"{base_name}_text.txt")
        
        # Parse page numbers if specified
        page_numbers = None
        if pages:
            page_numbers = _parse_page_numbers(pages)
        
        # Initialize content extractor
        extractor = ContentExtractor()
        
        # Show progress
        with show_progress("Extracting text", 1) as progress:
            # Perform text extraction
            result = extractor.extract_text(
                pdf_file,
                pages=page_numbers,
                preserve_layout=preserve_layout,
                include_metadata=include_metadata
            )
            progress.update(1)
        
        if result.success:
            # Save extracted text
            with open(output, 'w', encoding='utf-8') as f:
                f.write(result.content)
            
            click.echo(f"✓ Successfully extracted text to {output}")
            if not ctx.obj['quiet']:
                char_count = len(result.content)
                word_count = len(result.content.split())
                click.echo(f"  Characters: {char_count:,}")
                click.echo(f"  Words: {word_count:,}")
        else:
            raise PDFToolkitError(f"Text extraction failed: {result.error}")
            
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        raise click.ClickException(str(e))


@extract.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--output-dir', '-o', type=click.Path(),
              help='Output directory for extracted images')
@click.option('--pages', '-p',
              help='Pages to extract images from (e.g., "1,3,5-7")')
@click.option('--format', 'image_format', default='PNG',
              type=click.Choice(['PNG', 'JPEG', 'TIFF'], case_sensitive=False),
              help='Output image format')
@click.option('--quality', type=click.IntRange(1, 100), default=85,
              help='Image quality (1-100, for JPEG)')
@click.option('--min-size', type=int, default=100,
              help='Minimum image size in pixels')
@click.pass_context
def images(ctx, file: str, output_dir: Optional[str], pages: Optional[str],
           image_format: str, quality: int, min_size: int):
    """
    Extract images from a PDF file.
    
    FILE: PDF file to extract images from
    
    Examples:
        smart-pdf extract images document.pdf
        smart-pdf extract images document.pdf --pages "1-5" --format JPEG
        smart-pdf extract images document.pdf -o images/ --quality 95
    """
    config = ctx.obj['config']
    
    try:
        # Validate input file
        pdf_file = validate_pdf_file(file)
        
        # Determine output directory
        if not output_dir:
            base_name = Path(pdf_file).stem
            output_dir = Path(config.output_dir) / f"{base_name}_images"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Parse page numbers if specified
        page_numbers = None
        if pages:
            page_numbers = _parse_page_numbers(pages)
        
        # Initialize content extractor
        extractor = ContentExtractor()
        
        # Show progress
        with show_progress("Extracting images", 1) as progress:
            # Perform image extraction
            result = extractor.extract_images(
                pdf_file,
                output_dir=output_dir,
                pages=page_numbers,
                image_format=image_format.upper(),
                quality=quality,
                min_size=min_size
            )
            progress.update(1)
        
        if result.success:
            click.echo(f"✓ Successfully extracted {len(result.output_files)} images to {output_dir}")
            if not ctx.obj['quiet']:
                for image_file in result.output_files[:5]:  # Show first 5
                    click.echo(f"  Created: {Path(image_file).name}")
                if len(result.output_files) > 5:
                    click.echo(f"  ... and {len(result.output_files) - 5} more")
        else:
            raise PDFToolkitError(f"Image extraction failed: {result.error}")
            
    except Exception as e:
        logger.error(f"Image extraction failed: {e}")
        raise click.ClickException(str(e))


@extract.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(),
              help='Output CSV file path')
@click.option('--pages', '-p',
              help='Pages to extract tables from (e.g., "1,3,5-7")')
@click.option('--format', 'output_format', default='CSV',
              type=click.Choice(['CSV', 'Excel', 'JSON'], case_sensitive=False),
              help='Output format for tables')
@click.pass_context
def tables(ctx, file: str, output: Optional[str], pages: Optional[str], output_format: str):
    """
    Extract tables from a PDF file.
    
    FILE: PDF file to extract tables from
    
    Examples:
        smart-pdf extract tables document.pdf
        smart-pdf extract tables document.pdf --pages "1-5" --format Excel
        smart-pdf extract tables document.pdf -o tables.csv
    """
    config = ctx.obj['config']
    
    try:
        # Validate input file
        pdf_file = validate_pdf_file(file)
        
        # Determine output path
        if not output:
            base_name = Path(pdf_file).stem
            ext = {'CSV': '.csv', 'Excel': '.xlsx', 'JSON': '.json'}[output_format]
            output = get_output_path(config.output_dir, f"{base_name}_tables{ext}")
        
        # Parse page numbers if specified
        page_numbers = None
        if pages:
            page_numbers = _parse_page_numbers(pages)
        
        # Initialize content extractor
        extractor = ContentExtractor()
        
        # Show progress
        with show_progress("Extracting tables", 1) as progress:
            # Perform table extraction
            result = extractor.extract_tables(
                pdf_file,
                pages=page_numbers,
                output_format=output_format.lower()
            )
            progress.update(1)
        
        if result.success:
            # Save extracted tables
            if output_format.upper() == 'JSON':
                import json
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(result.content, f, indent=2)
            elif output_format.upper() == 'EXCEL':
                import pandas as pd
                with pd.ExcelWriter(output) as writer:
                    for i, table in enumerate(result.content):
                        df = pd.DataFrame(table)
                        df.to_excel(writer, sheet_name=f'Table_{i+1}', index=False)
            else:  # CSV
                import csv
                with open(output, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    for table in result.content:
                        for row in table:
                            writer.writerow(row)
                        writer.writerow([])  # Empty row between tables
            
            click.echo(f"✓ Successfully extracted {len(result.content)} tables to {output}")
            if not ctx.obj['quiet']:
                total_rows = sum(len(table) for table in result.content)
                click.echo(f"  Total rows: {total_rows}")
        else:
            raise PDFToolkitError(f"Table extraction failed: {result.error}")
            
    except Exception as e:
        logger.error(f"Table extraction failed: {e}")
        raise click.ClickException(str(e))


@extract.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(),
              help='Output text file path')
@click.option('--language', '-l', default='eng',
              help='OCR language (e.g., eng, fra, deu)')
@click.option('--pages', '-p',
              help='Pages to perform OCR on (e.g., "1,3,5-7")')
@click.option('--confidence-threshold', type=float, default=0.6,
              help='Minimum confidence threshold (0.0-1.0)')
@click.pass_context
def ocr(ctx, file: str, output: Optional[str], language: str, pages: Optional[str],
        confidence_threshold: float):
    """
    Perform OCR (Optical Character Recognition) on a PDF file.
    
    FILE: PDF file to perform OCR on
    
    Examples:
        smart-pdf extract ocr scanned.pdf
        smart-pdf extract ocr scanned.pdf --language fra --pages "1-5"
        smart-pdf extract ocr scanned.pdf -o ocr_text.txt --confidence-threshold 0.8
    """
    config = ctx.obj['config']
    
    try:
        # Validate input file
        pdf_file = validate_pdf_file(file)
        
        # Determine output path
        if not output:
            base_name = Path(pdf_file).stem
            output = get_output_path(config.output_dir, f"{base_name}_ocr.txt")
        
        # Parse page numbers if specified
        page_numbers = None
        if pages:
            page_numbers = _parse_page_numbers(pages)
        
        # Initialize OCR processor
        ocr_processor = OCRProcessor()
        
        # Show progress
        with show_progress("Performing OCR", 1) as progress:
            # Perform OCR
            result = ocr_processor.process_pdf(
                pdf_file,
                language=language,
                pages=page_numbers,
                confidence_threshold=confidence_threshold
            )
            progress.update(1)
        
        if result.success:
            # Save OCR text
            with open(output, 'w', encoding='utf-8') as f:
                f.write(result.text)
            
            click.echo(f"✓ Successfully performed OCR and saved to {output}")
            if not ctx.obj['quiet']:
                char_count = len(result.text)
                word_count = len(result.text.split())
                avg_confidence = result.confidence if hasattr(result, 'confidence') else 0
                click.echo(f"  Characters: {char_count:,}")
                click.echo(f"  Words: {word_count:,}")
                click.echo(f"  Average confidence: {avg_confidence:.2f}")
        else:
            raise PDFToolkitError(f"OCR failed: {result.error}")
            
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        raise click.ClickException(str(e))


def _parse_page_numbers(pages_str: str) -> List[int]:
    """Parse page numbers string into list of integers."""
    pages = []
    for part in pages_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = map(int, part.split('-'))
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    return pages