"""
CLI configuration management.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class CLIConfig:
    """CLI configuration settings."""
    
    # Directory settings
    output_dir: str = "output"
    temp_dir: str = "temp"
    
    # File processing settings
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    default_output_format: str = "pdf"
    
    # OCR settings
    ocr_language: str = "eng"
    ocr_confidence_threshold: float = 0.6
    
    # AI service settings
    ai_service_url: str = "https://api.openai.com/v1"
    ai_api_key: Optional[str] = None
    ai_model: str = "gpt-3.5-turbo"
    
    # Batch processing settings
    max_concurrent_jobs: int = 4
    batch_timeout: int = 3600  # 1 hour
    
    # Output settings
    verbose_output: bool = False
    progress_bar: bool = True
    
    # Quality settings
    image_quality: int = 85
    compression_level: str = "medium"


def get_default_config_path() -> Path:
    """Get the default configuration file path."""
    # Try user config directory first
    config_dir = Path.home() / ".config" / "smart-pdf-toolkit"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.yaml"


def load_cli_config(config_path: Optional[str] = None) -> CLIConfig:
    """
    Load CLI configuration from file.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        CLIConfig instance
    """
    config = CLIConfig()
    
    # Determine config file path
    if config_path:
        config_file = Path(config_path)
    else:
        config_file = get_default_config_path()
    
    # Load configuration if file exists
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                if config_file.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    config_data = yaml.safe_load(f)
            
            # Update config with loaded data
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                    
            logger.info(f"Configuration loaded from {config_file}")
            
        except Exception as e:
            logger.warning(f"Failed to load configuration from {config_file}: {e}")
    
    # Override with environment variables
    _load_env_overrides(config)
    
    # Ensure directories exist
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    Path(config.temp_dir).mkdir(parents=True, exist_ok=True)
    
    return config


def _load_env_overrides(config: CLIConfig) -> None:
    """Load configuration overrides from environment variables."""
    env_mappings = {
        'SMART_PDF_OUTPUT_DIR': 'output_dir',
        'SMART_PDF_TEMP_DIR': 'temp_dir',
        'SMART_PDF_MAX_FILE_SIZE': 'max_file_size',
        'SMART_PDF_OCR_LANGUAGE': 'ocr_language',
        'SMART_PDF_AI_API_KEY': 'ai_api_key',
        'SMART_PDF_AI_MODEL': 'ai_model',
        'SMART_PDF_AI_SERVICE_URL': 'ai_service_url',
        'SMART_PDF_MAX_CONCURRENT_JOBS': 'max_concurrent_jobs',
        'SMART_PDF_IMAGE_QUALITY': 'image_quality',
        'SMART_PDF_COMPRESSION_LEVEL': 'compression_level'
    }
    
    for env_var, config_attr in env_mappings.items():
        env_value = os.getenv(env_var)
        if env_value:
            # Convert to appropriate type
            if config_attr in ['max_file_size', 'max_concurrent_jobs', 'image_quality']:
                try:
                    env_value = int(env_value)
                except ValueError:
                    logger.warning(f"Invalid integer value for {env_var}: {env_value}")
                    continue
            elif config_attr == 'ocr_confidence_threshold':
                try:
                    env_value = float(env_value)
                except ValueError:
                    logger.warning(f"Invalid float value for {env_var}: {env_value}")
                    continue
            elif config_attr in ['verbose_output', 'progress_bar']:
                env_value = env_value.lower() in ('true', '1', 'yes', 'on')
            
            setattr(config, config_attr, env_value)


def save_cli_config(config: CLIConfig, config_path: Optional[str] = None) -> None:
    """
    Save CLI configuration to file.
    
    Args:
        config: Configuration to save
        config_path: Optional path to save configuration
    """
    if config_path:
        config_file = Path(config_path)
    else:
        config_file = get_default_config_path()
    
    try:
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = asdict(config)
        
        with open(config_file, 'w') as f:
            if config_file.suffix.lower() == '.json':
                json.dump(config_dict, f, indent=2)
            else:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration saved to {config_file}")
        
    except Exception as e:
        logger.error(f"Failed to save configuration to {config_file}: {e}")
        raise


def create_sample_config(config_path: Optional[str] = None) -> None:
    """
    Create a sample configuration file.
    
    Args:
        config_path: Optional path for the sample config
    """
    config = CLIConfig()
    save_cli_config(config, config_path)