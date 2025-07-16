"""
Batch processing CLI commands.
"""

import click
from pathlib import Path
from typing import List, Optional
import logging
import json
import time

from ...core.batch_processor import BatchProcessor
from ...core.exceptions import PDFToolkitError
from ..utils import validate_pdf_file, get_output_path, show_progress

logger = logging.getLogger(__name__)


@click.group()
def batch():
    """Batch processing operations for multiple files."""
    pass


@batch.command()
@click.argument('files', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('--operation', '-op', required=True,
              type=click.Choice(['merge', 'split', 'extract-text', 'extract-images', 'ocr', 'summarize']),
              help='Operation to perform on all files')
@click.option('--output-dir', '-o', type=click.Path(),
              help='Output directory for processed files')
@click.option('--config-file', '-c', type=click.Path(exists=True),
              help='JSON configuration file for batch operation')
@click.option('--max-workers', type=int, default=4,
              help='Maximum number of concurrent workers')
@click.option('--continue-on-error', is_flag=True,
              help='Continue processing other files if one fails')
@click.pass_context
def process(ctx, files: tuple, operation: str, output_dir: Optional[str],
            config_file: Optional[str], max_workers: int, continue_on_error: bool):
    """
    Process multiple PDF files with the same operation.
    
    FILES: One or more PDF files to process
    
    Examples:
        smart-pdf batch process *.pdf --operation extract-text
        smart-pdf batch process file1.pdf file2.pdf --operation merge -o output/
        smart-pdf batch process *.pdf --operation ocr --config-file batch_config.json
    """
    config = ctx.obj['config']
    
    try:
        # Validate input files
        pdf_files = []
        for file_path in files:
            validated_path = validate_pdf_file(file_path)
            pdf_files.append(validated_path)
        
        # Determine output directory
        if not output_dir:
            output_dir = config.output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Load batch configuration if provided
        batch_config = {}
        if config_file:
            with open(config_file, 'r') as f:
                batch_config = json.load(f)
        
        # Initialize batch processor
        batch_processor = BatchProcessor(
            max_workers=max_workers,
            continue_on_error=continue_on_error
        )
        
        # Create batch job
        job_config = {
            'operation': operation,
            'output_dir': output_dir,
            'files': pdf_files,
            **batch_config
        }
        
        # Show progress
        with show_progress(f"Processing {len(pdf_files)} files", len(pdf_files)) as progress:
            # Start batch processing
            job_id = batch_processor.create_job(job_config)
            batch_processor.start_job(job_id)
            
            # Monitor progress
            while True:
                status = batch_processor.get_job_status(job_id)
                progress.update(status.completed_tasks)
                
                if status.status in ['completed', 'failed', 'cancelled']:
                    break
                
                time.sleep(1)
        
        # Get final results
        results = batch_processor.get_job_results(job_id)
        
        if results.success:
            click.echo(f"✓ Successfully processed {results.successful_count} files")
            if results.failed_count > 0:
                click.echo(f"⚠ {results.failed_count} files failed to process")
            
            if not ctx.obj['quiet']:
                click.echo(f"  Output directory: {output_dir}")
                click.echo(f"  Total processing time: {results.total_time:.2f}s")
        else:
            raise PDFToolkitError(f"Batch processing failed: {results.error}")
            
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise click.ClickException(str(e))


@batch.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.option('--output-dir', '-o', type=click.Path(),
              help='Override output directory from config')
@click.option('--max-workers', type=int,
              help='Override max workers from config')
@click.pass_context
def run_config(ctx, config_file: str, output_dir: Optional[str], max_workers: Optional[int]):
    """
    Run a batch processing job from a configuration file.
    
    CONFIG_FILE: JSON configuration file defining the batch job
    
    Example configuration file:
    {
        "operation": "extract-text",
        "files": ["file1.pdf", "file2.pdf"],
        "output_dir": "output/",
        "max_workers": 4,
        "continue_on_error": true,
        "operation_config": {
            "preserve_layout": true,
            "include_metadata": false
        }
    }
    
    Examples:
        smart-pdf batch run-config batch_job.json
        smart-pdf batch run-config batch_job.json -o custom_output/
    """
    config = ctx.obj['config']
    
    try:
        # Load batch configuration
        with open(config_file, 'r') as f:
            batch_config = json.load(f)
        
        # Override with command line options
        if output_dir:
            batch_config['output_dir'] = output_dir
        if max_workers:
            batch_config['max_workers'] = max_workers
        
        # Validate required fields
        required_fields = ['operation', 'files']
        for field in required_fields:
            if field not in batch_config:
                raise ValueError(f"Missing required field in config: {field}")
        
        # Validate input files
        pdf_files = []
        for file_path in batch_config['files']:
            validated_path = validate_pdf_file(file_path)
            pdf_files.append(validated_path)
        batch_config['files'] = pdf_files
        
        # Set defaults
        batch_config.setdefault('output_dir', config.output_dir)
        batch_config.setdefault('max_workers', config.max_concurrent_jobs)
        batch_config.setdefault('continue_on_error', True)
        
        # Ensure output directory exists
        Path(batch_config['output_dir']).mkdir(parents=True, exist_ok=True)
        
        # Initialize batch processor
        batch_processor = BatchProcessor(
            max_workers=batch_config['max_workers'],
            continue_on_error=batch_config['continue_on_error']
        )
        
        # Show progress
        file_count = len(batch_config['files'])
        with show_progress(f"Processing {file_count} files", file_count) as progress:
            # Start batch processing
            job_id = batch_processor.create_job(batch_config)
            batch_processor.start_job(job_id)
            
            # Monitor progress
            while True:
                status = batch_processor.get_job_status(job_id)
                progress.update(status.completed_tasks)
                
                if status.status in ['completed', 'failed', 'cancelled']:
                    break
                
                time.sleep(1)
        
        # Get final results
        results = batch_processor.get_job_results(job_id)
        
        if results.success:
            click.echo(f"✓ Successfully processed {results.successful_count} files")
            if results.failed_count > 0:
                click.echo(f"⚠ {results.failed_count} files failed to process")
            
            if not ctx.obj['quiet']:
                click.echo(f"  Output directory: {batch_config['output_dir']}")
                click.echo(f"  Total processing time: {results.total_time:.2f}s")
        else:
            raise PDFToolkitError(f"Batch processing failed: {results.error}")
            
    except Exception as e:
        logger.error(f"Batch processing from config failed: {e}")
        raise click.ClickException(str(e))


@batch.command()
@click.option('--output', '-o', type=click.Path(), default='batch_config.json',
              help='Output configuration file path')
@click.option('--operation', required=True,
              type=click.Choice(['merge', 'split', 'extract-text', 'extract-images', 'ocr', 'summarize']),
              help='Operation to configure')
@click.pass_context
def create_config(ctx, output: str, operation: str):
    """
    Create a sample batch processing configuration file.
    
    Examples:
        smart-pdf batch create-config --operation extract-text
        smart-pdf batch create-config --operation ocr -o my_batch_config.json
    """
    
    # Create sample configuration based on operation
    sample_configs = {
        'merge': {
            'operation': 'merge',
            'files': ['file1.pdf', 'file2.pdf', 'file3.pdf'],
            'output_dir': 'output/',
            'max_workers': 1,  # Merge typically processes one job at a time
            'continue_on_error': False,
            'operation_config': {
                'output_filename': 'merged_document.pdf',
                'bookmark_titles': ['Document 1', 'Document 2', 'Document 3']
            }
        },
        'split': {
            'operation': 'split',
            'files': ['document1.pdf', 'document2.pdf'],
            'output_dir': 'split_output/',
            'max_workers': 2,
            'continue_on_error': True,
            'operation_config': {
                'pages': '1-3,5,7-9',  # Pages to split
                'prefix': 'page'
            }
        },
        'extract-text': {
            'operation': 'extract-text',
            'files': ['doc1.pdf', 'doc2.pdf', 'doc3.pdf'],
            'output_dir': 'text_output/',
            'max_workers': 4,
            'continue_on_error': True,
            'operation_config': {
                'preserve_layout': True,
                'include_metadata': False,
                'pages': None  # All pages
            }
        },
        'extract-images': {
            'operation': 'extract-images',
            'files': ['doc1.pdf', 'doc2.pdf'],
            'output_dir': 'images_output/',
            'max_workers': 3,
            'continue_on_error': True,
            'operation_config': {
                'format': 'PNG',
                'quality': 85,
                'min_size': 100
            }
        },
        'ocr': {
            'operation': 'ocr',
            'files': ['scanned1.pdf', 'scanned2.pdf'],
            'output_dir': 'ocr_output/',
            'max_workers': 2,
            'continue_on_error': True,
            'operation_config': {
                'language': 'eng',
                'confidence_threshold': 0.6
            }
        },
        'summarize': {
            'operation': 'summarize',
            'files': ['report1.pdf', 'report2.pdf'],
            'output_dir': 'summaries/',
            'max_workers': 2,
            'continue_on_error': True,
            'operation_config': {
                'length': 'medium',
                'style': 'paragraph'
            }
        }
    }
    
    try:
        config_data = sample_configs[operation]
        
        with open(output, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        click.echo(f"✓ Sample configuration created: {output}")
        click.echo(f"  Operation: {operation}")
        click.echo("  Edit the file to customize settings and file paths")
        
    except Exception as e:
        logger.error(f"Failed to create config: {e}")
        raise click.ClickException(str(e))