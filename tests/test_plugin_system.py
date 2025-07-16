"""
Tests for the plugin system.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, List

from smart_pdf_toolkit.plugins.api import (
    PluginInterface, PluginMetadata, PluginType, PluginPriority,
    PDFProcessorPlugin, plugin_registry, register_plugin_hook
)
from smart_pdf_toolkit.plugins.dependency import DependencyResolver, Dependency, DependencyType
from smart_pdf_toolkit.plugins.manager import PluginManager


class TestPlugin(PluginInterface):
    """Test plugin for unit testing."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            plugin_type=PluginType.PDF_PROCESSOR,
            dependencies=["dependency1:>=1.0.0", "optional_dep:>=2.0.0?"]
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._config = config
        self._initialized = True
        return True
    
    def cleanup(self) -> None:
        self._initialized = False


class TestPDFProcessor(PDFProcessorPlugin):
    """Test PDF processor plugin."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="test_pdf_processor",
            version="2.0.0",
            description="Test PDF processor",
            author="Test Author",
            plugin_type=PluginType.PDF_PROCESSOR
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._initialized = True
        return True
    
    def cleanup(self) -> None:
        self._initialized = False
    
    def process_pdf(self, input_path: str, output_path: str, **kwargs) -> Dict[str, Any]:
        return {
            'success': True,
            'message': 'Test processing completed',
            'input_path': input_path,
            'output_path': output_path
        }
    
    def get_supported_operations(self) -> List[str]:
        return ['test_operation']


def test_plugin_metadata():
    """Test plugin metadata creation."""
    metadata = PluginMetadata(
        name="test",
        version="1.0.0",
        description="Test plugin",
        author="Test Author",
        plugin_type=PluginType.CONTENT_EXTRACTOR,
        priority=PluginPriority.HIGH,
        dependencies=["dep1:>=1.0.0", "dep2:>=2.0.0"]
    )
    
    assert metadata.name == "test"
    assert metadata.version == "1.0.0"
    assert metadata.plugin_type == PluginType.CONTENT_EXTRACTOR
    assert metadata.priority == PluginPriority.HIGH
    assert len(metadata.dependencies) == 2


def test_plugin_interface():
    """Test plugin interface implementation."""
    plugin = TestPlugin()
    
    # Test metadata
    metadata = plugin.metadata
    assert metadata.name == "test_plugin"
    assert metadata.version == "1.0.0"
    
    # Test initialization
    assert not plugin.is_initialized()
    assert plugin.initialize({'test': 'config'})
    assert plugin.is_initialized()
    
    # Test enable/disable
    assert plugin.is_enabled()
    plugin.disable()
    assert not plugin.is_enabled()
    plugin.enable()
    assert plugin.is_enabled()
    
    # Test cleanup
    plugin.cleanup()
    assert not plugin.is_initialized()


def test_pdf_processor_plugin():
    """Test PDF processor plugin interface."""
    plugin = TestPDFProcessor()
    
    # Test metadata
    assert plugin.metadata.plugin_type == PluginType.PDF_PROCESSOR
    
    # Test initialization
    assert plugin.initialize({})
    
    # Test processing
    result = plugin.process_pdf("input.pdf", "output.pdf")
    assert result['success']
    assert result['input_path'] == "input.pdf"
    assert result['output_path'] == "output.pdf"
    
    # Test supported operations
    operations = plugin.get_supported_operations()
    assert 'test_operation' in operations


def test_dependency_parsing():
    """Test dependency parsing."""
    from smart_pdf_toolkit.plugins.dependency import DependencyResolver
    
    resolver = DependencyResolver()
    
    # Test dependency parsing
    deps = resolver._parse_dependencies([
        "plugin1:>=1.0.0",
        "package[package]:>=2.0.0",
        "system[system]:tesseract",
        "optional[plugin]:>=1.0.0?"
    ])
    
    assert len(deps) == 4
    assert deps[0].name == "plugin1"
    assert deps[0].dependency_type == DependencyType.PLUGIN
    assert not deps[0].optional
    
    assert deps[1].name == "package"
    assert deps[1].dependency_type == DependencyType.PACKAGE
    
    assert deps[2].name == "system"
    assert deps[2].dependency_type == DependencyType.SYSTEM
    
    assert deps[3].name == "optional"
    assert deps[3].optional


def test_dependency_resolution():
    """Test dependency resolution."""
    resolver = DependencyResolver()
    
    # Create test plugins with dependencies
    plugin1_meta = PluginMetadata(
        name="plugin1",
        version="1.0.0",
        description="Plugin 1",
        author="Test",
        dependencies=[]
    )
    
    plugin2_meta = PluginMetadata(
        name="plugin2",
        version="1.0.0",
        description="Plugin 2",
        author="Test",
        dependencies=["plugin1:>=1.0.0"]
    )
    
    plugin3_meta = PluginMetadata(
        name="plugin3",
        version="1.0.0",
        description="Plugin 3",
        author="Test",
        dependencies=["plugin2:>=1.0.0", "plugin1:>=1.0.0"]
    )
    
    # Add plugins to resolver
    resolver.add_plugin(plugin1_meta)
    resolver.add_plugin(plugin2_meta)
    resolver.add_plugin(plugin3_meta)
    
    # Resolve dependencies
    load_order, unresolved = resolver.resolve_dependencies()
    
    # Check load order
    assert len(unresolved) == 0
    assert load_order.index("plugin1") < load_order.index("plugin2")
    assert load_order.index("plugin2") < load_order.index("plugin3")


def test_plugin_registry():
    """Test plugin registry and hooks."""
    # Test hook registration
    @register_plugin_hook("test_hook", PluginPriority.HIGH)
    def test_callback(value):
        return value * 2
    
    @register_plugin_hook("test_hook", PluginPriority.LOW)
    def test_callback2(value):
        return value + 1
    
    # Test hook calling
    results = plugin_registry.call_hook("test_hook", 5)
    
    # High priority should execute first
    assert len(results) == 2
    assert results[0] == 10  # High priority: 5 * 2
    assert results[1] == 6   # Low priority: 5 + 1


def test_plugin_manager():
    """Test plugin manager functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test plugin file
        plugin_dir = Path(temp_dir) / "plugins"
        plugin_dir.mkdir()
        
        plugin_file = plugin_dir / "test_plugin.py"
        plugin_code = '''
from smart_pdf_toolkit.plugins.api import PluginInterface, PluginMetadata, PluginType

class Plugin(PluginInterface):
    @property
    def metadata(self):
        return PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            plugin_type=PluginType.PDF_PROCESSOR
        )
    
    def initialize(self, config):
        self._initialized = True
        return True
    
    def cleanup(self):
        self._initialized = False
'''
        
        with open(plugin_file, 'w') as f:
            f.write(plugin_code)
        
        # Test plugin manager
        manager = PluginManager([str(plugin_dir)])
        
        # Test discovery
        discovered = manager.discover_plugins()
        assert "test_plugin" in discovered
        
        # Test loading
        success = manager.load_plugin("test_plugin")
        assert success
        
        # Test getting plugin
        plugin = manager.get_plugin("test_plugin")
        assert plugin is not None
        assert plugin.metadata.name == "test_plugin"
        
        # Test listing plugins
        plugin_list = manager.list_plugins()
        assert "test_plugin" in plugin_list
        assert plugin_list["test_plugin"]["version"] == "1.0.0"
        
        # Test enable/disable
        assert manager.enable_plugin("test_plugin")
        assert manager.disable_plugin("test_plugin")
        
        # Test unloading
        assert manager.unload_plugin("test_plugin")
        assert manager.get_plugin("test_plugin") is None


