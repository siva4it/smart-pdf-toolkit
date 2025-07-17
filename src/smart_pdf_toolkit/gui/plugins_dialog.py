"""
Plugins management dialog for Smart PDF Toolkit GUI.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QGroupBox, QFormLayout,
    QCheckBox, QMessageBox, QFileDialog, QProgressBar, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QIcon

from ..core.config import Config
from ..plugins.manager import PluginManager
from ..plugins.api import PluginMetadata, PluginType, PluginPriority


class PluginInfoWidget(QWidget):
    """Widget for displaying plugin information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_plugin = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Plugin details
        details_group = QGroupBox("Plugin Details")
        details_layout = QFormLayout(details_group)
        
        self.name_label = QLabel("No plugin selected")
        self.name_label.setFont(QFont("", 12, QFont.Weight.Bold))
        details_layout.addRow("Name:", self.name_label)
        
        self.version_label = QLabel("-")
        details_layout.addRow("Version:", self.version_label)
        
        self.author_label = QLabel("-")
        details_layout.addRow("Author:", self.author_label)
        
        self.type_label = QLabel("-")
        details_layout.addRow("Type:", self.type_label)
        
        self.priority_label = QLabel("-")
        details_layout.addRow("Priority:", self.priority_label)
        
        layout.addWidget(details_group)
        
        # Description
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout(desc_group)
        
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(100)
        desc_layout.addWidget(self.description_text)
        
        layout.addWidget(desc_group)
        
        # Dependencies
        deps_group = QGroupBox("Dependencies")
        deps_layout = QVBoxLayout(deps_group)
        
        self.dependencies_list = QListWidget()
        self.dependencies_list.setMaximumHeight(80)
        deps_layout.addWidget(self.dependencies_list)
        
        layout.addWidget(deps_group)
        
        # Plugin actions
        actions_layout = QHBoxLayout()
        
        self.enable_btn = QPushButton("Enable")
        self.enable_btn.setEnabled(False)
        
        self.disable_btn = QPushButton("Disable")
        self.disable_btn.setEnabled(False)
        
        self.configure_btn = QPushButton("Configure")
        self.configure_btn.setEnabled(False)
        
        self.uninstall_btn = QPushButton("Uninstall")
        self.uninstall_btn.setEnabled(False)
        
        actions_layout.addWidget(self.enable_btn)
        actions_layout.addWidget(self.disable_btn)
        actions_layout.addWidget(self.configure_btn)
        actions_layout.addWidget(self.uninstall_btn)
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)
        layout.addStretch()
        
    def set_plugin(self, plugin_id: str, metadata: PluginMetadata, enabled: bool):
        """Set the current plugin to display."""
        self.current_plugin = plugin_id
        
        self.name_label.setText(metadata.name)
        self.version_label.setText(metadata.version)
        self.author_label.setText(metadata.author)
        self.type_label.setText(metadata.plugin_type.value)
        self.priority_label.setText(metadata.priority.value)
        
        self.description_text.setPlainText(metadata.description)
        
        # Update dependencies list
        self.dependencies_list.clear()
        for dep in metadata.dependencies:
            self.dependencies_list.addItem(dep)
            
        # Update button states
        self.enable_btn.setEnabled(not enabled)
        self.disable_btn.setEnabled(enabled)
        self.configure_btn.setEnabled(enabled)
        self.uninstall_btn.setEnabled(True)
        
    def clear_plugin(self):
        """Clear the plugin display."""
        self.current_plugin = None
        self.name_label.setText("No plugin selected")
        self.version_label.setText("-")
        self.author_label.setText("-")
        self.type_label.setText("-")
        self.priority_label.setText("-")
        self.description_text.clear()
        self.dependencies_list.clear()
        
        self.enable_btn.setEnabled(False)
        self.disable_btn.setEnabled(False)
        self.configure_btn.setEnabled(False)
        self.uninstall_btn.setEnabled(False)


