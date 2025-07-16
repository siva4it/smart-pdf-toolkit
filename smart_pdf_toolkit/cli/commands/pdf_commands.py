"""
PDF operations CLI commands.
"""

import click
from pathlib import Path
from typing import List, Optional, Tuple
import logging

from ...core.pdf_operations import PDFOperationsManager
from ...core.exceptions import PDFToolkitError
from ..utils import validate_pdf_file, get_output_path, show_progress
from ..completion import complete_pdf_files

logger = logging.getLogger(__name__)


@click.group()
def pdf():
    """PDF manipulation operations."""
    pass


@pdf.command()
@click.argument('files', nargs=-1, required=True, type=click.Path(exists=True), shell_complete=complete_pdf_files)
@click.option('--output', '-o', type=click.Path(), 
              help='Output file path')
@click.option('--bookmark-titles', multiple=True,
              help='Bookmark titles for each input file')
@click.pass_context
def merge(ctx, files: Tuple[str], output: Optional[str], bookmark_titles: Tuple[str]):
    """
    Merge multiple PDF files into a single document.
    
    FILES: One or more PDF files to merge
    
    Example:
        smart-pdf pdf merge file1.pdf file2.pdf -o merged.pdf
    """
    config = ctx.obj['config']
    
    try:
        # Validate input files
        pdf_files = []
        for file_path in files:
            validated_path = validate_pdf_file(file_path)
            pdf_files.append(validated_path)
        
        # Determine output path
        if not output:
            output = get_output_path(config.output_dir, "merged_document.pdf")
        
        # Initialize PDF operations manager
        pdf_manager = PDFOperationsManager()
        
        # Show progress
        with show_progress("Merging PDFs", len(pdf_files)) as progress:
            # Perform merge operation
            result = pdf_manager.merge_pdfs(
                pdf_files, 
                output,
                bookmark_titles=list(bookmark_titles) if bookmark_titles else None
            )
            progress.update(len(pdf_files))
        
        if result.success:
            click.echo(f"✓ Successfully merged {len(pdf_files)} files into {output}")
            if not ctx.obj['quiet']:
                click.echo(f"  Output size: {Path(output).stat().st_size // 1024}KB")
        else:
            raise PDFToolkitError(f"Merge failed: {result.error}")
            
    except Exception as e:
        logger.error(f"PDF merge failed: {e}")
        raise click.ClickException(str(e))


@pdf.command()
@click.argument('file', type=click.Path(exists=True), shell_complete=complete_pdf_files)
@click.option('--pages', '-p', help='Page ranges to split (e.g., "1-3,5,7-9")')
@click.option('--output-dir', '-o', type=click.Path(),
              help='Output directory for split files')
@click.option('--prefix', default='page',
              help='Prefix for output filenames')
@click.pass_context
def split(ctx, file: str, pages: Optional[str], output_dir: Optional[str], prefix: str):
    """
    Split a PDF file into multiple documents.
    
    FILE: PDF file to split
    
    Examples:
        smart-pdf pdf split document.pdf --pages "1-3,5,7-9"
        smart-pdf pdf split document.pdf -o split_output/
    """
    config = ctx.obj['config']
    
    try:
        # Validate input file
        pdf_file = validate_pdf_file(file)
        
        # Determine output directory
        if not output_dir:
            output_dir = config.output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Parse page ranges
        page_ranges = []
        if pages:
            page_ranges = _parse_page_ranges(pages)
        else:
            # Split each page individually
            pdf_manager = PDFOperationsManager()
            doc_info = pdf_manager.get_document_info(pdf_file)
            page_count = doc_info.get('page_count', 0)
            page_ranges = [(i, i) for i in range(1, page_count + 1)]
        
        # Initialize PDF operations manager
        pdf_manager = PDFOperationsManager()
        
        # Show progress
        with show_progress("Splitting PDF", len(page_ranges)) as progress:
            # Perform split operation
            result = pdf_manager.split_pdf(pdf_file, page_ranges, output_dir, prefix)
            progress.update(len(page_ranges))
        
        if result.success:
            click.echo(f"✓ Successfully split PDF into {len(result.output_files)} files")
            if not ctx.obj['quiet']:
                for output_file in result.output_files:
                    click.echo(f"  Created: {output_file}")
        else:
            raise PDFToolkitError(f"Split failed: {result.error}")
            
    except Exception as e:
        logger.error(f"PDF split failed: {e}")
        raise click.ClickException(str(e))


@pdf.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--pages', '-p', required=True,
              help='Pages to rotate with angles (e.g., "1:90,3:180,5-7:270")')
@click.option('--output', '-o', type=click.Path(),
              help='Output file path')
