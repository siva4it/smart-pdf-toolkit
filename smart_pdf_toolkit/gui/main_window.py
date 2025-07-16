"""
Main GUI window for Smart PDF Toolkit.
"""

import sys
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMenuBar, QStatusBar, QToolBar, QFileDialog,
    QMessageBox, QProgressBar, QLabel, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QIcon, QDragEnterEvent, QDropEvent

from ..core.config import Config
from ..core.exceptions import PDFToolkitError
from .file_browser import FileBrowser
from .operation_tabs import OperationTabs
from .progress_dialog import ProgressDialog
from .settings_dialog import SettingsDialog
from .batch_processing_dialog import BatchProcessingDialog


class MainWindow(QMainWindow):
    """Main application window with tabbed interface and file browser."""
    
    def __init__(self, config: Optional[Config] = None):
        super().__init__()
        self.config = config or Config()
        self.current_files: List[Path] = []
        self.progress_dialog: Optional[ProgressDialog] = None
        
        self.init_ui()
        self.setup_drag_drop()
        self.setup_status_bar()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Smart PDF Toolkit")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for file browser and operations
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # File browser on the left
        self.file_browser = FileBrowser(self.config)
        self.file_browser.files_selected.connect(self.on_files_selected)
        splitter.addWidget(self.file_browser)
        
        # Operation tabs on the right
        self.operation_tabs = OperationTabs(self.config)
        self.operation_tabs.operation_requested.connect(self.on_operation_requested)
        splitter.addWidget(self.operation_tabs)
        
        # Set splitter proportions (30% file browser, 70% operations)
        splitter.setSizes([360, 840])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        open_action = QAction('&Open Files...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_files)
        file_menu.addAction(open_action)
        
        open_folder_action = QAction('Open &Folder...', self)
        open_folder_action.setShortcut('Ctrl+Shift+O')
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('&Tools')
        
        batch_action = QAction('&Batch Processing...', self)
        batch_action.setShortcut('Ctrl+B')
        batch_action.triggered.connect(self.show_batch_processing)
        tools_menu.addAction(batch_action)
        
        tools_menu.addSeparator()
        
        settings_action = QAction('&Settings...', self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        plugins_action = QAction('&Plugins...', self)
        plugins_action.triggered.connect(self.show_plugins)
        tools_menu.addAction(plugins_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        """Create the application toolbar."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Open files action
        open_action = QAction('Open Files', self)
        open_action.triggered.connect(self.open_files)
        toolbar.addAction(open_action)
        
        # Open folder action
        open_folder_action = QAction('Open Folder', self)
        open_folder_action.triggered.connect(self.open_folder)
        toolbar.addAction(open_folder_action)
        
        toolbar.addSeparator()
        
        # Clear files action
        clear_action = QAction('Clear Files', self)
        clear_action.triggered.connect(self.clear_files)
        toolbar.addAction(clear_action)
        
    def setup_drag_drop(self):
        """Set up drag and drop functionality."""
        self.setAcceptDrops(True)
        
    def setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # File count label
        self.file_count_label = QLabel("No files loaded")
        self.status_bar.addWidget(self.file_count_label)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            # Check if any URLs are PDF files
            pdf_files = [
                url.toLocalFile() for url in event.mimeData().urls()
                if url.toLocalFile().lower().endswith('.pdf')
            ]
            if pdf_files:
                event.acceptProposedAction()
        
    def dropEvent(self, event: QDropEvent):
        """Handle drop events."""
        if event.mimeData().hasUrls():
            pdf_files = [
                Path(url.toLocalFile()) for url in event.mimeData().urls()
                if url.toLocalFile().lower().endswith('.pdf')
            ]
            if pdf_files:
                self.add_files(pdf_files)
                event.acceptProposedAction()
                
    def open_files(self):
        """Open file dialog to select PDF files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select PDF Files",
            str(Path.home()),
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if files:
            pdf_files = [Path(f) for f in files]
            self.add_files(pdf_files)
            
    def open_folder(self):
        """Open folder dialog to select a directory."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            str(Path.home())
        )
        
        if folder:
            folder_path = Path(folder)
            pdf_files = list(folder_path.glob("*.pdf"))
            if pdf_files:
                self.add_files(pdf_files)
            else:
                QMessageBox.information(
                    self,
                    "No PDF Files",
                    f"No PDF files found in {folder_path}"
                )
                
    def add_files(self, files: List[Path]):
        """Add files to the current file list."""
        # Filter out duplicates
        new_files = [f for f in files if f not in self.current_files]
        self.current_files.extend(new_files)
        
        # Update file browser
        self.file_browser.set_files(self.current_files)
        
        # Update status
        self.update_file_count()
        
        # Show success message if files were added
        if new_files:
            self.status_bar.showMessage(
                f"Added {len(new_files)} file(s)", 3000
            )
            
    def clear_files(self):
        """Clear all loaded files."""
        self.current_files.clear()
        self.file_browser.clear_files()
        self.update_file_count()
        self.status_bar.showMessage("Files cleared", 2000)
        
    def update_file_count(self):
        """Update the file count display."""
        count = len(self.current_files)
        if count == 0:
            self.file_count_label.setText("No files loaded")
        elif count == 1:
            self.file_count_label.setText("1 file loaded")
        else:
            self.file_count_label.setText(f"{count} files loaded")
            
    def on_files_selected(self, files: List[Path]):
        """Handle file selection from file browser."""
        # Update operation tabs with selected files
        self.operation_tabs.set_selected_files(files)
        
    def on_operation_requested(self, operation_type: str, params: dict):
        """Handle operation request from operation tabs."""
        try:
            # Show progress dialog
            self.show_progress("Processing files...")
            
            # TODO: Implement actual operation execution
            # This would integrate with the core processing modules
            
            # Simulate processing
            QTimer.singleShot(2000, self.hide_progress)
            
        except Exception as e:
            self.hide_progress()
            self.show_error(f"Operation failed: {str(e)}")
            
    def show_progress(self, message: str):
        """Show progress dialog."""
        if not self.progress_dialog:
            self.progress_dialog = ProgressDialog(self)
        
        self.progress_dialog.set_message(message)
        self.progress_dialog.show()
        
    def hide_progress(self):
        """Hide progress dialog."""
        if self.progress_dialog:
            self.progress_dialog.hide()
            
    def show_error(self, message: str):
        """Show error message dialog."""
        QMessageBox.critical(self, "Error", message)
        
    def show_batch_processing(self):
        """Show batch processing dialog."""
        dialog = BatchProcessingDialog(self.config, self)
        dialog.show()
        
    def show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self.config, self)
        dialog.settings_changed.connect(self.on_settings_changed)
        dialog.exec()
        
    def show_plugins(self):
        """Show plugins dialog."""
        # TODO: Implement plugins dialog
        QMessageBox.information(self, "Plugins", "Plugins dialog not yet implemented")
        
    def on_settings_changed(self):
        """Handle settings changes."""
        # Reload configuration and update UI as needed
        self.status_bar.showMessage("Settings updated", 3000)
        
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Smart PDF Toolkit",
            "Smart PDF Toolkit v1.0.0\n\n"
            "A comprehensive PDF processing and analysis tool.\n\n"
            "Features:\n"
            "• PDF manipulation (merge, split, rotate)\n"
            "• Content extraction (text, images, tables)\n"
            "• AI-powered analysis\n"
            "• Batch processing\n"
            "• Format conversion"
        )
        
    def closeEvent(self, event):
        """Handle application close event."""
        # TODO: Save settings and cleanup
        event.accept()


def main():
    """Main entry point for GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Smart PDF Toolkit")
    app.setApplicationVersion("1.0.0")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())