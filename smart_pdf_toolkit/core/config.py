"""
Configuration management system with YAML/JSON support.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from .exceptions import ConfigurationError


@dataclass
class ApplicationConfig:
    """Application-wide configuration."""
    temp_directory: str = "/tmp/smart_pdf_toolkit"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    ocr_languages: list = None
    ai_api_key: Optional[str] = None
    compression_default: int = 5
    batch_size_limit: int = 100
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    def __post_init__(self):
        if self.ocr_languages is None:
            self.ocr_languages = ["eng"]


@dataclass
class PluginConfig:
    """Plugin configuration structure."""
    name: str
    enabled: bool = True
    version: str = "1.0.0"
    settings: Dict[str, Any] = None
    dependencies: list = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {}
        if self.dependencies is None:
            self.dependencies = []


class ConfigManager:
    """Manages application configuration with YAML/JSON support."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_dir: Directory to store configuration files
        """
        if config_dir is None:
            config_dir = os.path.join(os.path.expanduser("~"), ".smart_pdf_toolkit")
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.app_config_file = self.config_dir / "config.yaml"
        self.plugins_config_file = self.config_dir / "plugins.yaml"
        
        self._app_config: Optional[ApplicationConfig] = None
        self._plugins_config: Dict[str, PluginConfig] = {}
    
    def load_config(self) -> ApplicationConfig:
        """Load application configuration from file."""
        if self._app_config is None:
            self._app_config = self._load_app_config()
        return self._app_config
    
    def save_config(self, config: ApplicationConfig) -> None:
        """Save application configuration to file."""
        try:
            config_dict = asdict(config)
            with open(self.app_config_file, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False)
            self._app_config = config
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {str(e)}")
    
    def load_plugins_config(self) -> Dict[str, PluginConfig]:
        """Load plugins configuration from file."""
        if not self._plugins_config:
            self._plugins_config = self._load_plugins_config()
        return self._plugins_config
    
    def save_plugins_config(self, plugins_config: Dict[str, PluginConfig]) -> None:
        """Save plugins configuration to file."""
        try:
            config_dict = {name: asdict(config) for name, config in plugins_config.items()}
            with open(self.plugins_config_file, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False)
            self._plugins_config = plugins_config
        except Exception as e:
            raise ConfigurationError(f"Failed to save plugins configuration: {str(e)}")
    
    def get_plugin_config(self, plugin_name: str) -> Optional[PluginConfig]:
        """Get configuration for a specific plugin."""
        plugins_config = self.load_plugins_config()
        return plugins_config.get(plugin_name)
    
    def set_plugin_config(self, plugin_name: str, config: PluginConfig) -> None:
        """Set configuration for a specific plugin."""
        plugins_config = self.load_plugins_config()
        plugins_config[plugin_name] = config
        self.save_plugins_config(plugins_config)
    
    def _load_app_config(self) -> ApplicationConfig:
        """Load application configuration from file or create default."""
        if self.app_config_file.exists():
            try:
                with open(self.app_config_file, 'r') as f:
                    config_dict = yaml.safe_load(f)
                return ApplicationConfig(**config_dict)
            except Exception as e:
                raise ConfigurationError(f"Failed to load configuration: {str(e)}")
        else:
            # Create default configuration
            default_config = ApplicationConfig()
            self.save_config(default_config)
            return default_config
    
    def _load_plugins_config(self) -> Dict[str, PluginConfig]:
        """Load plugins configuration from file or create empty."""
        if self.plugins_config_file.exists():
            try:
                with open(self.plugins_config_file, 'r') as f:
                    config_dict = yaml.safe_load(f) or {}
                return {
                    name: PluginConfig(**plugin_config) 
                    for name, plugin_config in config_dict.items()
                }
            except Exception as e:
                raise ConfigurationError(f"Failed to load plugins configuration: {str(e)}")
        else:
            return {}
    
    @staticmethod
    def load_from_file(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from a specific file (YAML or JSON)."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                elif file_path.suffix.lower() == '.json':
                    return json.load(f)
                else:
                    raise ConfigurationError(f"Unsupported configuration file format: {file_path.suffix}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration from {file_path}: {str(e)}")
    
    @staticmethod
    def save_to_file(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """Save configuration to a specific file (YAML or JSON)."""
        file_path = Path(file_path)
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(data, f, default_flow_style=False)
                elif file_path.suffix.lower() == '.json':
                    json.dump(data, f, indent=2)
                else:
                    raise ConfigurationError(f"Unsupported configuration file format: {file_path.suffix}")
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration to {file_path}: {str(e)}")


# Global configuration manager instance
config_manager = ConfigManager()