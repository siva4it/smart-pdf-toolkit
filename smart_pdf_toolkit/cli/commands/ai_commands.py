"""
AI services CLI commands.
"""

import click
from pathlib import Path
from typing import Optional
import logging

from ...core.ai_services import AIServices
from ...core.exceptions import PDFToolkitError
from ..utils import validate_pdf_file, get_output_path, show_progress

logger = logging.getLogger(__name__)


@click.group()
def ai():
    """AI-powered document analysis operations."""
    pass


@ai.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(),
              help='Output file for summary')
@click.option('--length', type=click.Choice(['short', 'medium', 'long']), default='medium',
              help='Summary length')
@click.option('--style', type=click.Choice(['bullet', 'paragraph', 'executive']), default='paragraph',
              help='Summary style')
@click.pass_context
def summarize(ctx, file: str, output: Optional[str], length: str, style: str):
    """
    Generate an AI-powered summary of a PDF document.
    
    FILE: PDF file to summarize
    
    Examples:
        smart-pdf ai summarize document.pdf
        smart-pdf ai summarize document.pdf --length short --style bullet
        smart-pdf ai summarize document.pdf -o summary.txt
    """
    config = ctx.obj['config']
    
    try:
        # Validate input file
        pdf_file = validate_pdf_file(file)
        
        # Determine output path
        if not output:
            base_name = Path(pdf_file).stem
            output = get_output_path(config.output_dir, f"{base_name}_summary.txt")
        
        # Initialize AI services
        ai_services = AIServices(
            api_key=config.ai_api_key,
            service_url=config.ai_service_url,
            model_name=config.ai_model
        )
        
        # Show progress
        with show_progress("Generating summary", 1) as progress:
            # Generate summary
            result = ai_services.summarize_document(
                pdf_file,
                length=length,
                style=style
            )
            progress.update(1)
        
        if result.success:
            # Save summary
            with open(output, 'w', encoding='utf-8') as f:
                f.write(result.summary)
            
            click.echo(f"✓ Successfully generated summary and saved to {output}")
            if not ctx.obj['quiet']:
                word_count = len(result.summary.split())
                click.echo(f"  Summary length: {word_count} words")
        else:
            raise PDFToolkitError(f"Summarization failed: {result.error}")
            
    except Exception as e:
        logger.error(f"AI summarization failed: {e}")
        raise click.ClickException(str(e))


@ai.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(),
              help='Output file for analysis')
@click.option('--analysis-type', multiple=True,
              type=click.Choice(['topics', 'sentiment', 'entities', 'keywords']),
              default=['topics', 'keywords'],
              help='Types of analysis to perform')
@click.pass_context
def analyze(ctx, file: str, output: Optional[str], analysis_type: tuple):
    """
    Perform AI-powered content analysis on a PDF document.
    
    FILE: PDF file to analyze
    
    Examples:
        smart-pdf ai analyze document.pdf
        smart-pdf ai analyze document.pdf --analysis-type topics --analysis-type sentiment
        smart-pdf ai analyze document.pdf -o analysis.json
    """
    config = ctx.obj['config']
    
    try:
        # Validate input file
        pdf_file = validate_pdf_file(file)
        
        # Determine output path
        if not output:
            base_name = Path(pdf_file).stem
            output = get_output_path(config.output_dir, f"{base_name}_analysis.json")
        
        # Initialize AI services
        ai_services = AIServices(
            api_key=config.ai_api_key,
            service_url=config.ai_service_url,
            model_name=config.ai_model
        )
        
        # Show progress
        with show_progress("Analyzing content", len(analysis_type)) as progress:
            # Perform analysis
            result = ai_services.analyze_content(
                pdf_file,
                analysis_types=list(analysis_type)
            )
            progress.update(len(analysis_type))
        
        if result.success:
            # Save analysis
            import json
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(result.analysis, f, indent=2)
            
            click.echo(f"✓ Successfully analyzed content and saved to {output}")
            if not ctx.obj['quiet']:
                for analysis_name in analysis_type:
                    if analysis_name in result.analysis:
                        click.echo(f"  {analysis_name.title()}: ✓")
        else:
            raise PDFToolkitError(f"Content analysis failed: {result.error}")
            
    except Exception as e:
        logger.error(f"AI content analysis failed: {e}")
        raise click.ClickException(str(e))


