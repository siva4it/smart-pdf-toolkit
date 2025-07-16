"""
Configuration management for the FastAPI application.
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache


class APIConfig(BaseSettings):
    """
    API configuration settings.
    """
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Security settings
    secret_key: str = "your-secret-key-here"
    access_token_expire_minutes: int = 30
    
    # CORS settings
    cors_origins: List[str] = ["*"]
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    # File handling settings
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_types: List[str] = ["application/pdf", "image/png", "image/jpeg", "image/tiff"]
    
    # Directory settings
    upload_dir: str = "uploads"
    temp_dir: str = "temp"
    output_dir: str = "output"
    
    # Processing settings
    max_concurrent_jobs: int = 10
    job_timeout_seconds: int = 300  # 5 minutes
    
    # AI services settings
    ai_api_key: Optional[str] = None
    ai_service_url: str = "https://api.openai.com/v1"
    ai_model_name: str = "gpt-3.5-turbo"
    
    # Cache settings
    enable_cache: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }


@lru_cache()
def get_api_config() -> APIConfig:
    """
    Get cached API configuration instance.
    
    Returns:
        APIConfig instance
    """
    return APIConfig()


def get_core_config() -> dict:
    """
    Get configuration dictionary for core services.
    
    Returns:
        Configuration dictionary for core PDF toolkit services
    """
    config = get_api_config()
    
    return {
        "temp_directory": config.temp_dir,
        "max_file_size": config.max_file_size,
        "ai_api_key": config.ai_api_key,
        "ai_service_url": config.ai_service_url,
        "model_name": config.ai_model_name,
        "enable_cache": config.enable_cache,
        "cache_dir": os.path.join(config.temp_dir, "cache")
    }