"""
Integration tests for CLI functionality.
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from click.testing import CliRunner

from smart_pdf_toolkit.cli.main import cli
from smart_pdf_toolkit.cli.completion import CompletionManager


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    temp_dir = tempfile.mkdtemp()
    output_dir = os.path.join(temp_dir, "output")
    config_dir = os.path.join(temp_dir, "config")
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(config_dir, exist_ok=True)
    
    return {
        "temp_dir": temp_dir,
        "output_dir": output_dir,
        "config_dir": config_dir
    }


@pytest.fixture
def sample_pdfs(temp_dirs):
    """Create sample PDF files for testing."""
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Content) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
    
    # Create multiple test PDFs
    pdf_files = []
    for i in range(3):
        pdf_path = os.path.join(temp_dirs["temp_dir"], f"test_{i+1}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_content)
        pdf_files.append(pdf_path)
    
    return pdf_files


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


def test_completion_install_command(runner):
    """Test completion install command."""
    result = runner.invoke(cli, ['completion', 'install', '--shell', 'bash'])
    assert result.exit_code == 0
    assert "Shell completion installation instructions" in result.output


def test_completion_generate_command(runner):
    """Test completion generate command."""
    result = runner.invoke(cli, ['completion', 'generate', 'bash'])
    assert result.exit_code == 0
    # Should generate some completion script content


def test_completion_status_command(runner):
    """Test completion status command."""
    result = runner.invoke(cli, ['completion', 'status'])
    assert result.exit_code == 0
    assert "Current shell:" in result.output
    assert "Completion available:" in result.output


def test_completion_manager():
    """Test completion manager functionality."""
    manager = CompletionManager()
    
    # Test shell detection
    shell = manager.detect_shell()
    assert shell in manager.supported_shells or shell == 'bash'  # fallback
    
    # Test completion status
    status = manager.get_completion_status()
    assert 'current_shell' in status
    assert 'supported_shells' in status
    assert 'completion_available' in status
    
    # Test installation instructions
    success, instructions = manager.install_completion('bash')
    assert success
    assert 'bashrc' in instructions.lower()


def test_batch_processing_integration(runner, sample_pdfs, temp_dirs):
    """Test batch processing integration."""
    # Create batch configuration
    batch_config = {
        "operation": "extract-text",
        "files": sample_pdfs,
        "output_dir": temp_dirs["output_dir"],
        "max_workers": 2,
        "continue_on_error": True,
        "operation_config": {
            "preserve_layout": False,
            "include_metadata": False
        }
    }
    
    config_file = os.path.join(temp_dirs["config_dir"], "batch_config.json")
    with open(config_file, 'w') as f:
        json.dump(batch_config, f)
    
    # Test batch config creation
    result = runner.invoke(cli, [
        'batch', 'create-config',
        '--operation', 'extract-text',
        '--output', os.path.join(temp_dirs["config_dir"], "created_config.json")
    ])
    assert result.exit_code == 0
    assert "Sample configuration created" in result.output


def test_cli_with_custom_config(runner, temp_dirs):
    """Test CLI with custom configuration file."""
    # Create custom config
    config_data = {
        'output_dir': temp_dirs["output_dir"],
        'temp_dir': temp_dirs["temp_dir"],
        'max_file_size': 50 * 1024 * 1024,
        'verbose_output': True,
        'progress_bar': True,
        'ocr_language': 'fra',
        'ai_model': 'gpt-4'
    }
    
    config_file = os.path.join(temp_dirs["config_dir"], "custom_config.yaml")
    import yaml
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)
    
    # Test CLI with custom config
    result = runner.invoke(cli, [
        '--config', config_file,
        'config-info'
    ])
    assert result.exit_code == 0
    assert temp_dirs["output_dir"] in result.output


def test_pdf_commands_integration(runner, sample_pdfs, temp_dirs):
    """Test PDF commands integration."""
    # Test merge command help
    result = runner.invoke(cli, ['pdf', 'merge', '--help'])
    assert result.exit_code == 0
    assert "Merge multiple PDF files" in result.output
    
    # Test split command help
    result = runner.invoke(cli, ['pdf', 'split', '--help'])
    assert result.exit_code == 0
    assert "Split a PDF file" in result.output
    
    # Test with invalid file (should fail gracefully)
    result = runner.invoke(cli, ['pdf', 'merge', 'nonexistent.pdf'])
    assert result.exit_code != 0


def test_extract_commands_integration(runner, sample_pdfs, temp_dirs):
    """Test extract commands integration."""
    # Test text extraction help
    result = runner.invoke(cli, ['extract', 'text', '--help'])
    assert result.exit_code == 0
    assert "Extract text content" in result.output
    
    # Test images extraction help
    result = runner.invoke(cli, ['extract', 'images', '--help'])
    assert result.exit_code == 0
    assert "Extract images" in result.output
    
    # Test tables extraction help
    result = runner.invoke(cli, ['extract', 'tables', '--help'])
    assert result.exit_code == 0
    assert "Extract tables" in result.output


def test_ai_commands_integration(runner, sample_pdfs, temp_dirs):
    """Test AI commands integration."""
    # Test summarize help
    result = runner.invoke(cli, ['ai', 'summarize', '--help'])
    assert result.exit_code == 0
    assert "Generate an AI-powered summary" in result.output
    
    # Test analyze help
    result = runner.invoke(cli, ['ai', 'analyze', '--help'])
    assert result.exit_code == 0
    assert "Perform AI-powered content analysis" in result.output
    
    # Test question help
    result = runner.invoke(cli, ['ai', 'question', '--help'])
    assert result.exit_code == 0
    assert "Ask a question about a PDF" in result.output


def test_cli_error_handling_integration(runner):
    """Test CLI error handling in integration scenarios."""
    # Test with completely invalid command
    result = runner.invoke(cli, ['invalid-command'])
    assert result.exit_code != 0
    
    # Test with invalid options
    result = runner.invoke(cli, ['--invalid-option'])
    assert result.exit_code != 0
    
    # Test with missing required arguments
    result = runner.invoke(cli, ['pdf', 'merge'])
    assert result.exit_code != 0


def test_cli_verbose_and_quiet_modes(runner, temp_dirs):
    """Test CLI verbose and quiet modes."""
    # Test verbose mode
    result = runner.invoke(cli, [
        '--verbose',
        '--output-dir', temp_dirs["output_dir"],
        'version'
    ])
    assert result.exit_code == 0
    
    # Test quiet mode
    result = runner.invoke(cli, [
        '--quiet',
        '--output-dir', temp_dirs["output_dir"],
        'version'
    ])
    assert result.exit_code == 0


def test_configuration_management_integration(runner, temp_dirs):
    """Test configuration management integration."""
    # Test config info with custom directories
    result = runner.invoke(cli, [
        '--output-dir', temp_dirs["output_dir"],
        '--temp-dir', temp_dirs["temp_dir"],
        'config-info'
    ])
    assert result.exit_code == 0
    assert temp_dirs["output_dir"] in result.output
    assert temp_dirs["temp_dir"] in result.output


def test_shell_completion_functions():
    """Test shell completion functions."""
    from smart_pdf_toolkit.cli.completion import (
        complete_output_formats, complete_languages, complete_operations
    )
    
    # Test format completion
    formats = complete_output_formats(None, None, 'p')
    format_names = [item.value for item in formats]
    assert 'PDF' in format_names or 'PNG' in format_names
    
    # Test language completion
    languages = complete_languages(None, None, 'en')
    lang_codes = [item.value for item in languages]
    assert 'eng' in lang_codes
    
    # Test operations completion
    operations = complete_operations(None, None, 'ex')
    op_names = [item.value for item in operations]
    assert any('extract' in op for op in op_names)


def test_advanced_cli_features(runner, temp_dirs):
    """Test advanced CLI features."""
    # Test with multiple global options
    result = runner.invoke(cli, [
        '--verbose',
        '--output-dir', temp_dirs["output_dir"],
        '--temp-dir', temp_dirs["temp_dir"],
        'config-info'
    ])
    assert result.exit_code == 0
    
    # Test help for main command
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert "Smart PDF Toolkit" in result.output
    assert "completion" in result.output  # Should show completion command


def test_batch_config_validation(runner, temp_dirs):
    """Test batch configuration validation."""
    # Create invalid batch configuration (missing required fields)
    invalid_config = {
        "output_dir": temp_dirs["output_dir"],
        "max_workers": 2
        # Missing 'operation' and 'files'
    }
    
    config_file = os.path.join(temp_dirs["config_dir"], "invalid_config.json")
    with open(config_file, 'w') as f:
        json.dump(invalid_config, f)
    
    # Test with invalid config (should fail)
    result = runner.invoke(cli, ['batch', 'run-config', config_file])
    assert result.exit_code != 0


def test_cli_progress_and_feedback(runner, sample_pdfs, temp_dirs):
    """Test CLI progress display and user feedback."""
    # Test commands that should show progress
    # Note: These tests verify the commands run without error
    # Actual progress display testing would require more complex mocking
    
    # Test version command (simple, should always work)
    result = runner.invoke(cli, ['version'])
    assert result.exit_code == 0
    assert "Smart PDF Toolkit" in result.output
    
    # Test config-info (should show formatted output)
    result = runner.invoke(cli, [
        '--output-dir', temp_dirs["output_dir"],
        'config-info'
    ])
    assert result.exit_code == 0
    assert "Current Configuration:" in result.output