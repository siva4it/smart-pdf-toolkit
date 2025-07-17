"""
Plugin dependency management system.
"""

import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .api import PluginMetadata

logger = logging.getLogger(__name__)


class DependencyType(Enum):
    """Types of dependencies."""
    PLUGIN = "plugin"
    PACKAGE = "package"
    SYSTEM = "system"
    TOOLKIT_VERSION = "toolkit_version"


@dataclass
class Dependency:
    """Represents a plugin dependency."""
    name: str
    version_spec: str
    dependency_type: DependencyType
    optional: bool = False
    description: Optional[str] = None
    
    def __post_init__(self):
        # Validate version specification
        if not self._is_valid_version_spec(self.version_spec):
            raise ValueError(f"Invalid version specification: {self.version_spec}")
    
    def _is_valid_version_spec(self, spec: str) -> bool:
        """Validate version specification format."""
        # Support formats like: >=1.0.0, ==1.2.3, ~=1.0, >=1.0,<2.0
        pattern = r'^([><=~!]+)?[\d\w\.\-\+]+([,\s]*[><=~!]+[\d\w\.\-\+]+)*$'
        return bool(re.match(pattern, spec.replace(' ', '')))
    
    def matches_version(self, version: str) -> bool:
        """
        Check if a version matches this dependency specification.
        
        Args:
            version: Version string to check
            
        Returns:
            True if version matches, False otherwise
        """
        try:
            from packaging import specifiers, version as pkg_version
            spec_set = specifiers.SpecifierSet(self.version_spec)
            return pkg_version.Version(version) in spec_set
        except ImportError:
            # Fallback to simple string comparison if packaging not available
            logger.warning("packaging library not available, using simple version comparison")
            return self._simple_version_match(version)
    
    def _simple_version_match(self, version: str) -> bool:
        """Simple version matching fallback."""
        # Remove operators and compare
        clean_spec = re.sub(r'^[><=~!]+', '', self.version_spec)
        return version == clean_spec