class InstalledPluginsTab(QWidget):
    """Tab for managing installed plugins."""
    
    plugin_selected = pyqtSignal(str, object, bool)  # plugin_id, metadata, enabled
    plugin_enabled = pyqtSignal(str)
    plugin_disabled = pyqtSignal(str)
    plugin_configured = pyqtSignal(str)
    plugin_uninstalled = pyqtSignal(str)
    
    def __init__(self, plugin_manager: PluginManager, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        
        self.init_ui()
        self.setup_connections()
        self.refresh_plugins()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QHBoxLayout(self)
        
        # Left side - plugin list
        left_layout = QVBoxLayout()
        
        # Search and filter
        search_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search plugins...")
        search_layout.addWidget(self.search_edit)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Enabled", "Disabled", "PDF Processor", "Content Extractor", "Format Converter"])
        search_layout.addWidget(self.filter_combo)
        
        left_layout.addLayout(search_layout)
        
        # Plugin list
        self.plugins_list = QListWidget()
        left_layout.addWidget(self.plugins_list)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        left_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(left_layout, 1)
        
        # Right side - plugin info
        self.plugin_info = PluginInfoWidget()
        layout.addWidget(self.plugin_info, 2)
        
    def setup_connections(self):
        """Set up signal connections."""
        self.plugins_list.currentItemChanged.connect(self.on_plugin_selected)
        self.refresh_btn.clicked.connect(self.refresh_plugins)
        self.search_edit.textChanged.connect(self.filter_plugins)
        self.filter_combo.currentTextChanged.connect(self.filter_plugins)
        
        # Connect plugin info signals
        self.plugin_info.enable_btn.clicked.connect(self.enable_current_plugin)
        self.plugin_info.disable_btn.clicked.connect(self.disable_current_plugin)
        self.plugin_info.configure_btn.clicked.connect(self.configure_current_plugin)
        self.plugin_info.uninstall_btn.clicked.connect(self.uninstall_current_plugin)
        
    def refresh_plugins(self):
        """Refresh the plugins list."""
        self.plugins_list.clear()
        
        # Get all registered plugins
        plugins = self.plugin_manager.get_all_plugins()
        
        for plugin_id, plugin_info in plugins.items():
            metadata = plugin_info.get('metadata')
            enabled = plugin_info.get('enabled', False)
            
            if metadata:
                item = QListWidgetItem(f"{metadata.name} v{metadata.version}")
                item.setData(Qt.ItemDataRole.UserRole, (plugin_id, metadata, enabled))
                
                # Set icon based on status
                if enabled:
                    item.setText(f"✓ {metadata.name} v{metadata.version}")
                else:
                    item.setText(f"○ {metadata.name} v{metadata.version}")
                    
                self.plugins_list.addItem(item)
                
    def filter_plugins(self):
        """Filter plugins based on search and filter criteria."""
        search_text = self.search_edit.text().lower()
        filter_type = self.filter_combo.currentText()
        
        for i in range(self.plugins_list.count()):
            item = self.plugins_list.item(i)
            plugin_id, metadata, enabled = item.data(Qt.ItemDataRole.UserRole)
            
            # Apply search filter
            show_item = True
            if search_text:
                show_item = (search_text in metadata.name.lower() or 
                           search_text in metadata.description.lower() or
                           search_text in metadata.author.lower())
                           
            # Apply type filter
            if show_item and filter_type != "All":
                if filter_type == "Enabled":
                    show_item = enabled
                elif filter_type == "Disabled":
                    show_item = not enabled
                else:
                    show_item = metadata.plugin_type.value == filter_type
                    
            item.setHidden(not show_item)
            
    def on_plugin_selected(self, current, previous):
        """Handle plugin selection."""
        if current:
            plugin_id, metadata, enabled = current.data(Qt.ItemDataRole.UserRole)
            self.plugin_info.set_plugin(plugin_id, metadata, enabled)
            self.plugin_selected.emit(plugin_id, metadata, enabled)
        else:
            self.plugin_info.clear_plugin()
            
    def enable_current_plugin(self):
        """Enable the currently selected plugin."""
        if self.plugin_info.current_plugin:
            try:
                self.plugin_manager.enable_plugin(self.plugin_info.current_plugin)
                self.plugin_enabled.emit(self.plugin_info.current_plugin)
                self.refresh_plugins()
                QMessageBox.information(self, "Success", "Plugin enabled successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to enable plugin: {str(e)}")
                
    def disable_current_plugin(self):
        """Disable the currently selected plugin."""
        if self.plugin_info.current_plugin:
            try:
                self.plugin_manager.disable_plugin(self.plugin_info.current_plugin)
                self.plugin_disabled.emit(self.plugin_info.current_plugin)
                self.refresh_plugins()
                QMessageBox.information(self, "Success", "Plugin disabled successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to disable plugin: {str(e)}")
                
    def configure_current_plugin(self):
        """Configure the currently selected plugin."""
        if self.plugin_info.current_plugin:
            self.plugin_configured.emit(self.plugin_info.current_plugin)
            QMessageBox.information(self, "Configure Plugin", "Plugin configuration dialog would open here.")
            
    def uninstall_current_plugin(self):
        """Uninstall the currently selected plugin."""
        if self.plugin_info.current_plugin:
            reply = QMessageBox.question(
                self, "Uninstall Plugin",
                "Are you sure you want to uninstall this plugin?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.plugin_manager.uninstall_plugin(self.plugin_info.current_plugin)
                    self.plugin_uninstalled.emit(self.plugin_info.current_plugin)
                    self.refresh_plugins()
                    QMessageBox.information(self, "Success", "Plugin uninstalled successfully.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to uninstall plugin: {str(e)}")


class PluginInstallTab(QWidget):
    """Tab for installing new plugins."""
    
    plugin_installed = pyqtSignal(str)  # plugin_id
    
    def __init__(self, plugin_manager: PluginManager, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Install from file
        file_group = QGroupBox("Install from File")
        file_layout = QFormLayout(file_group)
        
        self.plugin_file_edit = QLineEdit()
        self.plugin_file_edit.setPlaceholderText("Select plugin file...")
        
        file_input_layout = QHBoxLayout()
        file_input_layout.addWidget(self.plugin_file_edit)
        
        self.browse_file_btn = QPushButton("Browse...")
        file_input_layout.addWidget(self.browse_file_btn)
        
        file_layout.addRow("Plugin file:", file_input_layout)
        
        self.install_file_btn = QPushButton("Install from File")
        self.install_file_btn.setEnabled(False)
        file_layout.addRow(self.install_file_btn)
        
        layout.addWidget(file_group)
        
        # Install from URL
        url_group = QGroupBox("Install from URL")
        url_layout = QFormLayout(url_group)
        
        self.plugin_url_edit = QLineEdit()
        self.plugin_url_edit.setPlaceholderText("https://example.com/plugin.zip")
        url_layout.addRow("Plugin URL:", self.plugin_url_edit)
        
        self.install_url_btn = QPushButton("Install from URL")
        self.install_url_btn.setEnabled(False)
        url_layout.addRow(self.install_url_btn)
        
        layout.addWidget(url_group)
        
        # Plugin marketplace (placeholder)
        marketplace_group = QGroupBox("Plugin Marketplace")
        marketplace_layout = QVBoxLayout(marketplace_group)
        
        marketplace_label = QLabel("Plugin marketplace integration coming soon...")
        marketplace_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        marketplace_layout.addWidget(marketplace_label)
        
        self.browse_marketplace_btn = QPushButton("Browse Marketplace")
        self.browse_marketplace_btn.setEnabled(False)
        marketplace_layout.addWidget(self.browse_marketplace_btn)
        
        layout.addWidget(marketplace_group)
        
        # Installation progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        
    def setup_connections(self):
        """Set up signal connections."""
        self.browse_file_btn.clicked.connect(self.browse_plugin_file)
        self.plugin_file_edit.textChanged.connect(self.update_install_buttons)
        self.plugin_url_edit.textChanged.connect(self.update_install_buttons)
        self.install_file_btn.clicked.connect(self.install_from_file)
        self.install_url_btn.clicked.connect(self.install_from_url)
        
    def browse_plugin_file(self):
        """Browse for plugin file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Plugin File", str(Path.home()),
            "Plugin Files (*.zip *.tar.gz *.py);;All Files (*)"
        )
        
        if file_path:
            self.plugin_file_edit.setText(file_path)
            
    def update_install_buttons(self):
        """Update install button states."""
        has_file = bool(self.plugin_file_edit.text().strip())
        has_url = bool(self.plugin_url_edit.text().strip())
        
        self.install_file_btn.setEnabled(has_file)
        self.install_url_btn.setEnabled(has_url)
        
    def install_from_file(self):
        """Install plugin from file."""
        file_path = self.plugin_file_edit.text().strip()
        if not file_path:
            return
            
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate
            
            # TODO: Implement actual plugin installation
            plugin_id = self.plugin_manager.install_plugin_from_file(file_path)
            
            self.progress_bar.setVisible(False)
            self.plugin_installed.emit(plugin_id)
            
            QMessageBox.information(self, "Success", f"Plugin installed successfully: {plugin_id}")
            self.plugin_file_edit.clear()
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to install plugin: {str(e)}")
            
    def install_from_url(self):
        """Install plugin from URL."""
        url = self.plugin_url_edit.text().strip()
        if not url:
            return
            
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate
            
            # TODO: Implement actual plugin installation from URL
            plugin_id = self.plugin_manager.install_plugin_from_url(url)
            
            self.progress_bar.setVisible(False)
            self.plugin_installed.emit(plugin_id)
            
            QMessageBox.information(self, "Success", f"Plugin installed successfully: {plugin_id}")
            self.plugin_url_edit.clear()
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to install plugin: {str(e)}")


class PluginsDialog(QDialog):
    """Main plugins management dialog."""
    
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.plugin_manager = PluginManager()
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Plugin Manager")
        self.setModal(False)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Installed plugins tab
        self.installed_tab = InstalledPluginsTab(self.plugin_manager)
        self.tab_widget.addTab(self.installed_tab, "Installed Plugins")
        
        # Install plugins tab
        self.install_tab = PluginInstallTab(self.plugin_manager)
        self.tab_widget.addTab(self.install_tab, "Install Plugins")
        
        layout.addWidget(self.tab_widget)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
    def setup_connections(self):
        """Set up signal connections."""
        # Connect install tab to refresh installed tab
        self.install_tab.plugin_installed.connect(self.installed_tab.refresh_plugins)
        
        # Connect installed tab signals
        self.installed_tab.plugin_uninstalled.connect(self.installed_tab.refresh_plugins)