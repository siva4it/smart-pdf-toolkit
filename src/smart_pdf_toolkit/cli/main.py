"""
Main CLI application entry point.
"""

import click
import sys
import os
from pathlib import Path
from typing import Optional
import logging

from .config import CLIConfig, load_cli_config
from .commands import pdf_commands, content_commands, ai_commands, batch_commands
from .completion import CompletionManager, complete_pdf_files, complete_config_files
from ..core.exceptions import PDFToolkitError


# Configure logging for CLI
def setup_logging(verbose: bool = False, quiet: bool = False):
    """Setup logging configuration for CLI."""
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        handlers=[logging.StreamHandler()]
    )


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), 
              help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, 
              help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, 
              help='Suppress all output except errors')
@click.option('--output-dir', '-o', type=click.Path(), 
              help='Default output directory')
@click.option('--temp-dir', type=click.Path(), 
              help='Temporary directory for processing')
@click.pass_context
def cli(ctx, config: Optional[str], verbose: bool, quiet: bool, 
        output_dir: Optional[str], temp_dir: Optional[str]):
    """
    Smart PDF Toolkit - Comprehensive PDF processing and analysis tool.
    
    This tool provides a command-line interface for PDF operations including:
    - PDF manipulation (merge, split, rotate, extract pages)
    - Content extraction (text, images, tables, metadata)
    - AI-powered analysis (summarization, classification, Q&A)
    - Batch processing for multiple files
    - Format conversion and optimization
    
    Use --help with any command to see detailed usage information.
    """
    # Setup logging
    setup_logging(verbose, quiet)
    
    # Load configuration
    cli_config = load_cli_config(config)
    
    # Override config with command line options
    if output_dir:
        cli_config.output_dir = output_dir
    if temp_dir:
        cli_config.temp_dir = temp_dir
    
    # Ensure context object exists
    ctx.ensure_object(dict)
    ctx.obj['config'] = cli_config
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information."""
    click.echo("Smart PDF Toolkit v1.0.0")
    click.echo("A comprehensive PDF processing and analysis tool")


@cli.command()
@click.pass_context
def config_info(ctx):
    """Show current configuration."""
    config = ctx.obj['config']
    
    click.echo("Current Configuration:")
    click.echo(f"  Output Directory: {config.output_dir}")
    click.echo(f"  Temp Directory: {config.temp_dir}")
    click.echo(f"  Max File Size: {config.max_file_size // (1024*1024)}MB")
    click.echo(f"  Default Format: {config.default_output_format}")
    click.echo(f"  OCR Language: {config.ocr_language}")
    click.echo(f"  AI Service: {config.ai_service_url}")


@cli.group()
def completion():
    """Shell completion management."""
    pass


@completion.command()
@click.option('--shell', type=click.Choice(['bash', 'zsh', 'fish', 'powershell']),
              help='Target shell (auto-detect if not specified)')
@click.option('--force', is_flag=True, help='Force installation')
def install(shell, force):
    """Install shell completion."""
    manager = CompletionManager()
    success, message = manager.install_completion(shell, force)
    
    if success:
        click.echo("Shell completion installation instructions:")
        click.echo(message)
    else:
        click.echo(f"Failed to install completion: {message}", err=True)


@completion.command()
@click.argument('shell', type=click.Choice(['bash', 'zsh', 'fish', 'powershell']))
def generate(shell):
    """Generate completion script for a specific shell."""
    manager = CompletionManager()
    success, script = manager.generate_script(shell)
    
    if success:
        click.echo(script)
    else:
        click.echo(f"Failed to generate script: {script}", err=True)


@completion.command()
def status():
    """Show completion status and installation instructions."""
    manager = CompletionManager()
    status = manager.get_completion_status()
    
    click.echo(f"Current shell: {status['current_shell']}")
    click.echo(f"Completion available: {'Yes' if status['completion_available'] else 'No'}")
    click.echo(f"Supported shells: {', '.join(status['supported_shells'])}")
    click.echo("\nInstallation instructions:")
    click.echo(status['installation_instructions'])


# Add command groups
cli.add_command(pdf_commands.pdf)
cli.add_command(content_commands.extract)
cli.add_command(ai_commands.ai)
cli.add_command(batch_commands.batch)
cli.add_command(completion)


def main():
    """Main entry point for the CLI application."""
    try:
        cli()
    except PDFToolkitError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()