def test_plugin_configuration():
    """Test plugin configuration management."""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = PluginManager()
        
        # Create and add a test plugin
        plugin = TestPlugin()
        manager.plugins["test_plugin"] = plugin
        manager._plugin_metadata["test_plugin"] = plugin.metadata
        
        # Test configuration
        config = {"setting1": "value1", "setting2": 42}
        assert manager.configure_plugin("test_plugin", config)
        assert manager.plugin_configs["test_plugin"] == config
        
        # Test saving configuration
        config_file = Path(temp_dir) / "plugin_config.json"
        assert manager.save_plugin_config(str(config_file))
        assert config_file.exists()
        
        # Test loading configuration
        manager2 = PluginManager()
        manager2.plugins["test_plugin"] = TestPlugin()
        manager2._plugin_metadata["test_plugin"] = plugin.metadata
        
        assert manager2.load_plugin_config(str(config_file))
        # Config should be stored for later application
        assert "test_plugin" in manager2.plugin_configs


def test_plugin_types():
    """Test different plugin types."""
    # Test all plugin types are defined
    assert PluginType.PDF_PROCESSOR
    assert PluginType.CONTENT_EXTRACTOR
    assert PluginType.FORMAT_CONVERTER
    assert PluginType.AI_SERVICE
    assert PluginType.CLI_COMMAND
    assert PluginType.API_ENDPOINT
    assert PluginType.GUI_WIDGET
    
    # Test plugin priorities
    assert PluginPriority.HIGHEST.value < PluginPriority.HIGH.value
    assert PluginPriority.HIGH.value < PluginPriority.NORMAL.value
    assert PluginPriority.NORMAL.value < PluginPriority.LOW.value
    assert PluginPriority.LOW.value < PluginPriority.LOWEST.value


def test_version_matching():
    """Test version specification matching."""
    from smart_pdf_toolkit.plugins.dependency import Dependency, DependencyType
    
    # Test exact version
    dep = Dependency("test", "==1.0.0", DependencyType.PLUGIN)
    assert dep.matches_version("1.0.0")
    assert not dep.matches_version("1.0.1")
    
    # Test minimum version
    dep = Dependency("test", ">=1.0.0", DependencyType.PLUGIN)
    assert dep.matches_version("1.0.0")
    assert dep.matches_version("1.0.1")
    assert dep.matches_version("2.0.0")
    assert not dep.matches_version("0.9.0")


def test_circular_dependency_detection():
    """Test circular dependency detection."""
    resolver = DependencyResolver()
    
    # Create circular dependency
    plugin1_meta = PluginMetadata(
        name="plugin1",
        version="1.0.0",
        description="Plugin 1",
        author="Test",
        dependencies=["plugin2:>=1.0.0"]
    )
    
    plugin2_meta = PluginMetadata(
        name="plugin2",
        version="1.0.0",
        description="Plugin 2",
        author="Test",
        dependencies=["plugin1:>=1.0.0"]
    )
    
    resolver.add_plugin(plugin1_meta)
    resolver.add_plugin(plugin2_meta)
    
    # Should detect circular dependency
    load_order, unresolved = resolver.resolve_dependencies()
    
    # Both plugins should be unresolved due to circular dependency
    assert len(unresolved) == 2 or len(load_order) == 0