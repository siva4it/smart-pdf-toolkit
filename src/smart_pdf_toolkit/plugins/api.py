"""
Plugin API for extending Smart PDF Toolkit functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PluginType(Enum):
    """Types of plugins supported by the system."""
    PDF_PROCESSOR = "pdf_processor"
    CONTENT_EXTRACTOR = "content_extractor"
    FORMAT_CONVERTER = "format_converter"
    AI_SERVICE = "ai_service"
    SECURITY_HANDLER = "security_handler"
    OPTIMIZATION_ENGINE = "optimization_engine"
    BATCH_PROCESSOR = "batch_processor"
    CLI_COMMAND = "cli_command"
    API_ENDPOINT = "api_endpoint"
    GUI_WIDGET = "gui_widget"


class PluginPriority(Enum):
    """Plugin execution priority levels."""
    HIGHEST = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    LOWEST = 5


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    name: str
    version: str
    description: str
    author: str
    email: Optional[str] = None
    website: Optional[str] = None
    license: Optional[str] = None
    plugin_type: PluginType = PluginType.PDF_PROCESSOR
    priority: PluginPriority = PluginPriority.NORMAL
    dependencies: List[str] = None
    min_toolkit_version: str = "1.0.0"
    max_toolkit_version: Optional[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class PluginInterface(ABC):
    """Base interface for all plugins."""
    
    def __init__(self):
        self._metadata: Optional[PluginMetadata] = None
        self._enabled = True
        self._initialized = False
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the plugin.
        
        Args:
            config: Plugin configuration dictionary
            
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up plugin resources."""
        pass
    
    def is_enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self._enabled
    
    def enable(self) -> None:
        """Enable the plugin."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable the plugin."""
        self._enabled = False
    
    def is_initialized(self) -> bool:
        """Check if plugin is initialized."""
        return self._initialized
    
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Get the configuration schema for this plugin.
        
        Returns:
            JSON schema dictionary
        """
        return {}


class PDFProcessorPlugin(PluginInterface):
    """Interface for PDF processing plugins."""
    
    @abstractmethod
    def process_pdf(self, input_path: str, output_path: str, **kwargs) -> Dict[str, Any]:
        """
        Process a PDF file.
        
        Args:
            input_path: Path to input PDF
            output_path: Path to output PDF
            **kwargs: Additional processing parameters
            
        Returns:
            Processing result dictionary
        """
        pass
    
    @abstractmethod
    def get_supported_operations(self) -> List[str]:
        """
        Get list of supported operations.
        
        Returns:
            List of operation names
        """
        pass


class ContentExtractorPlugin(PluginInterface):
    """Interface for content extraction plugins."""
    
    @abstractmethod
    def extract_content(self, pdf_path: str, content_type: str, **kwargs) -> Dict[str, Any]:
        """
        Extract content from a PDF.
        
        Args:
            pdf_path: Path to PDF file
            content_type: Type of content to extract
            **kwargs: Additional extraction parameters
            
        Returns:
            Extracted content dictionary
        """
        pass
    
    @abstractmethod
    def get_supported_content_types(self) -> List[str]:
        """
        Get list of supported content types.
        
        Returns:
            List of content type names
        """
        pass


class FormatConverterPlugin(PluginInterface):
    """Interface for format conversion plugins."""
    
    @abstractmethod
    def convert(self, input_path: str, output_path: str, target_format: str, **kwargs) -> Dict[str, Any]:
        """
        Convert a file to another format.
        
        Args:
            input_path: Path to input file
            output_path: Path to output file
            target_format: Target format
            **kwargs: Additional conversion parameters
            
        Returns:
            Conversion result dictionary
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """
        Get supported input and output formats.
        
        Returns:
            Dictionary with 'input' and 'output' format lists
        """
        pass