@ai.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--question', '-q', required=True,
              help='Question to ask about the document')
@click.option('--output', '-o', type=click.Path(),
              help='Output file for answer')
@click.pass_context
def question(ctx, file: str, question: str, output: Optional[str]):
    """
    Ask a question about a PDF document using AI.
    
    FILE: PDF file to ask questions about
    
    Examples:
        smart-pdf ai question document.pdf -q "What is the main topic?"
        smart-pdf ai question document.pdf --question "Who are the authors?" -o answer.txt
    """
    config = ctx.obj['config']
    
    try:
        # Validate input file
        pdf_file = validate_pdf_file(file)
        
        # Initialize AI services
        ai_services = AIServices(
            api_key=config.ai_api_key,
            service_url=config.ai_service_url,
            model_name=config.ai_model
        )
        
        # Show progress
        with show_progress("Processing question", 1) as progress:
            # Ask question
            result = ai_services.answer_question(pdf_file, question)
            progress.update(1)
        
        if result.success:
            # Display or save answer
            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(f"Question: {question}\\n\\n")
                    f.write(f"Answer: {result.answer}")
                click.echo(f"✓ Answer saved to {output}")
            else:
                click.echo(f"\\nQuestion: {question}")
                click.echo(f"Answer: {result.answer}")
            
            if not ctx.obj['quiet'] and hasattr(result, 'confidence'):
                click.echo(f"Confidence: {result.confidence:.2f}")
        else:
            raise PDFToolkitError(f"Question answering failed: {result.error}")
            
    except Exception as e:
        logger.error(f"AI question answering failed: {e}")
        raise click.ClickException(str(e))


@ai.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--target-language', '-t', required=True,
              help='Target language for translation (e.g., "french", "spanish", "german")')
@click.option('--output', '-o', type=click.Path(),
              help='Output file for translated content')
@click.option('--preserve-formatting', is_flag=True,
              help='Attempt to preserve document formatting')
@click.pass_context
def translate(ctx, file: str, target_language: str, output: Optional[str], preserve_formatting: bool):
    """
    Translate a PDF document to another language using AI.
    
    FILE: PDF file to translate
    
    Examples:
        smart-pdf ai translate document.pdf -t french
        smart-pdf ai translate document.pdf --target-language spanish -o translated.txt
        smart-pdf ai translate document.pdf -t german --preserve-formatting
    """
    config = ctx.obj['config']
    
    try:
        # Validate input file
        pdf_file = validate_pdf_file(file)
        
        # Determine output path
        if not output:
            base_name = Path(pdf_file).stem
            output = get_output_path(config.output_dir, f"{base_name}_translated_{target_language}.txt")
        
        # Initialize AI services
        ai_services = AIServices(
            api_key=config.ai_api_key,
            service_url=config.ai_service_url,
            model_name=config.ai_model
        )
        
        # Show progress
        with show_progress("Translating document", 1) as progress:
            # Translate document
            result = ai_services.translate_document(
                pdf_file,
                target_language=target_language,
                preserve_formatting=preserve_formatting
            )
            progress.update(1)
        
        if result.success:
            # Save translation
            with open(output, 'w', encoding='utf-8') as f:
                f.write(result.translated_text)
            
            click.echo(f"✓ Successfully translated document to {target_language} and saved to {output}")
            if not ctx.obj['quiet']:
                word_count = len(result.translated_text.split())
                click.echo(f"  Translated text length: {word_count} words")
        else:
            raise PDFToolkitError(f"Translation failed: {result.error}")
            
    except Exception as e:
        logger.error(f"AI translation failed: {e}")
        raise click.ClickException(str(e))