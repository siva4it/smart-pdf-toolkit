"""
Format Conversion tab for Smart PDF Toolkit GUI.
"""

from pathlib import Path
from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QLineEdit, QCheckBox, QGroupBox, QFormLayout, QSpinBox, QSlider,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..core.config import Config


class FormatConversionTab(QWidget):
    """Tab for format conversion operations."""
    
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
        
        # PDF to Images section
        pdf_to_images_group = QGroupBox("PDF to Images")
        pdf_to_images_layout = QFormLayout(pdf_to_images_group)
        
        self.image_format_combo = QComboBox()
        self.image_format_combo.addItems(["PNG", "JPEG", "TIFF", "BMP"])
        pdf_to_images_layout.addRow("Image format:", self.image_format_combo)
        
        self.image_quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.image_quality_slider.setRange(1, 100)
        self.image_quality_slider.setValue(95)
        self.image_quality_label = QLabel("95%")
        
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(self.image_quality_slider)
        quality_layout.addWidget(self.image_quality_label)
        pdf_to_images_layout.addRow("Image quality:", quality_layout)
        
        self.image_dpi_spinbox = QSpinBox()
        self.image_dpi_spinbox.setRange(72, 600)
        self.image_dpi_spinbox.setValue(300)
        self.image_dpi_spinbox.setSuffix(" DPI")
        pdf_to_images_layout.addRow("Resolution:", self.image_dpi_spinbox)
        
        self.images_output_dir_edit = QLineEdit()
        self.images_output_dir_edit.setPlaceholderText("images/")
        
        images_output_layout = QHBoxLayout()
        images_output_layout.addWidget(self.images_output_dir_edit)
        
        self.images_browse_btn = QPushButton("Browse...")
        images_output_layout.addWidget(self.images_browse_btn)
        
        pdf_to_images_layout.addRow("Output directory:", images_output_layout)
        
        self.pdf_to_images_btn = QPushButton("Convert to Images")
        self.pdf_to_images_btn.setEnabled(False)
        pdf_to_images_layout.addRow(self.pdf_to_images_btn)
        
        layout.addWidget(pdf_to_images_group)
        
        # Images to PDF section
        images_to_pdf_group = QGroupBox("Images to PDF")
        images_to_pdf_layout = QFormLayout(images_to_pdf_group)
        
        self.images_input_edit = QLineEdit()
        self.images_input_edit.setPlaceholderText("Select image files...")
        self.images_input_edit.setReadOnly(True)
        
        images_input_layout = QHBoxLayout()
        images_input_layout.addWidget(self.images_input_edit)
        
        self.select_images_btn = QPushButton("Select Images...")
        images_input_layout.addWidget(self.select_images_btn)
        
        images_to_pdf_layout.addRow("Image files:", images_input_layout)
        
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["A4", "Letter", "Legal", "A3", "A5", "Custom"])
        images_to_pdf_layout.addRow("Page size:", self.page_size_combo)
        
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItems(["Portrait", "Landscape", "Auto"])
        images_to_pdf_layout.addRow("Orientation:", self.orientation_combo)
        
        self.images_to_pdf_output_edit = QLineEdit()
        self.images_to_pdf_output_edit.setPlaceholderText("output.pdf")
        images_to_pdf_layout.addRow("Output file:", self.images_to_pdf_output_edit)
        
        self.images_to_pdf_btn = QPushButton("Convert to PDF")
        self.images_to_pdf_btn.setEnabled(False)
        images_to_pdf_layout.addRow(self.images_to_pdf_btn)
        
        layout.addWidget(images_to_pdf_group)
        
        # Office Documents section
        office_group = QGroupBox("Office Document Conversion")
        office_layout = QFormLayout(office_group)
        
        self.office_format_combo = QComboBox()
        self.office_format_combo.addItems(["Word (.docx)", "Excel (.xlsx)", "PowerPoint (.pptx)"])
        office_layout.addRow("Convert to:", self.office_format_combo)
        
        self.preserve_images_cb = QCheckBox("Preserve images")
        self.preserve_images_cb.setChecked(True)
        office_layout.addRow(self.preserve_images_cb)
        
        self.preserve_tables_cb = QCheckBox("Preserve tables")
        self.preserve_tables_cb.setChecked(True)
        office_layout.addRow(self.preserve_tables_cb)
        
        self.office_output_edit = QLineEdit()
        self.office_output_edit.setPlaceholderText("document.docx")
        office_layout.addRow("Output file:", self.office_output_edit)
        
        self.pdf_to_office_btn = QPushButton("Convert to Office")
        self.pdf_to_office_btn.setEnabled(False)
        office_layout.addRow(self.pdf_to_office_btn)
        
        layout.addWidget(office_group)
        
        # HTML Conversion section
        html_group = QGroupBox("HTML Conversion")
        html_layout = QFormLayout(html_group)
        
        self.include_css_cb = QCheckBox("Include CSS styling")
        self.include_css_cb.setChecked(True)
        html_layout.addRow(self.include_css_cb)
        
        self.embed_images_cb = QCheckBox("Embed images")
        self.embed_images_cb.setChecked(False)
        html_layout.addRow(self.embed_images_cb)
        
        self.html_output_edit = QLineEdit()
        self.html_output_edit.setPlaceholderText("document.html")
        html_layout.addRow("Output file:", self.html_output_edit)
        
        self.pdf_to_html_btn = QPushButton("Convert to HTML")
        self.pdf_to_html_btn.setEnabled(False)
        html_layout.addRow(self.pdf_to_html_btn)
        
        layout.addWidget(html_group)
        
        layout.addStretch()
        
        # Store selected image files
        self.selected_image_files: List[Path] = []
        
    def setup_connections(self):
        """Set up signal connections."""
        self.image_quality_slider.valueChanged.connect(self.on_quality_changed)
        self.images_browse_btn.clicked.connect(self.browse_output_directory)
        self.select_images_btn.clicked.connect(self.select_image_files)
        
        self.pdf_to_images_btn.clicked.connect(self.on_pdf_to_images_clicked)
        self.images_to_pdf_btn.clicked.connect(self.on_images_to_pdf_clicked)
        self.pdf_to_office_btn.clicked.connect(self.on_pdf_to_office_clicked)
        self.pdf_to_html_btn.clicked.connect(self.on_pdf_to_html_clicked)
        
    def set_selected_files(self, files: List[Path]):
        """Set the selected files."""
        self.selected_files = files
        self.update_button_states()
        
    def update_button_states(self):
        """Update button enabled states based on selection."""
        has_files = len(self.selected_files) > 0
        has_images = len(self.selected_image_files) > 0
        
        self.pdf_to_images_btn.setEnabled(has_files)
        self.images_to_pdf_btn.setEnabled(has_images)
        self.pdf_to_office_btn.setEnabled(has_files)
        self.pdf_to_html_btn.setEnabled(has_files)
        
    def on_quality_changed(self, value: int):
        """Handle quality slider change."""
        self.image_quality_label.setText(f"{value}%")
        
    def browse_output_directory(self):
        """Browse for output directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            str(Path.home())
        )
        
        if directory:
            self.images_output_dir_edit.setText(directory)
            
    def select_image_files(self):
        """Select image files for conversion to PDF."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Image Files",
            str(Path.home()),
            "Image Files (*.png *.jpg *.jpeg *.tiff *.bmp);;All Files (*)"
        )
        
        if files:
            self.selected_image_files = [Path(f) for f in files]
            self.images_input_edit.setText(f"{len(files)} image(s) selected")
            self.update_button_states()
            
    def on_pdf_to_images_clicked(self):
        """Handle PDF to images conversion."""
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select PDF files to convert.")
            return
            
        output_dir = self.images_output_dir_edit.text().strip()
        if not output_dir:
            output_dir = "images/"
            
        params = {
            'files': self.selected_files,
            'format': self.image_format_combo.currentText(),
            'quality': self.image_quality_slider.value(),
            'dpi': self.image_dpi_spinbox.value(),
            'output_dir': output_dir
        }
        
        self.operation_requested.emit('pdf_to_images', params)
        
    def on_images_to_pdf_clicked(self):
        """Handle images to PDF conversion."""
        if not self.selected_image_files:
            QMessageBox.warning(self, "Warning", "Please select image files to convert.")
            return
            
        output_file = self.images_to_pdf_output_edit.text().strip()
        if not output_file:
            output_file = "output.pdf"
            
        params = {
            'image_files': self.selected_image_files,
            'page_size': self.page_size_combo.currentText(),
            'orientation': self.orientation_combo.currentText(),
            'output_file': output_file
        }
        
        self.operation_requested.emit('images_to_pdf', params)
        
    def on_pdf_to_office_clicked(self):
        """Handle PDF to Office conversion."""
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select PDF files to convert.")
            return
            
        format_text = self.office_format_combo.currentText()
        format_map = {
            "Word (.docx)": "docx",
            "Excel (.xlsx)": "xlsx", 
            "PowerPoint (.pptx)": "pptx"
        }
        
        output_format = format_map.get(format_text, "docx")
        output_file = self.office_output_edit.text().strip()
        if not output_file:
            extensions = {"docx": ".docx", "xlsx": ".xlsx", "pptx": ".pptx"}
            output_file = f"document{extensions[output_format]}"
            
        params = {
            'files': self.selected_files,
            'format': output_format,
            'preserve_images': self.preserve_images_cb.isChecked(),
            'preserve_tables': self.preserve_tables_cb.isChecked(),
            'output_file': output_file
        }
        
        self.operation_requested.emit('pdf_to_office', params)
        
    def on_pdf_to_html_clicked(self):
        """Handle PDF to HTML conversion."""
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select PDF files to convert.")
            return
            
        output_file = self.html_output_edit.text().strip()
        if not output_file:
            output_file = "document.html"
            
        params = {
            'files': self.selected_files,
            'include_css': self.include_css_cb.isChecked(),
            'embed_images': self.embed_images_cb.isChecked(),
            'output_file': output_file
        }
        
        self.operation_requested.emit('pdf_to_html', params)