class AIServicePlugin(PluginInterface):
    """Interface for AI service plugins."""
    
    @abstractmethod
    def analyze_document(self, pdf_path: str, analysis_type: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze a document using AI.
        
        Args:
            pdf_path: Path to PDF file
            analysis_type: Type of analysis to perform
            **kwargs: Additional analysis parameters
            
        Returns:
            Analysis result dictionary
        """
        pass
    
    @abstractmethod
    def get_supported_analyses(self) -> List[str]:
        """
        Get list of supported analysis types.
        
        Returns:
            List of analysis type names
        """
        pass


class CLICommandPlugin(PluginInterface):
    """Interface for CLI command plugins."""
    
    @abstractmethod
    def get_command(self) -> Any:
        """
        Get the Click command object.
        
        Returns:
            Click command or group
        """
        pass
    
    @abstractmethod
    def get_command_name(self) -> str:
        """
        Get the command name.
        
        Returns:
            Command name string
        """
        pass


class APIEndpointPlugin(PluginInterface):
    """Interface for API endpoint plugins."""
    
    @abstractmethod
    def get_router(self) -> Any:
        """
        Get the FastAPI router object.
        
        Returns:
            FastAPI APIRouter instance
        """
        pass
    
    @abstractmethod
    def get_prefix(self) -> str:
        """
        Get the URL prefix for the endpoints.
        
        Returns:
            URL prefix string
        """
        pass
    
    @abstractmethod
    def get_tags(self) -> List[str]:
        """
        Get the tags for the endpoints.
        
        Returns:
            List of tag strings
        """
        pass


class GUIWidgetPlugin(PluginInterface):
    """Interface for GUI widget plugins."""
    
    @abstractmethod
    def create_widget(self, parent=None) -> Any:
        """
        Create the widget.
        
        Args:
            parent: Parent widget
            
        Returns:
            Widget instance
        """
        pass
    
    @abstractmethod
    def get_widget_name(self) -> str:
        """
        Get the widget name.
        
        Returns:
            Widget name string
        """
        pass


class PluginHook:
    """Decorator for plugin hook methods."""
    
    def __init__(self, hook_name: str, priority: PluginPriority = PluginPriority.NORMAL):
        self.hook_name = hook_name
        self.priority = priority
    
    def __call__(self, func):
        func._plugin_hook = self.hook_name
        func._plugin_priority = self.priority
        return func


class PluginRegistry:
    """Registry for managing plugin hooks and callbacks."""
    
    def __init__(self):
        self._hooks: Dict[str, List[tuple]] = {}
    
    def register_hook(self, hook_name: str, callback, priority: PluginPriority = PluginPriority.NORMAL):
        """
        Register a hook callback.
        
        Args:
            hook_name: Name of the hook
            callback: Callback function
            priority: Execution priority
        """
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        
        self._hooks[hook_name].append((callback, priority))
        # Sort by priority
        self._hooks[hook_name].sort(key=lambda x: x[1].value)
    
    def call_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Call all callbacks for a hook.
        
        Args:
            hook_name: Name of the hook
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            List of callback results
        """
        results = []
        
        if hook_name in self._hooks:
            for callback, priority in self._hooks[hook_name]:
                try:
                    result = callback(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Hook callback failed: {e}")
        
        return results
    
    def get_hooks(self) -> Dict[str, List[str]]:
        """
        Get all registered hooks.
        
        Returns:
            Dictionary of hook names and their callback count
        """
        return {
            hook_name: len(callbacks)
            for hook_name, callbacks in self._hooks.items()
        }


# Global plugin registry instance
plugin_registry = PluginRegistry()


def register_plugin_hook(hook_name: str, priority: PluginPriority = PluginPriority.NORMAL):
    """
    Decorator to register a function as a plugin hook.
    
    Args:
        hook_name: Name of the hook
        priority: Execution priority
    """
    def decorator(func):
        plugin_registry.register_hook(hook_name, func, priority)
        return func
    return decorator


def call_plugin_hook(hook_name: str, *args, **kwargs) -> List[Any]:
    """
    Call all registered callbacks for a hook.
    
    Args:
        hook_name: Name of the hook
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        List of callback results
    """
    return plugin_registry.call_hook(hook_name, *args, **kwargs)