@click.pass_context
def rotate(ctx, file: str, pages: str, output: Optional[str]):
    """
    Rotate specific pages in a PDF document.
    
    FILE: PDF file to rotate pages in
    
    Examples:
        smart-pdf pdf rotate document.pdf --pages "1:90,3:180,5-7:270"
        smart-pdf pdf rotate document.pdf -p "all:90" -o rotated.pdf
    """
    config = ctx.obj['config']
    
    try:
        # Validate input file
        pdf_file = validate_pdf_file(file)
        
        # Determine output path
        if not output:
            base_name = Path(pdf_file).stem
            output = get_output_path(config.output_dir, f"{base_name}_rotated.pdf")
        
        # Parse page rotations
        page_rotations = _parse_page_rotations(pages)
        
        # Initialize PDF operations manager
        pdf_manager = PDFOperationsManager()
        
        # Show progress
        with show_progress("Rotating pages", len(page_rotations)) as progress:
            # Perform rotation operation
            result = pdf_manager.rotate_pages(pdf_file, page_rotations, output)
            progress.update(len(page_rotations))
        
        if result.success:
            click.echo(f"✓ Successfully rotated pages in {output}")
            if not ctx.obj['quiet']:
                rotated_pages = list(page_rotations.keys())
                click.echo(f"  Rotated pages: {rotated_pages}")
        else:
            raise PDFToolkitError(f"Rotation failed: {result.error}")
            
    except Exception as e:
        logger.error(f"PDF rotation failed: {e}")
        raise click.ClickException(str(e))


@pdf.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--pages', '-p', required=True,
              help='Pages to extract (e.g., "1,3,5-7")')
@click.option('--output', '-o', type=click.Path(),
              help='Output file path')
@click.pass_context
def extract(ctx, file: str, pages: str, output: Optional[str]):
    """
    Extract specific pages from a PDF document.
    
    FILE: PDF file to extract pages from
    
    Examples:
        smart-pdf pdf extract document.pdf --pages "1,3,5-7"
        smart-pdf pdf extract document.pdf -p "1-10" -o extracted.pdf
    """
    config = ctx.obj['config']
    
    try:
        # Validate input file
        pdf_file = validate_pdf_file(file)
        
        # Determine output path
        if not output:
            base_name = Path(pdf_file).stem
            output = get_output_path(config.output_dir, f"{base_name}_extracted.pdf")
        
        # Parse page numbers
        page_numbers = _parse_page_numbers(pages)
        
        # Initialize PDF operations manager
        pdf_manager = PDFOperationsManager()
        
        # Show progress
        with show_progress("Extracting pages", len(page_numbers)) as progress:
            # Perform extraction operation
            result = pdf_manager.extract_pages(pdf_file, page_numbers, output)
            progress.update(len(page_numbers))
        
        if result.success:
            click.echo(f"✓ Successfully extracted {len(page_numbers)} pages to {output}")
            if not ctx.obj['quiet']:
                click.echo(f"  Extracted pages: {sorted(page_numbers)}")
        else:
            raise PDFToolkitError(f"Extraction failed: {result.error}")
            
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise click.ClickException(str(e))


@pdf.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--order', '-o', required=True,
              help='New page order (e.g., "3,1,2,4-6")')
@click.option('--output', type=click.Path(),
              help='Output file path')
@click.pass_context
def reorder(ctx, file: str, order: str, output: Optional[str]):
    """
    Reorder pages in a PDF document.
    
    FILE: PDF file to reorder pages in
    
    Examples:
        smart-pdf pdf reorder document.pdf --order "3,1,2,4-6"
        smart-pdf pdf reorder document.pdf -o "2,1,3" --output reordered.pdf
    """
    config = ctx.obj['config']
    
    try:
        # Validate input file
        pdf_file = validate_pdf_file(file)
        
        # Determine output path
        if not output:
            base_name = Path(pdf_file).stem
            output = get_output_path(config.output_dir, f"{base_name}_reordered.pdf")
        
        # Parse new page order
        new_order = _parse_page_numbers(order)
        
        # Initialize PDF operations manager
        pdf_manager = PDFOperationsManager()
        
        # Show progress
        with show_progress("Reordering pages", len(new_order)) as progress:
            # Perform reorder operation
            result = pdf_manager.reorder_pages(pdf_file, new_order, output)
            progress.update(len(new_order))
        
        if result.success:
            click.echo(f"✓ Successfully reordered pages in {output}")
            if not ctx.obj['quiet']:
                click.echo(f"  New page order: {new_order}")
        else:
            raise PDFToolkitError(f"Reordering failed: {result.error}")
            
    except Exception as e:
        logger.error(f"PDF reordering failed: {e}")
        raise click.ClickException(str(e))


def _parse_page_ranges(pages_str: str) -> List[Tuple[int, int]]:
    """Parse page ranges string into list of tuples."""
    ranges = []
    for part in pages_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = map(int, part.split('-'))
            ranges.append((start, end))
        else:
            page = int(part)
            ranges.append((page, page))
    return ranges


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


def _parse_page_rotations(rotations_str: str) -> dict:
    """Parse page rotations string into dictionary."""
    rotations = {}
    for part in rotations_str.split(','):
        part = part.strip()
        if ':' not in part:
            raise ValueError(f"Invalid rotation format: {part}")
        
        pages_part, angle_str = part.split(':', 1)
        angle = int(angle_str)
        
        if pages_part.lower() == 'all':
            # Handle 'all' pages - will be resolved later
            rotations['all'] = angle
        elif '-' in pages_part:
            start, end = map(int, pages_part.split('-'))
            for page in range(start, end + 1):
                rotations[page] = angle
        else:
            page = int(pages_part)
            rotations[page] = angle
    
    return rotations