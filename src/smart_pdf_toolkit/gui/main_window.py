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
from ..core.pdf_operations import PDFOperationsManager
from ..core.content_extractor import ContentExtractor
from ..core.format_converter import FormatConverter
from ..core.security_manager import SecurityManager
from ..core.optimization_engine import OptimizationEngine
from ..core.ai_services import AIServices
from .file_browser import FileBrowser
from .operation_tabs import OperationTabs
from .progress_dialog import ProgressDialog
from .settings_dialog import SettingsDialog
from .batch_processing_dialog import BatchProcessingDialog
from .plugins_dialog import PluginsDialog
from .about_dialog import AboutDialog


class OperationWorker(QThread):
    """Worker thread for processing operations."""
    
    progress_updated = pyqtSignal(int, str)
    operation_completed = pyqtSignal(bool, str)
    
    def __init__(self, operation_type: str, params: dict, config: Config):
        super().__init__()
        self.operation_type = operation_type
        self.params = params
        self.config = config
        self.cancelled = False
        
    def run(self):
        """Execute the operation in a separate thread."""
        try:
            self.progress_updated.emit(10, "Initializing...")
            
            # Initialize core processors
            pdf_ops = PDFOperationsManager(self.config)
            content_extractor = ContentExtractor(self.config)
            format_converter = FormatConverter(self.config)
            security_manager = SecurityManager(self.config)
            optimization_engine = OptimizationEngine(self.config)
            ai_services = AIServices(self.config)
            
            self.progress_updated.emit(20, "Processing files...")
            
            # Execute operation based on type
            if self.operation_type == 'merge':
                self._execute_merge(pdf_ops)
            elif self.operation_type == 'split':
                self._execute_split(pdf_ops)
            elif self.operation_type == 'rotate':
                self._execute_rotate(pdf_ops)
            elif self.operation_type == 'extract_text':
                self._execute_extract_text(content_extractor)
            elif self.operation_type == 'extract_images':
                self._execute_extract_images(content_extractor)
            elif self.operation_type == 'extract_tables':
                self._execute_extract_tables(content_extractor)
            elif self.operation_type == 'pdf_to_images':
                self._execute_pdf_to_images(format_converter)
            elif self.operation_type == 'images_to_pdf':
                self._execute_images_to_pdf(format_converter)
            elif self.operation_type == 'pdf_to_office':
                self._execute_pdf_to_office(format_converter)
            elif self.operation_type == 'pdf_to_html':
                self._execute_pdf_to_html(format_converter)
            elif self.operation_type == 'add_password':
                self._execute_add_password(security_manager)
            elif self.operation_type == 'remove_password':
                self._execute_remove_password(security_manager)
            elif self.operation_type == 'add_watermark':
                self._execute_add_watermark(security_manager)
            elif self.operation_type == 'optimize':
                self._execute_optimize(optimization_engine)
            elif self.operation_type == 'sign':
                self._execute_sign(security_manager)
            elif self.operation_type == 'summarize':
                self._execute_summarize(ai_services)
            elif self.operation_type == 'analyze':
                self._execute_analyze(ai_services)
            elif self.operation_type == 'question':
                self._execute_question(ai_services)
            elif self.operation_type == 'translate':
                self._execute_translate(ai_services)
            else:
                raise ValueError(f"Unknown operation type: {self.operation_type}")
                
            self.progress_updated.emit(100, "Operation completed successfully!")
            self.operation_completed.emit(True, "Operation completed successfully!")
            
        except Exception as e:
            self.operation_completed.emit(False, str(e))
            
    def _execute_merge(self, pdf_ops):
        """Execute PDF merge operation."""
        files = self.params['files']
        output_file = Path(self.params['output_file'])
        
        # Convert Path objects to strings
        file_paths = [str(f) for f in files]
        output_path = str(output_file)
        
        self.progress_updated.emit(50, f"Merging {len(files)} files...")
        result = pdf_ops.merge_pdfs(file_paths, output_path)
        self.progress_updated.emit(90, "Finalizing merge...")
        
    def _execute_split(self, pdf_ops):
        """Execute PDF split operation."""
        file = self.params['file']
        pages = self.params.get('pages')
        output_dir = Path(self.params['output_dir'])
        
        # Convert Path objects to strings
        file_path = str(file)
        output_path = str(output_dir)
        
        self.progress_updated.emit(50, "Splitting PDF...")
        if pages:
            # Parse page ranges
            page_ranges = self._parse_page_ranges(pages)
            result = pdf_ops.split_pdf(file_path, output_path, page_ranges)
        else:
            result = pdf_ops.split_pdf(file_path, output_path)
        self.progress_updated.emit(90, "Finalizing split...")
        
    def _execute_rotate(self, pdf_ops):
        """Execute PDF rotate operation."""
        file = self.params['file']
        rotations = self.params['rotations']
        output_file = Path(self.params['output_file'])
        
        self.progress_updated.emit(50, "Rotating pages...")
        rotation_dict = self._parse_rotations(rotations)
        result = pdf_ops.rotate_pages(file, rotation_dict, output_file)
        self.progress_updated.emit(90, "Finalizing rotation...")
        
    def _execute_extract_text(self, content_extractor):
        """Execute text extraction operation."""
        files = self.params['files']
        output_file = Path(self.params['output_file'])
        preserve_layout = self.params.get('preserve_layout', False)
        
        self.progress_updated.emit(50, "Extracting text...")
        all_text = []
        for i, file in enumerate(files):
            text = content_extractor.extract_text(file, preserve_layout=preserve_layout)
            all_text.append(f"=== {file.name} ===\n{text}\n\n")
            progress = 50 + (30 * (i + 1) // len(files))
            self.progress_updated.emit(progress, f"Processed {i + 1}/{len(files)} files...")
            
        output_file.write_text('\n'.join(all_text), encoding='utf-8')
        self.progress_updated.emit(90, "Saving extracted text...")
        
    def _execute_extract_images(self, content_extractor):
        """Execute image extraction operation."""
        files = self.params['files']
        output_dir = Path(self.params['output_dir'])
        format = self.params.get('format', 'PNG').lower()
        
        output_dir.mkdir(parents=True, exist_ok=True)
        self.progress_updated.emit(50, "Extracting images...")
        
        for i, file in enumerate(files):
            images = content_extractor.extract_images(file, output_dir, format)
            progress = 50 + (30 * (i + 1) // len(files))
            self.progress_updated.emit(progress, f"Processed {i + 1}/{len(files)} files...")
            
        self.progress_updated.emit(90, "Finalizing image extraction...")
        
    def _execute_extract_tables(self, content_extractor):
        """Execute table extraction operation."""
        files = self.params['files']
        output_file = Path(self.params['output_file'])
        format = self.params.get('format', 'CSV')
        
        self.progress_updated.emit(50, "Extracting tables...")
        all_tables = []
        
        for i, file in enumerate(files):
            tables = content_extractor.extract_tables(file)
            all_tables.extend(tables)
            progress = 50 + (30 * (i + 1) // len(files))
            self.progress_updated.emit(progress, f"Processed {i + 1}/{len(files)} files...")
            
        if format.upper() == 'CSV':
            # Save as CSV
            import pandas as pd
            if all_tables:
                combined_df = pd.concat(all_tables, ignore_index=True)
                combined_df.to_csv(output_file, index=False)
        else:
            # Save as Excel
            import pandas as pd
            if all_tables:
                with pd.ExcelWriter(output_file) as writer:
                    for i, table in enumerate(all_tables):
                        table.to_excel(writer, sheet_name=f'Table_{i+1}', index=False)
                        
        self.progress_updated.emit(90, "Saving extracted tables...")
        
    def _parse_page_ranges(self, pages_str: str) -> List[int]:
        """Parse page ranges string like '1-3,5,7-9' into list of page numbers."""
        pages = []
        for part in pages_str.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                pages.extend(range(start, end + 1))
            else:
                pages.append(int(part))
        return sorted(set(pages))
        
    def _parse_rotations(self, rotations_str: str) -> dict:
        """Parse rotations string like '1:90,3:180,5-7:270' into dict."""
        rotations = {}
        for part in rotations_str.split(','):
            part = part.strip()
            if ':' in part:
                pages_part, angle_str = part.split(':')
                angle = int(angle_str)
                
                if '-' in pages_part:
                    start, end = map(int, pages_part.split('-'))
                    for page in range(start, end + 1):
                        rotations[page] = angle
                else:
                    page = int(pages_part)
                    rotations[page] = angle
        return rotations
        
    # Add placeholder methods for other operations
    def _execute_pdf_to_images(self, format_converter):
        self.progress_updated.emit(50, "Converting PDF to images...")
        # Implementation would call format_converter methods
        
    def _execute_images_to_pdf(self, format_converter):
        self.progress_updated.emit(50, "Converting images to PDF...")
        # Implementation would call format_converter methods
        
    def _execute_pdf_to_office(self, format_converter):
        self.progress_updated.emit(50, "Converting PDF to Office format...")
        # Implementation would call format_converter methods
        
    def _execute_pdf_to_html(self, format_converter):
        self.progress_updated.emit(50, "Converting PDF to HTML...")
        # Implementation would call format_converter methods
        
    def _execute_add_password(self, security_manager):
        self.progress_updated.emit(50, "Adding password protection...")
        # Implementation would call security_manager methods
        
    def _execute_remove_password(self, security_manager):
        self.progress_updated.emit(50, "Removing password protection...")
        # Implementation would call security_manager methods
        
    def _execute_add_watermark(self, security_manager):
        self.progress_updated.emit(50, "Adding watermark...")
        # Implementation would call security_manager methods
        
    def _execute_optimize(self, optimization_engine):
        self.progress_updated.emit(50, "Optimizing PDF...")
        # Implementation would call optimization_engine methods
        
    def _execute_sign(self, security_manager):
        self.progress_updated.emit(50, "Signing PDF...")
        # Implementation would call security_manager methods
        
    def _execute_summarize(self, ai_services):
        self.progress_updated.emit(50, "Generating summary...")
        # Implementation would call ai_services methods
        
    def _execute_analyze(self, ai_services):
        self.progress_updated.emit(50, "Analyzing content...")
        # Implementation would call ai_services methods
        
    def _execute_question(self, ai_services):
        self.progress_updated.emit(50, "Processing question...")
        # Implementation would call ai_services methods
        
    def _execute_translate(self, ai_services):
        self.progress_updated.emit(50, "Translating document...")
        # Implementation would call ai_services methods


class MainWindow(QMainWindow):
    """Main application window with tabbed interface and file browser."""
    
    def __init__(self, config: Optional[Config] = None):
        super().__init__()
        self.config = config or Config()
        self.current_files: List[Path] = []
        self.progress_dialog: Optional[ProgressDialog] = None
        self.operation_worker: Optional[OperationWorker] = None
        
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
            self.show_progress("Initializing operation...")
            
            # Create and start operation worker
            self.operation_worker = OperationWorker(operation_type, params, self.config)
            self.operation_worker.progress_updated.connect(self.on_operation_progress)
            self.operation_worker.operation_completed.connect(self.on_operation_completed)
            self.operation_worker.start()
            
        except Exception as e:
            self.hide_progress()
            self.show_error(f"Failed to start operation: {str(e)}")
            
    def on_operation_progress(self, progress: int, message: str):
        """Handle operation progress updates."""
        if self.progress_dialog:
            self.progress_dialog.set_progress(progress)
            self.progress_dialog.set_message(message)
            
    def on_operation_completed(self, success: bool, message: str):
        """Handle operation completion."""
        self.hide_progress()
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.status_bar.showMessage("Operation completed successfully", 5000)
        else:
            self.show_error(f"Operation failed: {message}")
            
        # Clean up worker
        if self.operation_worker:
            self.operation_worker.deleteLater()
            self.operation_worker = None
            
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
        dialog = PluginsDialog(self.config, self)
        dialog.show()
        
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
        # Save settings and cleanup
        try:
            # Cancel any running operations
            if self.operation_worker and self.operation_worker.isRunning():
                self.operation_worker.terminate()
                self.operation_worker.wait(3000)  # Wait up to 3 seconds
                
            # Save configuration
            self.config.save()
            
            # Hide progress dialog
            if self.progress_dialog:
                self.progress_dialog.close()
                
        except Exception as e:
            # Log error but don't prevent closing
            print(f"Error during cleanup: {e}")
            
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