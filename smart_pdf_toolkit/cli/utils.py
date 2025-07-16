"""
CLI utility functions.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Union
from contextlib import contextmanager
import click
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console

from ..core.exceptions import PDFToolkitError

console = Console()


def validate_pdf_file(file_path: Union[str, Path]) -> str:
    """
    Validate that a file exists and is a PDF.
    
    Args:
        file_path: Path to the file to validate
        
    Returns:
        Validated file path as string
        
    Raises:
        PDFToolkitError: If file doesn't exist or isn't a PDF
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise PDFToolkitError(f"File not found: {file_path}")
    
    if not file_path.is_file():
        raise PDFToolkitError(f"Path is not a file: {file_path}")
    
    if file_path.suffix.lower() != '.pdf':
        raise PDFToolkitError(f"File is not a PDF: {file_path}")
    
    return str(file_path.absolute())


def get_output_path(output_dir: str, filename: str) -> str:
    """
    Get a safe output path, ensuring the directory exists.
    
    Args:
        output_dir: Output directory
        filename: Output filename
        
    Returns:
        Full output path
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / filename
    
    # Handle filename conflicts
    counter = 1
    original_path = output_path
    while output_path.exists():
        stem = original_path.stem
        suffix = original_path.suffix
        output_path = output_dir / f"{stem}_{counter}{suffix}"
        counter += 1
    
    return str(output_path)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


@contextmanager
def show_progress(description: str, total: Optional[int] = None):
    """
    Context manager for showing progress with rich progress bar.
    
    Args:
        description: Description of the operation
        total: Total number of items (None for indeterminate progress)
        
    Yields:
        Progress task that can be updated
    """
    if total is None:
        # Indeterminate progress (spinner)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(description)
            yield progress
    else:
        # Determinate progress (bar)
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(description, total=total)
            
            class ProgressUpdater:
                def __init__(self, progress_obj, task_id):
                    self.progress = progress_obj
                    self.task_id = task_id
                
                def update(self, advance: int = 1):
                    self.progress.update(self.task_id, advance=advance)
            
            yield ProgressUpdater(progress, task)


def confirm_operation(message: str, default: bool = False) -> bool:
    """
    Ask user for confirmation.
    
    Args:
        message: Confirmation message
        default: Default response if user just presses Enter
        
    Returns:
        True if user confirms, False otherwise
    """
    suffix = " [Y/n]" if default else " [y/N]"
    response = click.prompt(message + suffix, default="", show_default=False)
    
    if not response:
        return default
    
    return response.lower().startswith('y')


def print_error(message: str, exit_code: int = 1):
    """
    Print error message and exit.
    
    Args:
        message: Error message
        exit_code: Exit code
    """
    click.echo(f"Error: {message}", err=True)
    sys.exit(exit_code)


def print_warning(message: str):
    """
    Print warning message.
    
    Args:
        message: Warning message
    """
    click.echo(f"Warning: {message}", err=True)


def print_info(message: str, quiet: bool = False):
    """
    Print info message if not in quiet mode.
    
    Args:
        message: Info message
        quiet: Whether to suppress output
    """
    if not quiet:
        click.echo(message)


def get_file_info(file_path: Union[str, Path]) -> dict:
    """
    Get basic file information.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {}
    
    stat = file_path.stat()
    
    return {
        'name': file_path.name,
        'size': stat.st_size,
        'size_formatted': format_file_size(stat.st_size),
        'modified': stat.st_mtime,
        'path': str(file_path.absolute())
    }


def setup_output_directory(output_dir: str, create: bool = True) -> Path:
    """
    Setup and validate output directory.
    
    Args:
        output_dir: Output directory path
        create: Whether to create the directory if it doesn't exist
        
    Returns:
        Path object for the output directory
        
    Raises:
        PDFToolkitError: If directory setup fails
    """
    output_path = Path(output_dir)
    
    if output_path.exists() and not output_path.is_dir():
        raise PDFToolkitError(f"Output path exists but is not a directory: {output_path}")
    
    if create and not output_path.exists():
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise PDFToolkitError(f"Failed to create output directory: {e}")
    
    return output_path


def check_dependencies():
    """
    Check if required dependencies are available.
    
    Raises:
        PDFToolkitError: If required dependencies are missing
    """
    missing_deps = []
    
    # Check for tesseract (for OCR)
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
    except Exception:
        missing_deps.append("tesseract-ocr (for OCR functionality)")
    
    # Check for AI service dependencies
    try:
        import openai
    except ImportError:
        missing_deps.append("openai (for AI services)")
    
    if missing_deps:
        deps_str = ", ".join(missing_deps)
        raise PDFToolkitError(f"Missing dependencies: {deps_str}")


def validate_page_range(page_range: str, max_pages: int) -> bool:
    """
    Validate page range string.
    
    Args:
        page_range: Page range string (e.g., "1-3,5,7-9")
        max_pages: Maximum number of pages in document
        
    Returns:
        True if valid, False otherwise
    """
    try:
        for part in page_range.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                if start < 1 or end > max_pages or start > end:
                    return False
            else:
                page = int(part)
                if page < 1 or page > max_pages:
                    return False
        return True
    except (ValueError, AttributeError):
        return False