"""
Base plugin system implementation.
"""

import importlib
import inspect
from typing import Dict, Any, List, Type, Optional
from pathlib import Path
from ..core.interfaces import IPlugin
from ..core.exceptions import PluginError
from ..core.config import config_manager, PluginConfig


class PluginManager:
    """Manages plugin discovery, loading, and lifecycle."""
    
    def __init__(self):
        self._plugins: Dict[str, IPlugin] = {}
        self._plugin_classes: Dict[str, Type[IPlugin]] = {}
    
    def discover_plugins(self, plugin_dirs: List[str] = None) -> List[str]:
        """Discover available plugins in specified directories.
        
        Args:
            plugin_dirs: List of directories to search for plugins
            
        Returns:
            List of discovered plugin names
        """
        if plugin_dirs is None:
            plugin_dirs = [str(Path(__file__).parent)]
        
        discovered = []
        
        for plugin_dir in plugin_dirs:
            plugin_path = Path(plugin_dir)
            if not plugin_path.exists():
                continue
            
            for py_file in plugin_path.glob("*.py"):
                if py_file.name.startswith("_") or py_file.name == "base.py":
                    continue
                
                try:
                    module_name = f"smart_pdf_toolkit.plugins.{py_file.stem}"
                    module = importlib.import_module(module_name)
                    
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, IPlugin) and 
                            obj != IPlugin and 
                            not inspect.isabstract(obj)):
                            plugin_name = getattr(obj, 'name', name)
                            self._plugin_classes[plugin_name] = obj
                            discovered.append(plugin_name)
                            
                except Exception as e:
                    raise PluginError(f"Failed to discover plugin in {py_file}: {str(e)}")
        
        return discovered
    
    def load_plugin(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Load and initialize a plugin.
        
        Args:
            plugin_name: Name of the plugin to load
            config: Optional configuration for the plugin
        """
        if plugin_name in self._plugins:
            return  # Already loaded
        
        if plugin_name not in self._plugin_classes:
            raise PluginError(f"Plugin not found: {plugin_name}")
        
        try:
            plugin_class = self._plugin_classes[plugin_name]
            plugin_instance = plugin_class()
            
            # Load plugin configuration
            if config is None:
                plugin_config = config_manager.get_plugin_config(plugin_name)
                if plugin_config:
                    config = plugin_config.settings
                else:
                    config = {}
            
            plugin_instance.initialize(config)
            self._plugins[plugin_name] = plugin_instance
            
        except Exception as e:
            raise PluginError(f"Failed to load plugin {plugin_name}: {str(e)}")
    
    def unload_plugin(self, plugin_name: str) -> None:
        """Unload a plugin and cleanup its resources.
        
        Args:
            plugin_name: Name of the plugin to unload
        """
        if plugin_name not in self._plugins:
            return
        
        try:
            plugin = self._plugins[plugin_name]
            plugin.cleanup()
            del self._plugins[plugin_name]
        except Exception as e:
            raise PluginError(f"Failed to unload plugin {plugin_name}: {str(e)}")
    
    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """Get a loaded plugin instance.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin instance or None if not loaded
        """
        return self._plugins.get(plugin_name)
    
    def list_loaded_plugins(self) -> List[str]:
        """Get list of currently loaded plugin names."""
        return list(self._plugins.keys())
    
    def list_available_plugins(self) -> List[str]:
        """Get list of available plugin names."""
        return list(self._plugin_classes.keys())
    
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """Check if a plugin is currently loaded."""
        return plugin_name in self._plugins
    
    def reload_plugin(self, plugin_name: str) -> None:
        """Reload a plugin (unload and load again)."""
        if self.is_plugin_loaded(plugin_name):
            self.unload_plugin(plugin_name)
        self.load_plugin(plugin_name)
    
    def load_enabled_plugins(self) -> None:
        """Load all plugins that are marked as enabled in configuration."""
        plugins_config = config_manager.load_plugins_config()
        
        for plugin_name, plugin_config in plugins_config.items():
            if plugin_config.enabled:
                try:
                    self.load_plugin(plugin_name, plugin_config.settings)
                except PluginError as e:
                    # Log error but continue loading other plugins
                    print(f"Warning: Failed to load plugin {plugin_name}: {e}")
    
    def shutdown_all_plugins(self) -> None:
        """Shutdown all loaded plugins."""
        for plugin_name in list(self._plugins.keys()):
            self.unload_plugin(plugin_name)


# Global plugin manager instance
plugin_manager = PluginManager()