class DependencyResolver:
    """Resolves plugin dependencies and determines load order."""
    
    def __init__(self):
        self._plugins: Dict[str, PluginMetadata] = {}
        self._dependencies: Dict[str, List[Dependency]] = {}
    
    def add_plugin(self, metadata: PluginMetadata) -> None:
        """
        Add a plugin to the dependency resolver.
        
        Args:
            metadata: Plugin metadata
        """
        self._plugins[metadata.name] = metadata
        self._dependencies[metadata.name] = self._parse_dependencies(metadata.dependencies)
    
    def _parse_dependencies(self, dependencies: List[str]) -> List[Dependency]:
        """
        Parse dependency strings into Dependency objects.
        
        Args:
            dependencies: List of dependency strings
            
        Returns:
            List of Dependency objects
        """
        parsed_deps = []
        
        for dep_str in dependencies:
            # Parse dependency string format: "name[type]:version_spec[?optional]"
            # Examples: "plugin-name:>=1.0.0", "package[package]:>=2.0", "system[system]:tesseract"
            
            optional = dep_str.endswith('?')
            if optional:
                dep_str = dep_str[:-1]
            
            # Extract type if specified
            if '[' in dep_str and ']' in dep_str:
                name_part, rest = dep_str.split('[', 1)
                type_part, version_part = rest.split(']:', 1)
                dep_type = DependencyType(type_part)
                name = name_part
                version_spec = version_part
            else:
                # Default to plugin dependency
                if ':' in dep_str:
                    name, version_spec = dep_str.split(':', 1)
                else:
                    name = dep_str
                    version_spec = ">=0.0.0"
                dep_type = DependencyType.PLUGIN
            
            dependency = Dependency(
                name=name,
                version_spec=version_spec,
                dependency_type=dep_type,
                optional=optional
            )
            parsed_deps.append(dependency)
        
        return parsed_deps
    
    def resolve_dependencies(self) -> Tuple[List[str], List[str]]:
        """
        Resolve plugin dependencies and return load order.
        
        Returns:
            Tuple of (load_order, unresolved_plugins)
        """
        # Build dependency graph
        graph = self._build_dependency_graph()
        
        # Perform topological sort
        load_order = []
        unresolved = []
        
        try:
            load_order = self._topological_sort(graph)
        except ValueError as e:
            logger.error(f"Dependency resolution failed: {e}")
            # Return plugins that can be loaded
            load_order = list(self._plugins.keys())
        
        # Check for unresolved dependencies
        for plugin_name in self._plugins.keys():
            if not self._check_dependencies_satisfied(plugin_name):
                unresolved.append(plugin_name)
                if plugin_name in load_order:
                    load_order.remove(plugin_name)
        
        return load_order, unresolved
    
    def _build_dependency_graph(self) -> Dict[str, Set[str]]:
        """Build dependency graph for topological sorting."""
        graph = {}
        
        for plugin_name in self._plugins.keys():
            graph[plugin_name] = set()
            
            for dependency in self._dependencies[plugin_name]:
                if dependency.dependency_type == DependencyType.PLUGIN:
                    if dependency.name in self._plugins:
                        graph[plugin_name].add(dependency.name)
                    elif not dependency.optional:
                        logger.warning(f"Required plugin dependency not found: {dependency.name}")
        
        return graph
    
    def _topological_sort(self, graph: Dict[str, Set[str]]) -> List[str]:
        """
        Perform topological sort on dependency graph.
        
        Args:
            graph: Dependency graph
            
        Returns:
            Sorted list of plugin names
            
        Raises:
            ValueError: If circular dependency detected
        """
        # Kahn's algorithm
        in_degree = {node: 0 for node in graph}
        
        # Calculate in-degrees
        for node in graph:
            for neighbor in graph[node]:
                in_degree[neighbor] += 1
        
        # Find nodes with no incoming edges
        queue = [node for node in in_degree if in_degree[node] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            # Remove edges from this node
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for circular dependencies
        if len(result) != len(graph):
            remaining = [node for node in graph if node not in result]
            raise ValueError(f"Circular dependency detected involving: {remaining}")
        
        return result
    
    def _check_dependencies_satisfied(self, plugin_name: str) -> bool:
        """
        Check if all dependencies for a plugin are satisfied.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            True if all dependencies satisfied, False otherwise
        """
        dependencies = self._dependencies.get(plugin_name, [])
        
        for dependency in dependencies:
            if not self._is_dependency_satisfied(dependency):
                if not dependency.optional:
                    logger.warning(f"Required dependency not satisfied: {dependency.name}")
                    return False
                else:
                    logger.info(f"Optional dependency not satisfied: {dependency.name}")
        
        return True
    
    def _is_dependency_satisfied(self, dependency: Dependency) -> bool:
        """
        Check if a specific dependency is satisfied.
        
        Args:
            dependency: Dependency to check
            
        Returns:
            True if satisfied, False otherwise
        """
        if dependency.dependency_type == DependencyType.PLUGIN:
            # Check if plugin exists and version matches
            if dependency.name not in self._plugins:
                return False
            
            plugin_version = self._plugins[dependency.name].version
            return dependency.matches_version(plugin_version)
        
        elif dependency.dependency_type == DependencyType.PACKAGE:
            # Check if Python package is available
            try:
                import importlib
                module = importlib.import_module(dependency.name)
                
                # Try to get version
                version = getattr(module, '__version__', '0.0.0')
                return dependency.matches_version(version)
            except ImportError:
                return False
        
        elif dependency.dependency_type == DependencyType.SYSTEM:
            # Check if system dependency is available
            import shutil
            return shutil.which(dependency.name) is not None
        
        elif dependency.dependency_type == DependencyType.TOOLKIT_VERSION:
            # Check toolkit version compatibility
            from .. import __version__
            return dependency.matches_version(__version__)
        
        return False
    
    def get_dependency_info(self, plugin_name: str) -> Dict[str, any]:
        """
        Get detailed dependency information for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Dictionary with dependency information
        """
        if plugin_name not in self._plugins:
            return {}
        
        dependencies = self._dependencies.get(plugin_name, [])
        
        info = {
            'plugin': plugin_name,
            'version': self._plugins[plugin_name].version,
            'dependencies': [],
            'satisfied': True,
            'missing_required': [],
            'missing_optional': []
        }
        
        for dependency in dependencies:
            satisfied = self._is_dependency_satisfied(dependency)
            
            dep_info = {
                'name': dependency.name,
                'type': dependency.dependency_type.value,
                'version_spec': dependency.version_spec,
                'optional': dependency.optional,
                'satisfied': satisfied
            }
            
            info['dependencies'].append(dep_info)
            
            if not satisfied:
                if dependency.optional:
                    info['missing_optional'].append(dependency.name)
                else:
                    info['missing_required'].append(dependency.name)
                    info['satisfied'] = False
        
        return info
    
    def get_load_order_explanation(self) -> Dict[str, List[str]]:
        """
        Get explanation of plugin load order.
        
        Returns:
            Dictionary mapping plugin names to their dependencies
        """
        explanation = {}
        
        for plugin_name in self._plugins.keys():
            plugin_deps = []
            for dependency in self._dependencies.get(plugin_name, []):
                if dependency.dependency_type == DependencyType.PLUGIN:
                    plugin_deps.append(dependency.name)
            
            explanation[plugin_name] = plugin_deps
        
        return explanation