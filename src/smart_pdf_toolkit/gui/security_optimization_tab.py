"""
Security and Optimization tab for Smart PDF Toolkit GUI.
"""

from pathlib import Path
from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QLineEdit, QCheckBox, QGroupBox, QFormLayout, QSpinBox, QSlider,
    QMessageBox, QPasswordLineEdit, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..core.config import Config


class SecurityOptimizationTab(QWidget):
    """Tab for security and optimization operations."""
    
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
        
        # Password Protection section
        password_group = QGroupBox("Password Protection")
        password_layout = QFormLayout(password_group)
        
        self.user_password_edit = QLineEdit()
        self.user_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.user_password_edit.setPlaceholderText("Enter user password...")
        password_layout.addRow("User password:", self.user_password_edit)
        
        self.owner_password_edit = QLineEdit()
        self.owner_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.owner_password_edit.setPlaceholderText("Enter owner password...")
        password_layout.addRow("Owner password:", self.owner_password_edit)
        
        # Permissions
        permissions_layout = QVBoxLayout()
        self.allow_printing_cb = QCheckBox("Allow printing")
        self.allow_copying_cb = QCheckBox("Allow copying text")
        self.allow_editing_cb = QCheckBox("Allow editing")
        self.allow_annotations_cb = QCheckBox("Allow annotations")
        
        permissions_layout.addWidget(self.allow_printing_cb)
        permissions_layout.addWidget(self.allow_copying_cb)
        permissions_layout.addWidget(self.allow_editing_cb)
        permissions_layout.addWidget(self.allow_annotations_cb)
        
        password_layout.addRow("Permissions:", permissions_layout)
        
        self.password_output_edit = QLineEdit()
        self.password_output_edit.setPlaceholderText("protected.pdf")
        password_layout.addRow("Output file:", self.password_output_edit)
        
        password_buttons_layout = QHBoxLayout()
        self.add_password_btn = QPushButton("Add Password")
        self.add_password_btn.setEnabled(False)
        self.remove_password_btn = QPushButton("Remove Password")
        self.remove_password_btn.setEnabled(False)
        
        password_buttons_layout.addWidget(self.add_password_btn)
        password_buttons_layout.addWidget(self.remove_password_btn)
        
        password_layout.addRow(password_buttons_layout)
        
        layout.addWidget(password_group)
        
        # Watermark section
        watermark_group = QGroupBox("Watermark")
        watermark_layout = QFormLayout(watermark_group)
        
        self.watermark_type_combo = QComboBox()
        self.watermark_type_combo.addItems(["Text", "Image"])
        watermark_layout.addRow("Watermark type:", self.watermark_type_combo)
        
        self.watermark_text_edit = QLineEdit()
        self.watermark_text_edit.setPlaceholderText("Enter watermark text...")
        watermark_layout.addRow("Watermark text:", self.watermark_text_edit)
        
        self.watermark_image_edit = QLineEdit()
        self.watermark_image_edit.setPlaceholderText("Select watermark image...")
        self.watermark_image_edit.setEnabled(False)
        
        watermark_image_layout = QHBoxLayout()
        watermark_image_layout.addWidget(self.watermark_image_edit)
        
        self.watermark_browse_btn = QPushButton("Browse...")
        self.watermark_browse_btn.setEnabled(False)
        watermark_image_layout.addWidget(self.watermark_browse_btn)
        
        watermark_layout.addRow("Watermark image:", watermark_image_layout)
        
        self.watermark_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.watermark_opacity_slider.setRange(10, 100)
        self.watermark_opacity_slider.setValue(50)
        self.watermark_opacity_label = QLabel("50%")
        
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(self.watermark_opacity_slider)
        opacity_layout.addWidget(self.watermark_opacity_label)
        
        watermark_layout.addRow("Opacity:", opacity_layout)
        
        self.watermark_position_combo = QComboBox()
        self.watermark_position_combo.addItems([
            "Center", "Top Left", "Top Right", "Bottom Left", "Bottom Right"
        ])
        watermark_layout.addRow("Position:", self.watermark_position_combo)
        
        self.watermark_output_edit = QLineEdit()
        self.watermark_output_edit.setPlaceholderText("watermarked.pdf")
        watermark_layout.addRow("Output file:", self.watermark_output_edit)
        
        self.add_watermark_btn = QPushButton("Add Watermark")
        self.add_watermark_btn.setEnabled(False)
        watermark_layout.addRow(self.add_watermark_btn)
        
        layout.addWidget(watermark_group)
        
        # Optimization section
        optimization_group = QGroupBox("PDF Optimization")
        optimization_layout = QFormLayout(optimization_group)
        
        self.compression_level_combo = QComboBox()
        self.compression_level_combo.addItems(["Low", "Medium", "High", "Maximum"])
        optimization_layout.addRow("Compression level:", self.compression_level_combo)
        
        self.optimize_images_cb = QCheckBox("Optimize images")
        self.optimize_images_cb.setChecked(True)
        optimization_layout.addRow(self.optimize_images_cb)
        
        self.remove_metadata_cb = QCheckBox("Remove metadata")
        optimization_layout.addRow(self.remove_metadata_cb)
        
        self.linearize_cb = QCheckBox("Linearize for web")
        optimization_layout.addRow(self.linearize_cb)
        
        self.image_quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.image_quality_slider.setRange(10, 100)
        self.image_quality_slider.setValue(80)
        self.image_quality_label = QLabel("80%")
        
        image_quality_layout = QHBoxLayout()
        image_quality_layout.addWidget(self.image_quality_slider)
        image_quality_layout.addWidget(self.image_quality_label)
        
        optimization_layout.addRow("Image quality:", image_quality_layout)
        
        self.optimization_output_edit = QLineEdit()
        self.optimization_output_edit.setPlaceholderText("optimized.pdf")
        optimization_layout.addRow("Output file:", self.optimization_output_edit)
        
        self.optimize_btn = QPushButton("Optimize PDF")
        self.optimize_btn.setEnabled(False)
        optimization_layout.addRow(self.optimize_btn)
        
        layout.addWidget(optimization_group)
        
        # Digital Signature section
        signature_group = QGroupBox("Digital Signature")
        signature_layout = QFormLayout(signature_group)
        
        self.certificate_edit = QLineEdit()
        self.certificate_edit.setPlaceholderText("Select certificate file...")
        
        cert_layout = QHBoxLayout()
        cert_layout.addWidget(self.certificate_edit)
        
        self.cert_browse_btn = QPushButton("Browse...")
        cert_layout.addWidget(self.cert_browse_btn)
        
        signature_layout.addRow("Certificate:", cert_layout)
        
        self.cert_password_edit = QLineEdit()
        self.cert_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.cert_password_edit.setPlaceholderText("Certificate password...")
        signature_layout.addRow("Password:", self.cert_password_edit)
        
        self.signature_reason_edit = QLineEdit()
        self.signature_reason_edit.setPlaceholderText("Reason for signing...")
        signature_layout.addRow("Reason:", self.signature_reason_edit)
        
        self.signature_location_edit = QLineEdit()
        self.signature_location_edit.setPlaceholderText("Location...")
        signature_layout.addRow("Location:", self.signature_location_edit)
        
        self.signature_output_edit = QLineEdit()
        self.signature_output_edit.setPlaceholderText("signed.pdf")
        signature_layout.addRow("Output file:", self.signature_output_edit)
        
        self.sign_btn = QPushButton("Sign PDF")
        self.sign_btn.setEnabled(False)
        signature_layout.addRow(self.sign_btn)
        
        layout.addWidget(signature_group)
        
        layout.addStretch()
        
    def setup_connections(self):
        """Set up signal connections."""
        self.watermark_type_combo.currentTextChanged.connect(self.on_watermark_type_changed)
        self.watermark_opacity_slider.valueChanged.connect(self.on_watermark_opacity_changed)
        self.image_quality_slider.valueChanged.connect(self.on_image_quality_changed)
        
        self.add_password_btn.clicked.connect(self.on_add_password_clicked)
        self.remove_password_btn.clicked.connect(self.on_remove_password_clicked)
        self.add_watermark_btn.clicked.connect(self.on_add_watermark_clicked)
        self.optimize_btn.clicked.connect(self.on_optimize_clicked)
        self.sign_btn.clicked.connect(self.on_sign_clicked)
        
    def set_selected_files(self, files: List[Path]):
        """Set the selected files."""
        self.selected_files = files
        self.update_button_states()
        
    def update_button_states(self):
        """Update button enabled states based on selection."""
        has_files = len(self.selected_files) > 0
        
        self.add_password_btn.setEnabled(has_files)
        self.remove_password_btn.setEnabled(has_files)
        self.add_watermark_btn.setEnabled(has_files)
        self.optimize_btn.setEnabled(has_files)
        self.sign_btn.setEnabled(has_files)
        
    def on_watermark_type_changed(self, text: str):
        """Handle watermark type change."""
        is_image = text == "Image"
        self.watermark_text_edit.setEnabled(not is_image)
        self.watermark_image_edit.setEnabled(is_image)
        self.watermark_browse_btn.setEnabled(is_image)
        
    def on_watermark_opacity_changed(self, value: int):
        """Handle watermark opacity change."""
        self.watermark_opacity_label.setText(f"{value}%")
        
    def on_image_quality_changed(self, value: int):
        """Handle image quality change."""
        self.image_quality_label.setText(f"{value}%")
        
    def on_add_password_clicked(self):
        """Handle add password button click."""
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select files to protect.")
            return
            
        user_password = self.user_password_edit.text().strip()
        owner_password = self.owner_password_edit.text().strip()
        
        if not user_password and not owner_password:
            QMessageBox.warning(self, "Warning", "Please enter at least one password.")
            return
            
        output_file = self.password_output_edit.text().strip()
        if not output_file:
            output_file = "protected.pdf"
            
        permissions = {
            'printing': self.allow_printing_cb.isChecked(),
            'copying': self.allow_copying_cb.isChecked(),
            'editing': self.allow_editing_cb.isChecked(),
            'annotations': self.allow_annotations_cb.isChecked()
        }
        
        params = {
            'files': self.selected_files,
            'user_password': user_password if user_password else None,
            'owner_password': owner_password if owner_password else None,
            'permissions': permissions,
            'output_file': output_file
        }
        
        self.operation_requested.emit('add_password', params)
        
    def on_remove_password_clicked(self):
        """Handle remove password button click."""
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select files to unprotect.")
            return
            
        # For removing passwords, we need the current password
        current_password = self.user_password_edit.text().strip()
        if not current_password:
            QMessageBox.warning(self, "Warning", "Please enter the current password.")
            return
            
        params = {
            'files': self.selected_files,
            'password': current_password
        }
        
        self.operation_requested.emit('remove_password', params)
        
    def on_add_watermark_clicked(self):
        """Handle add watermark button click."""
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select files to watermark.")
            return
            
        watermark_type = self.watermark_type_combo.currentText().lower()
        
        if watermark_type == "text":
            watermark_content = self.watermark_text_edit.text().strip()
            if not watermark_content:
                QMessageBox.warning(self, "Warning", "Please enter watermark text.")
                return
        else:
            watermark_content = self.watermark_image_edit.text().strip()
            if not watermark_content:
                QMessageBox.warning(self, "Warning", "Please select watermark image.")
                return
                
        output_file = self.watermark_output_edit.text().strip()
        if not output_file:
            output_file = "watermarked.pdf"
            
        params = {
            'files': self.selected_files,
            'watermark_type': watermark_type,
            'watermark_content': watermark_content,
            'opacity': self.watermark_opacity_slider.value() / 100.0,
            'position': self.watermark_position_combo.currentText().lower().replace(' ', '_'),
            'output_file': output_file
        }
        
        self.operation_requested.emit('add_watermark', params)
        
    def on_optimize_clicked(self):
        """Handle optimize button click."""
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select files to optimize.")
            return
            
        output_file = self.optimization_output_edit.text().strip()
        if not output_file:
            output_file = "optimized.pdf"
            
        params = {
            'files': self.selected_files,
            'compression_level': self.compression_level_combo.currentText().lower(),
            'optimize_images': self.optimize_images_cb.isChecked(),
            'remove_metadata': self.remove_metadata_cb.isChecked(),
            'linearize': self.linearize_cb.isChecked(),
            'image_quality': self.image_quality_slider.value() / 100.0,
            'output_file': output_file
        }
        
        self.operation_requested.emit('optimize', params)
        
    def on_sign_clicked(self):
        """Handle sign button click."""
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select files to sign.")
            return
            
        certificate = self.certificate_edit.text().strip()
        if not certificate:
            QMessageBox.warning(self, "Warning", "Please select a certificate file.")
            return
            
        cert_password = self.cert_password_edit.text().strip()
        if not cert_password:
            QMessageBox.warning(self, "Warning", "Please enter certificate password.")
            return
            
        output_file = self.signature_output_edit.text().strip()
        if not output_file:
            output_file = "signed.pdf"
            
        params = {
            'files': self.selected_files,
            'certificate': certificate,
            'password': cert_password,
            'reason': self.signature_reason_edit.text().strip(),
            'location': self.signature_location_edit.text().strip(),
            'output_file': output_file
        }
        
        self.operation_requested.emit('sign', params)