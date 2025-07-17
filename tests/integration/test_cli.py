"""
Tests for CLI functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from click.testing import CliRunner
import json

from smart_pdf_toolkit.cli.main import cli
from smart_pdf_toolkit.cli.config import CLIConfig, load_cli_config, save_cli_config


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
def sample_pdf(temp_dirs):
    """Create a sample PDF file for testing."""
    # Create a minimal PDF file for testing
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
(Hello World) Tj
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
    
    pdf_path = os.path.join(temp_dirs["temp_dir"], "sample.pdf")
    with open(pdf_path, "wb") as f:
        f.write(pdf_content)
    
    return pdf_path


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


def test_cli_version(runner):
    """Test CLI version command."""
    result = runner.invoke(cli, ['version'])
    assert result.exit_code == 0
    assert "Smart PDF Toolkit v1.0.0" in result.output


def test_cli_config_info(runner, temp_dirs):
    """Test CLI config info command."""
    result = runner.invoke(cli, ['--output-dir', temp_dirs["output_dir"], 'config-info'])
    assert result.exit_code == 0
    assert "Current Configuration:" in result.output
    assert temp_dirs["output_dir"] in result.output


def test_cli_help(runner):
    """Test CLI help output."""
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert "Smart PDF Toolkit" in result.output
    assert "pdf" in result.output
    assert "extract" in result.output
    assert "ai" in result.output
    assert "batch" in result.output


def test_pdf_commands_help(runner):
    """Test PDF commands help."""
    result = runner.invoke(cli, ['pdf', '--help'])
    assert result.exit_code == 0
    assert "PDF manipulation operations" in result.output
    assert "merge" in result.output
    assert "split" in result.output
    assert "rotate" in result.output


def test_extract_commands_help(runner):
    """Test extract commands help."""
    result = runner.invoke(cli, ['extract', '--help'])
    assert result.exit_code == 0
    assert "Content extraction operations" in result.output
    assert "text" in result.output
    assert "images" in result.output
    assert "tables" in result.output


def test_ai_commands_help(runner):
    """Test AI commands help."""
    result = runner.invoke(cli, ['ai', '--help'])
    assert result.exit_code == 0
    assert "AI-powered document analysis" in result.output
    assert "summarize" in result.output
    assert "analyze" in result.output
    assert "question" in result.output


def test_batch_commands_help(runner):
    """Test batch commands help."""
    result = runner.invoke(cli, ['batch', '--help'])
    assert result.exit_code == 0
    assert "Batch processing operations" in result.output
    assert "process" in result.output
    assert "run-config" in result.output


def test_cli_config_loading(temp_dirs):
    """Test CLI configuration loading."""
    config_file = os.path.join(temp_dirs["config_dir"], "test_config.yaml")
    
    # Create test configuration
    test_config = {
        'output_dir': temp_dirs["output_dir"],
        'temp_dir': temp_dirs["temp_dir"],
        'max_file_size': 50 * 1024 * 1024,
        'ocr_language': 'fra',
        'ai_model': 'gpt-4'
    }
    
    import yaml
    with open(config_file, 'w') as f:
        yaml.dump(test_config, f)
    
    # Load configuration
    config = load_cli_config(config_file)
    
    assert config.output_dir == temp_dirs["output_dir"]
    assert config.temp_dir == temp_dirs["temp_dir"]
    assert config.max_file_size == 50 * 1024 * 1024
    assert config.ocr_language == 'fra'
    assert config.ai_model == 'gpt-4'


def test_cli_config_saving(temp_dirs):
    """Test CLI configuration saving."""
    config_file = os.path.join(temp_dirs["config_dir"], "saved_config.yaml")
    
    # Create and save configuration
    config = CLIConfig(
        output_dir=temp_dirs["output_dir"],
        temp_dir=temp_dirs["temp_dir"],
        max_file_size=75 * 1024 * 1024,
        ocr_language='deu'
    )
    
    save_cli_config(config, config_file)
    
    # Verify file was created
    assert os.path.exists(config_file)
    
    # Load and verify configuration
    loaded_config = load_cli_config(config_file)
    assert loaded_config.output_dir == temp_dirs["output_dir"]
    assert loaded_config.max_file_size == 75 * 1024 * 1024
    assert loaded_config.ocr_language == 'deu'


def test_batch_create_config(runner, temp_dirs):
    """Test batch config creation."""
    config_file = os.path.join(temp_dirs["temp_dir"], "batch_config.json")
    
    result = runner.invoke(cli, [
        'batch', 'create-config',
        '--operation', 'extract-text',
        '--output', config_file
    ])
    
    assert result.exit_code == 0
    assert "Sample configuration created" in result.output
    assert os.path.exists(config_file)
    
    # Verify configuration content
    with open(config_file, 'r') as f:
        config_data = json.load(f)
    
    assert config_data['operation'] == 'extract-text'
    assert 'files' in config_data
    assert 'output_dir' in config_data
    assert 'max_workers' in config_data


def test_cli_error_handling(runner):
    """Test CLI error handling."""
    # Test with non-existent file
    result = runner.invoke(cli, ['pdf', 'merge', 'nonexistent.pdf'])
    assert result.exit_code != 0
    assert "Error:" in result.output or "File not found" in result.output


def test_cli_verbose_mode(runner, temp_dirs):
    """Test CLI verbose mode."""
    result = runner.invoke(cli, ['--verbose', '--output-dir', temp_dirs["output_dir"], 'config-info'])
    assert result.exit_code == 0
    # Verbose mode should work without errors


def test_cli_quiet_mode(runner, temp_dirs):
    """Test CLI quiet mode."""
    result = runner.invoke(cli, ['--quiet', '--output-dir', temp_dirs["output_dir"], 'config-info'])
    assert result.exit_code == 0
    # Quiet mode should work without errors


def test_argument_validation():
    """Test argument validation functions."""
    from smart_pdf_toolkit.cli.utils import validate_page_range
    
    # Valid page ranges
    assert validate_page_range("1-3,5,7-9", 10) == True
    assert validate_page_range("1", 10) == True
    assert validate_page_range("1-10", 10) == True
    
    # Invalid page ranges
    assert validate_page_range("0-3", 10) == False  # Page 0 doesn't exist
    assert validate_page_range("1-15", 10) == False  # Page 15 > max_pages
    assert validate_page_range("5-3", 10) == False  # Invalid range
    assert validate_page_range("abc", 10) == False  # Non-numeric


def test_file_utilities(temp_dirs):
    """Test file utility functions."""
    from smart_pdf_toolkit.cli.utils import get_output_path, format_file_size, get_file_info
    
    # Test output path generation
    output_path = get_output_path(temp_dirs["output_dir"], "test.txt")
    assert output_path.endswith("test.txt")
    assert temp_dirs["output_dir"] in output_path
    
    # Test file size formatting
    assert format_file_size(0) == "0B"
    assert format_file_size(1024) == "1.0KB"
    assert format_file_size(1024 * 1024) == "1.0MB"
    
    # Test file info (create a test file first)
    test_file = os.path.join(temp_dirs["temp_dir"], "test.txt")
    with open(test_file, "w") as f:
        f.write("test content")
    
    file_info = get_file_info(test_file)
    assert file_info['name'] == "test.txt"
    assert file_info['size'] > 0
    assert 'size_formatted' in file_info


def test_config_environment_overrides(temp_dirs, monkeypatch):
    """Test configuration environment variable overrides."""
    # Set environment variables
    monkeypatch.setenv("SMART_PDF_OUTPUT_DIR", temp_dirs["output_dir"])
    monkeypatch.setenv("SMART_PDF_MAX_FILE_SIZE", "200000000")
    monkeypatch.setenv("SMART_PDF_OCR_LANGUAGE", "spa")
    
    # Load configuration (should pick up env vars)
    config = load_cli_config()
    
    assert config.output_dir == temp_dirs["output_dir"]
    assert config.max_file_size == 200000000
    assert config.ocr_language == "spa"


def test_cli_with_config_file(runner, temp_dirs):
    """Test CLI with custom config file."""
    config_file = os.path.join(temp_dirs["config_dir"], "cli_config.yaml")
    
    # Create test configuration
    test_config = {
        'output_dir': temp_dirs["output_dir"],
        'verbose_output': True,
        'progress_bar': False
    }
    
    import yaml
    with open(config_file, 'w') as f:
        yaml.dump(test_config, f)
    
    # Use CLI with config file
    result = runner.invoke(cli, ['--config', config_file, 'config-info'])
    assert result.exit_code == 0
    assert temp_dirs["output_dir"] in result.output


def test_pdf_command_argument_parsing():
    """Test PDF command argument parsing functions."""
    from smart_pdf_toolkit.cli.commands.pdf_commands import _parse_page_ranges, _parse_page_numbers, _parse_page_rotations
    
    # Test page ranges parsing
    ranges = _parse_page_ranges("1-3,5,7-9")
    expected = [(1, 3), (5, 5), (7, 9)]
    assert ranges == expected
    
    # Test page numbers parsing
    pages = _parse_page_numbers("1,3,5-7")
    expected = [1, 3, 5, 6, 7]
    assert pages == expected
    
    # Test page rotations parsing
    rotations = _parse_page_rotations("1:90,3:180,5-7:270")
    expected = {1: 90, 3: 180, 5: 270, 6: 270, 7: 270}
    assert rotations == expected


def test_content_command_argument_parsing():
    """Test content extraction command argument parsing."""
    from smart_pdf_toolkit.cli.commands.content_commands import _parse_page_numbers
    
    # Test page numbers parsing
    pages = _parse_page_numbers("1,3,5-7,10")
    expected = [1, 3, 5, 6, 7, 10]
    assert pages == expected