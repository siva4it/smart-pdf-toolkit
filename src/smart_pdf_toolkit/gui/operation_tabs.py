"""
Operation tabs widget for Smart PDF Toolkit GUI.
"""

from pathlib import Path
from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QPushButton, QComboBox, QSpinBox, QLineEdit, QTextEdit,
    QCheckBox, QGroupBox, QFormLayout, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..core.config import Config
from .ai_services_tab import AIServicesTab
from .format_conversion_tab import FormatConversionTab
from .security_optimization_tab import SecurityOptimizationTab


class PDFOperationsTab(QWidget):
    """Tab for basic PDF operations (merge, split, rotate, etc.)."""
    
    operation_requested = pyqtSignal(str, dict)
    
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.selected_files: List[Path] = []
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Merge section
        merge_group = QGroupBox("Merge PDFs")
        merge_layout = QFormLayout(merge_group)
        
        # Output file selection
        merge_file_layout = QHBoxLayout()
        self.merge_output_edit = QLineEdit()
        self.merge_output_edit.setPlaceholderText("merged_output.pdf")
        self.merge_browse_btn = QPushButton("Browse...")
        self.merge_browse_btn.setMaximumWidth(80)
        merge_file_layout.addWidget(self.merge_output_edit)
        merge_file_layout.addWidget(self.merge_browse_btn)
        merge_layout.addRow("Output file:", merge_file_layout)
        
        self.merge_btn = QPushButton("Merge Selected Files")
        self.merge_btn.setEnabled(False)
        merge_layout.addRow(self.merge_btn)
        
        layout.addWidget(merge_group)
        
        # Split section
        split_group = QGroupBox("Split PDF")
        split_layout = QFormLayout(split_group)
        
        self.split_pages_edit = QLineEdit()
        self.split_pages_edit.setPlaceholderText("1-3,5,7-9 or leave empty for all pages")
        split_layout.addRow("Page ranges:", self.split_pages_edit)
        
        # Output directory selection
        split_dir_layout = QHBoxLayout()
        self.split_output_edit = QLineEdit()
        self.split_output_edit.setPlaceholderText("split_output/")
        self.split_browse_btn = QPushButton("Browse...")
        self.split_browse_btn.setMaximumWidth(80)
        split_dir_layout.addWidget(self.split_output_edit)
        split_dir_layout.addWidget(self.split_browse_btn)
        split_layout.addRow("Output directory:", split_dir_layout)
        
        self.split_btn = QPushButton("Split Selected File")
        self.split_btn.setEnabled(False)
        split_layout.addRow(self.split_btn)
        
        layout.addWidget(split_group)
        
        # Rotate section
        rotate_group = QGroupBox("Rotate Pages")
        rotate_layout = QFormLayout(rotate_group)
        
        self.rotate_pages_edit = QLineEdit()
        self.rotate_pages_edit.setPlaceholderText("1:90,3:180,5-7:270")
        rotate_layout.addRow("Page rotations:", self.rotate_pages_edit)
        
        # Output file selection
        rotate_file_layout = QHBoxLayout()
        self.rotate_output_edit = QLineEdit()
        self.rotate_output_edit.setPlaceholderText("rotated_output.pdf")
        self.rotate_browse_btn = QPushButton("Browse...")
        self.rotate_browse_btn.setMaximumWidth(80)
        rotate_file_layout.addWidget(self.rotate_output_edit)
        rotate_file_layout.addWidget(self.rotate_browse_btn)
        rotate_layout.addRow("Output file:", rotate_file_layout)
        
        self.rotate_btn = QPushButton("Rotate Pages")
        self.rotate_btn.setEnabled(False)
        rotate_layout.addRow(self.rotate_btn)
        
        layout.addWidget(rotate_group)
        
        layout.addStretch()
        
    def setup_connections(self):
        """Set up signal connections."""
        self.merge_btn.clicked.connect(self.on_merge_clicked)
        self.split_btn.clicked.connect(self.on_split_clicked)
        self.rotate_btn.clicked.connect(self.on_rotate_clicked)
        
        # Browse button connections
        self.merge_browse_btn.clicked.connect(self.on_merge_browse_clicked)
        self.split_browse_btn.clicked.connect(self.on_split_browse_clicked)
        self.rotate_browse_btn.clicked.connect(self.on_rotate_browse_clicked)
        
    def set_selected_files(self, files: List[Path]):
        """Set the selected files."""
        self.selected_files = files
        self.update_button_states()
        
    def update_button_states(self):
        """Update button enabled states based on selection."""
        has_files = len(self.selected_files) > 0
        has_single_file = len(self.selected_files) == 1
        has_multiple_files = len(self.selected_files) > 1
        
        self.merge_btn.setEnabled(has_multiple_files)
        self.split_btn.setEnabled(has_single_file)
        self.rotate_btn.setEnabled(has_single_file)
        
    def on_merge_clicked(self):
        """Handle merge button click."""
        if len(self.selected_files) < 2:
            QMessageBox.warning(self, "Warning", "Please select at least 2 files to merge.")
            return
            
        output_file = self.merge_output_edit.text().strip()
        if not output_file:
            output_file = "merged_output.pdf"
            
        params = {
            'files': self.selected_files,
            'output_file': output_file
        }
        
        self.operation_requested.emit('merge', params)
        
    def on_split_clicked(self):
        """Handle split button click."""
        if len(self.selected_files) != 1:
            QMessageBox.warning(self, "Warning", "Please select exactly 1 file to split.")
            return
            
        pages = self.split_pages_edit.text().strip()
        output_dir = self.split_output_edit.text().strip()
        if not output_dir:
            output_dir = "split_output/"
            
        params = {
            'file': self.selected_files[0],
            'pages': pages if pages else None,
            'output_dir': output_dir
        }
        
        self.operation_requested.emit('split', params)
        
    def on_rotate_clicked(self):
        """Handle rotate button click."""
        if len(self.selected_files) != 1:
            QMessageBox.warning(self, "Warning", "Please select exactly 1 file to rotate.")
            return
            
        rotations = self.rotate_pages_edit.text().strip()
        if not rotations:
            QMessageBox.warning(self, "Warning", "Please specify page rotations.")
            return
            
        output_file = self.rotate_output_edit.text().strip()
        if not output_file:
            output_file = "rotated_output.pdf"
            
        params = {
            'file': self.selected_files[0],
            'rotations': rotations,
            'output_file': output_file
        }
        
        self.operation_requested.emit('rotate', params)
    
    def on_merge_browse_clicked(self):
        """Handle merge browse button click."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Merged PDF As",
            self.merge_output_edit.text() or "merged_output.pdf",
            "PDF Files (*.pdf);;All Files (*)"
        )
        if file_path:
            self.merge_output_edit.setText(file_path)
    
    def on_split_browse_clicked(self):
        """Handle split browse button click."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory for Split Files",
            self.split_output_edit.text() or str(Path.home())
        )
        if dir_path:
            self.split_output_edit.setText(dir_path)
    
    def on_rotate_browse_clicked(self):
        """Handle rotate browse button click."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Rotated PDF As",
            self.rotate_output_edit.text() or "rotated_output.pdf",
            "PDF Files (*.pdf);;All Files (*)"
        )
        if file_path:
            self.rotate_output_edit.setText(file_path)


class ContentExtractionTab(QWidget):
    """Tab for content extraction operations."""
    
    operation_requested = pyqtSignal(str, dict)
    
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.selected_files: List[Path] = []
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Text extraction section
        text_group = QGroupBox("Extract Text")
        text_layout = QFormLayout(text_group)
        
        self.text_output_edit = QLineEdit()
        self.text_output_edit.setPlaceholderText("extracted_text.txt")
        text_layout.addRow("Output file:", self.text_output_edit)
        
        self.preserve_layout_cb = QCheckBox("Preserve layout")
        text_layout.addRow(self.preserve_layout_cb)
        
        self.extract_text_btn = QPushButton("Extract Text")
        self.extract_text_btn.setEnabled(False)
        text_layout.addRow(self.extract_text_btn)
        
        layout.addWidget(text_group)
        
        # Image extraction section
        images_group = QGroupBox("Extract Images")
        images_layout = QFormLayout(images_group)
        
        self.images_output_edit = QLineEdit()
        self.images_output_edit.setPlaceholderText("images/")
        images_layout.addRow("Output directory:", self.images_output_edit)
        
        self.image_format_combo = QComboBox()
        self.image_format_combo.addItems(["PNG", "JPEG", "TIFF"])
        images_layout.addRow("Image format:", self.image_format_combo)
        
        self.extract_images_btn = QPushButton("Extract Images")
        self.extract_images_btn.setEnabled(False)
        images_layout.addRow(self.extract_images_btn)
        
        layout.addWidget(images_group)
        
        # Table extraction section
        tables_group = QGroupBox("Extract Tables")
        tables_layout = QFormLayout(tables_group)
        
        self.tables_output_edit = QLineEdit()
        self.tables_output_edit.setPlaceholderText("tables.csv")
        tables_layout.addRow("Output file:", self.tables_output_edit)
        
        self.table_format_combo = QComboBox()
        self.table_format_combo.addItems(["CSV", "Excel"])
        tables_layout.addRow("Output format:", self.table_format_combo)
        
        self.extract_tables_btn = QPushButton("Extract Tables")
        self.extract_tables_btn.setEnabled(False)
        tables_layout.addRow(self.extract_tables_btn)
        
        layout.addWidget(tables_group)
        
        layout.addStretch()
        
    def setup_connections(self):
        """Set up signal connections."""
        self.extract_text_btn.clicked.connect(self.on_extract_text_clicked)
        self.extract_images_btn.clicked.connect(self.on_extract_images_clicked)
        self.extract_tables_btn.clicked.connect(self.on_extract_tables_clicked)
        
    def set_selected_files(self, files: List[Path]):
        """Set the selected files."""
        self.selected_files = files
        self.update_button_states()
        
    def update_button_states(self):
        """Update button enabled states based on selection."""
        has_files = len(self.selected_files) > 0
        
        self.extract_text_btn.setEnabled(has_files)
        self.extract_images_btn.setEnabled(has_files)
        self.extract_tables_btn.setEnabled(has_files)
        
    def on_extract_text_clicked(self):
        """Handle extract text button click."""
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select files to extract text from.")
            return
            
        output_file = self.text_output_edit.text().strip()
        if not output_file:
            output_file = "extracted_text.txt"
            
        params = {
            'files': self.selected_files,
            'output_file': output_file,
            'preserve_layout': self.preserve_layout_cb.isChecked()
        }
        
        self.operation_requested.emit('extract_text', params)
        
    def on_extract_images_clicked(self):
        """Handle extract images button click."""
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select files to extract images from.")
            return
            
        output_dir = self.images_output_edit.text().strip()
        if not output_dir:
            output_dir = "images/"
            
        params = {
            'files': self.selected_files,
            'output_dir': output_dir,
            'format': self.image_format_combo.currentText()
        }
        
        self.operation_requested.emit('extract_images', params)
        
    def on_extract_tables_clicked(self):
        """Handle extract tables button click."""
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select files to extract tables from.")
            return
            
        output_file = self.tables_output_edit.text().strip()
        if not output_file:
            output_file = "tables.csv"
            
        params = {
            'files': self.selected_files,
            'output_file': output_file,
            'format': self.table_format_combo.currentText()
        }
        
        self.operation_requested.emit('extract_tables', params)


class OperationTabs(QTabWidget):
    """Main operation tabs widget."""
    
    operation_requested = pyqtSignal(str, dict)
    
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface."""
        # PDF Operations tab
        self.pdf_ops_tab = PDFOperationsTab(self.config)
        self.addTab(self.pdf_ops_tab, "PDF Operations")
        
        # Content Extraction tab
        self.content_tab = ContentExtractionTab(self.config)
        self.addTab(self.content_tab, "Content Extraction")
        
        # AI Services tab
        self.ai_tab = AIServicesTab(self.config)
        self.addTab(self.ai_tab, "AI Services")
        
        # Format Conversion tab
        self.format_tab = FormatConversionTab(self.config)
        self.addTab(self.format_tab, "Format Conversion")
        
        # Security & Optimization tab
        self.security_tab = SecurityOptimizationTab(self.config)
        self.addTab(self.security_tab, "Security & Optimization")
        
    def setup_connections(self):
        """Set up signal connections."""
        self.pdf_ops_tab.operation_requested.connect(self.operation_requested)
        self.content_tab.operation_requested.connect(self.operation_requested)
        self.ai_tab.operation_requested.connect(self.operation_requested)
        self.format_tab.operation_requested.connect(self.operation_requested)
        self.security_tab.operation_requested.connect(self.operation_requested)
        
    def set_selected_files(self, files: List[Path]):
        """Set the selected files for all tabs."""
        self.pdf_ops_tab.set_selected_files(files)
        self.content_tab.set_selected_files(files)
        self.ai_tab.set_selected_files(files)
        self.format_tab.set_selected_files(files)
        self.security_tab.set_selected_files(files)