"""
Enhanced plugin management system for Smart PDF Toolkit.
"""

import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional, Type, Union
import logging
import json

from .api import PluginInterface, PluginMetadata, PluginType
from .dependency import DependencyResolver

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages plugin discovery, loading, and execution with dependency resolution."""
    
    def __init__(self, plugin_dirs: List[str] = None):
        """
        Initialize plugin manager.
        
        Args:
            plugin_dirs: List of directories to search for plugins
        """
        self.plugin_dirs = plugin_dirs or []
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_configs: Dict[str, Dict] = {}
        self.dependency_resolver = DependencyResolver()
        self._plugin_metadata: Dict[str, PluginMetadata] = {}
        
        # Add default plugin directories
        self._add_default_plugin_dirs()
    
    def _add_default_plugin_dirs(self):
        """Add default plugin directories."""
        # User plugin directory
        user_plugin_dir = Path.home() / ".smart_pdf_toolkit" / "plugins"
        if user_plugin_dir.exists():
            self.plugin_dirs.append(str(user_plugin_dir))
        
        # System plugin directory
        system_plugin_dir = Path(__file__).parent / "builtin"
        if system_plugin_dir.exists():
            self.plugin_dirs.append(str(system_plugin_dir))
    
    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins in plugin directories.
        
        Returns:
            List of discovered plugin names
        """
        discovered = []
        
        for plugin_dir in self.plugin_dirs:
            plugin_path = Path(plugin_dir)
            if not plugin_path.exists():
                continue
            
            # Look for Python files and packages
            for item in plugin_path.iterdir():
                if item.is_file() and item.suffix == '.py' and not item.name.startswith('_'):
                    plugin_name = item.stem
                    discovered.append(plugin_name)
                    logger.info(f"Discovered plugin: {plugin_name} at {item}")
                
                elif item.is_dir() and not item.name.startswith('_'):
                    # Check if it's a Python package
                    init_file = item / "__init__.py"
                    if init_file.exists():
                        plugin_name = item.name
                        discovered.append(plugin_name)
                        logger.info(f"Discovered plugin package: {plugin_name} at {item}")
        
        return discovered
    
    def load_plugin(self, plugin_name: str, config: Dict[str, Any] = None) -> bool:
        """
        Load a specific plugin.
        
        Args:
            plugin_name: Name of the plugin to load
            config: Optional plugin configuration
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            # Find plugin file
            plugin_path = self._find_plugin_path(plugin_name)
            if not plugin_path:
                logger.error(f"Plugin not found: {plugin_name}")
                return False
            
            # Load plugin module
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            if not spec or not spec.loader:
                logger.error(f"Failed to create spec for plugin: {plugin_name}")
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for plugin class or function
            plugin_instance = self._instantiate_plugin(module, plugin_name)
            if not plugin_instance:
                logger.error(f"Failed to instantiate plugin: {plugin_name}")
                return False
            
            # Validate plugin interface
            if not isinstance(plugin_instance, PluginInterface):
                logger.error(f"Plugin {plugin_name} does not implement PluginInterface")
                return False
            
            # Get and store metadata
            metadata = plugin_instance.metadata
            self._plugin_metadata[plugin_name] = metadata
            self.dependency_resolver.add_plugin(metadata)
            
            # Initialize plugin
            if not plugin_instance.initialize(config or {}):
                logger.error(f"Failed to initialize plugin: {plugin_name}")
                return False
            
            # Store plugin
            self.plugins[plugin_name] = plugin_instance
            if config:
                self.plugin_configs[plugin_name] = config
            
            logger.info(f"Successfully loaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return False
    
    def _find_plugin_path(self, plugin_name: str) -> Optional[Path]:
        """Find the path to a plugin file."""
        for plugin_dir in self.plugin_dirs:
            plugin_path = Path(plugin_dir)
            
            # Check for .py file
            py_file = plugin_path / f"{plugin_name}.py"
            if py_file.exists():
                return py_file
            
            # Check for package
            package_dir = plugin_path / plugin_name
            if package_dir.is_dir():
                init_file = package_dir / "__init__.py"
                if init_file.exists():
                    return init_file
        
        return None
    
    def _instantiate_plugin(self, module: Any, plugin_name: str) -> Optional[PluginInterface]:
        """Instantiate a plugin from a module."""
        # Look for common plugin patterns
        
        # 1. Plugin class with same name as module
        class_name = plugin_name.title().replace('_', '') + 'Plugin'
        if hasattr(module, class_name):
            plugin_class = getattr(module, class_name)
            if callable(plugin_class):
                return plugin_class()
        
        # 2. Plugin class named 'Plugin'
        if hasattr(module, 'Plugin'):
            plugin_class = getattr(module, 'Plugin')
            if callable(plugin_class):
                return plugin_class()
        
        # 3. Function named 'create_plugin'
        if hasattr(module, 'create_plugin'):
            create_func = getattr(module, 'create_plugin')
            if callable(create_func):
                return create_func()
        
        # 4. Look for any class that implements PluginInterface
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, PluginInterface) and 
                attr != PluginInterface):
                return attr()
        
        return None
    
    def load_all_plugins(self) -> Dict[str, bool]:
        """
        Load all discovered plugins in dependency order.
        
        Returns:
            Dictionary mapping plugin names to load success status
        """
        discovered = self.discover_plugins()
        results = {}
        
        # First pass: load plugins to get metadata
        temp_plugins = {}
        for plugin_name in discovered:
            try:
                plugin_path = self._find_plugin_path(plugin_name)
                if plugin_path:
                    spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        plugin_instance = self._instantiate_plugin(module, plugin_name)
                        if plugin_instance and isinstance(plugin_instance, PluginInterface):
                            temp_plugins[plugin_name] = plugin_instance
                            self.dependency_resolver.add_plugin(plugin_instance.metadata)
            except Exception as e:
                logger.warning(f"Failed to analyze plugin {plugin_name}: {e}")
        
        # Resolve dependencies and get load order
        load_order, unresolved = self.dependency_resolver.resolve_dependencies()
        
        # Load plugins in dependency order
        for plugin_name in load_order:
            if plugin_name in temp_plugins:
                try:
                    plugin_instance = temp_plugins[plugin_name]
                    config = self.plugin_configs.get(plugin_name, {})
                    
                    if plugin_instance.initialize(config):
                        self.plugins[plugin_name] = plugin_instance
                        self._plugin_metadata[plugin_name] = plugin_instance.metadata
                        results[plugin_name] = True
                        logger.info(f"Successfully loaded plugin: {plugin_name}")
                    else:
                        results[plugin_name] = False
                        logger.error(f"Failed to initialize plugin: {plugin_name}")
                except Exception as e:
                    results[plugin_name] = False
                    logger.error(f"Failed to load plugin {plugin_name}: {e}")
            else:
                results[plugin_name] = False
        
        # Mark unresolved plugins as failed
        for plugin_name in unresolved:
            results[plugin_name] = False
            logger.error(f"Plugin has unresolved dependencies: {plugin_name}")
        
        return results
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            plugin_name: Name of the plugin to unload
            
        Returns:
            True if unloaded successfully, False otherwise
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin not loaded: {plugin_name}")
            return False
        
        try:
            plugin = self.plugins[plugin_name]
            
            # Call cleanup
            plugin.cleanup()
            
            # Remove from loaded plugins
            del self.plugins[plugin_name]
            if plugin_name in self._plugin_metadata:
                del self._plugin_metadata[plugin_name]
            
            logger.info(f"Successfully unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """
        Get a loaded plugin instance.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginInterface]:
        """
        Get all loaded plugins of a specific type.
        
        Args:
            plugin_type: Type of plugins to retrieve
            
        Returns:
            List of plugin instances
        """
        matching_plugins = []
        
        for plugin_name, plugin in self.plugins.items():
            if plugin.metadata.plugin_type == plugin_type:
                matching_plugins.append(plugin)
        
        return matching_plugins
    
    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        List all loaded plugins with their information.
        
        Returns:
            Dictionary of plugin information
        """
        plugin_info = {}
        
        for name, plugin in self.plugins.items():
            metadata = plugin.metadata
            
            info = {
                'name': metadata.name,
                'version': metadata.version,
                'description': metadata.description,
                'author': metadata.author,
                'type': metadata.plugin_type.value,
                'priority': metadata.priority.value,
                'enabled': plugin.is_enabled(),
                'initialized': plugin.is_initialized(),
                'dependencies': metadata.dependencies
            }
            
            # Get dependency information
            dep_info = self.dependency_resolver.get_dependency_info(name)
            if dep_info:
                info['dependency_status'] = dep_info
            
            plugin_info[name] = info
        
        return plugin_info
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """
        Enable a plugin.
        
        Args:
            plugin_name: Name of the plugin to enable
            
        Returns:
            True if enabled successfully, False otherwise
        """
        plugin = self.get_plugin(plugin_name)
        if plugin:
            plugin.enable()
            logger.info(f"Enabled plugin: {plugin_name}")
            return True
        
        logger.error(f"Plugin not found: {plugin_name}")
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """
        Disable a plugin.
        
        Args:
            plugin_name: Name of the plugin to disable
            
        Returns:
            True if disabled successfully, False otherwise
        """
        plugin = self.get_plugin(plugin_name)
        if plugin:
            plugin.disable()
            logger.info(f"Disabled plugin: {plugin_name}")
            return True
        
        logger.error(f"Plugin not found: {plugin_name}")
        return False
    
    def get_dependency_info(self) -> Dict[str, Any]:
        """
        Get comprehensive dependency information.
        
        Returns:
            Dictionary with dependency information
        """
        load_order, unresolved = self.dependency_resolver.resolve_dependencies()
        
        return {
            'load_order': load_order,
            'unresolved': unresolved,
            'explanation': self.dependency_resolver.get_load_order_explanation(),
            'plugin_details': {
                name: self.dependency_resolver.get_dependency_info(name)
                for name in self._plugin_metadata.keys()
            }
        }
    
    def configure_plugin(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """
        Configure a plugin.
        
        Args:
            plugin_name: Name of the plugin
            config: Configuration dictionary
            
        Returns:
            True if configured successfully, False otherwise
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            logger.error(f"Plugin not found: {plugin_name}")
            return False
        
        try:
            # Validate configuration against schema if available
            schema = plugin.get_config_schema()
            if schema:
                # TODO: Implement JSON schema validation
                pass
            
            # Re-initialize with new configuration
            if not plugin.initialize(config):
                logger.error(f"Failed to reconfigure plugin: {plugin_name}")
                return False
            
            # Store configuration
            self.plugin_configs[plugin_name] = config
            
            logger.info(f"Successfully configured plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure plugin {plugin_name}: {e}")
            return False
    
    def save_plugin_config(self, config_file: str) -> bool:
        """
        Save plugin configurations to file.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            config_data = {
                'plugins': self.plugin_configs,
                'metadata': {
                    name: {
                        'name': meta.name,
                        'version': meta.version,
                        'type': meta.plugin_type.value,
                        'enabled': self.plugins[name].is_enabled() if name in self.plugins else False
                    }
                    for name, meta in self._plugin_metadata.items()
                }
            }
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Plugin configurations saved to: {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save plugin config: {e}")
            return False
    
    def load_plugin_config(self, config_file: str) -> bool:
        """
        Load plugin configurations from file.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Load plugin configurations
            plugin_configs = config_data.get('plugins', {})
            
            # Apply configurations to loaded plugins
            for plugin_name, config in plugin_configs.items():
                if plugin_name in self.plugins:
                    self.configure_plugin(plugin_name, config)
                else:
                    # Store config for when plugin is loaded
                    self.plugin_configs[plugin_name] = config
            
            # Apply enable/disable states
            metadata = config_data.get('metadata', {})
            for plugin_name, meta in metadata.items():
                if plugin_name in self.plugins:
                    if meta.get('enabled', True):
                        self.enable_plugin(plugin_name)
                    else:
                        self.disable_plugin(plugin_name)
            
            logger.info(f"Plugin configurations loaded from: {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load plugin config: {e}")
            return False