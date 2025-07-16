"""
Example PDF processor plugin demonstrating the plugin API.
"""

from typing import Dict, Any, List
from ..api import PDFProcessorPlugin, PluginMetadata, PluginType, PluginPriority


class ExampleProcessorPlugin(PDFProcessorPlugin):
    """Example PDF processor plugin."""
    
    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name="example_processor",
            version="1.0.0",
            description="Example PDF processor plugin for demonstration",
            author="Smart PDF Toolkit Team",
            email="contact@smart-pdf-toolkit.com",
            plugin_type=PluginType.PDF_PROCESSOR,
            priority=PluginPriority.NORMAL,
            dependencies=[],
            min_toolkit_version="1.0.0"
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin."""
        self._config = config
        self._initialized = True
        return True
    
    def cleanup(self) -> None:
        """Clean up plugin resources."""
        self._initialized = False
    
    def process_pdf(self, input_path: str, output_path: str, **kwargs) -> Dict[str, Any]:
        """
        Process a PDF file.
        
        This is a demonstration plugin that doesn't actually process files.
        """
        operation = kwargs.get('operation', 'copy')
        
        if operation == 'copy':
            # In a real plugin, this would copy the file
            return {
                'success': True,
                'message': f'Successfully copied {input_path} to {output_path}',
                'operation': operation,
                'input_path': input_path,
                'output_path': output_path
            }
        else:
            return {
                'success': False,
                'message': f'Unsupported operation: {operation}',
                'operation': operation
            }
    
    def get_supported_operations(self) -> List[str]:
        """Get list of supported operations."""
        return ['copy', 'validate']
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema."""
        return {
            "type": "object",
            "properties": {
                "enable_validation": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable PDF validation"
                },
                "max_file_size": {
                    "type": "integer",
                    "default": 104857600,
                    "description": "Maximum file size in bytes"
                }
            }
        }


# Plugin factory function
def create_plugin() -> ExampleProcessorPlugin:
    """Create plugin instance."""
    return ExampleProcessorPlugin()