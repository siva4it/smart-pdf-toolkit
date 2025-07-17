"""
Settings dialog for Smart PDF Toolkit GUI.
"""

from pathlib import Path
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLabel,
    QPushButton, QLineEdit, QCheckBox, QComboBox, QSpinBox, QGroupBox,
    QFormLayout, QFileDialog, QMessageBox, QTextEdit, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..core.config import Config


class GeneralSettingsTab(QWidget):
    """General settings tab."""
    
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Output Settings
        output_group = QGroupBox("Output Settings")
        output_layout = QFormLayout(output_group)
        
        self.output_dir_edit = QLineEdit()
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_edit)
        
        self.output_dir_browse_btn = QPushButton("Browse...")
        self.output_dir_browse_btn.clicked.connect(self.browse_output_dir)
        output_dir_layout.addWidget(self.output_dir_browse_btn)
        
        output_layout.addRow("Default output directory:", output_dir_layout)
        
        self.temp_dir_edit = QLineEdit()
        temp_dir_layout = QHBoxLayout()
        temp_dir_layout.addWidget(self.temp_dir_edit)
        
        self.temp_dir_browse_btn = QPushButton("Browse...")
        self.temp_dir_browse_btn.clicked.connect(self.browse_temp_dir)
        temp_dir_layout.addWidget(self.temp_dir_browse_btn)
        
        output_layout.addRow("Temporary directory:", temp_dir_layout)
        
        self.overwrite_files_cb = QCheckBox("Overwrite existing files")
        output_layout.addRow(self.overwrite_files_cb)
        
        layout.addWidget(output_group)
        
        # Performance Settings
        performance_group = QGroupBox("Performance Settings")
        performance_layout = QFormLayout(performance_group)
        
        self.max_workers_spinbox = QSpinBox()
        self.max_workers_spinbox.setRange(1, 16)
        self.max_workers_spinbox.setValue(4)
        performance_layout.addRow("Max worker threads:", self.max_workers_spinbox)
        
        self.memory_limit_spinbox = QSpinBox()
        self.memory_limit_spinbox.setRange(256, 8192)
        self.memory_limit_spinbox.setValue(1024)
        self.memory_limit_spinbox.setSuffix(" MB")
        performance_layout.addRow("Memory limit:", self.memory_limit_spinbox)
        
        self.enable_caching_cb = QCheckBox("Enable file caching")
        self.enable_caching_cb.setChecked(True)
        performance_layout.addRow(self.enable_caching_cb)
        
        layout.addWidget(performance_group)
        
        # UI Settings
        ui_group = QGroupBox("User Interface")
        ui_layout = QFormLayout(ui_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Light", "Dark"])
        ui_layout.addRow("Theme:", self.theme_combo)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Spanish", "French", "German"])
        ui_layout.addRow("Language:", self.language_combo)
        
        self.show_tooltips_cb = QCheckBox("Show tooltips")
        self.show_tooltips_cb.setChecked(True)
        ui_layout.addRow(self.show_tooltips_cb)
        
        self.confirm_operations_cb = QCheckBox("Confirm destructive operations")
        self.confirm_operations_cb.setChecked(True)
        ui_layout.addRow(self.confirm_operations_cb)
        
        layout.addWidget(ui_group)
        
        layout.addStretch()
        
    def load_settings(self):
        """Load settings from config."""
        self.output_dir_edit.setText(str(self.config.output_dir))
        self.temp_dir_edit.setText(str(self.config.temp_dir))
        # Load other settings as needed
        
    def save_settings(self):
        """Save settings to config."""
        self.config.output_dir = Path(self.output_dir_edit.text())
        self.config.temp_dir = Path(self.temp_dir_edit.text())
        # Save other settings as needed
        
    def browse_output_dir(self):
        """Browse for output directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", str(self.config.output_dir)
        )
        if directory:
            self.output_dir_edit.setText(directory)
            
    def browse_temp_dir(self):
        """Browse for temporary directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Temporary Directory", str(self.config.temp_dir)
        )
        if directory:
            self.temp_dir_edit.setText(directory)


class OCRSettingsTab(QWidget):
    """OCR settings tab."""
    
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Tesseract Settings
        tesseract_group = QGroupBox("Tesseract OCR Settings")
        tesseract_layout = QFormLayout(tesseract_group)
        
        self.tesseract_path_edit = QLineEdit()
        tesseract_path_layout = QHBoxLayout()
        tesseract_path_layout.addWidget(self.tesseract_path_edit)
        
        self.tesseract_browse_btn = QPushButton("Browse...")
        self.tesseract_browse_btn.clicked.connect(self.browse_tesseract_path)
        tesseract_path_layout.addWidget(self.tesseract_browse_btn)
        
        tesseract_layout.addRow("Tesseract executable:", tesseract_path_layout)
        
        self.default_language_combo = QComboBox()
        self.default_language_combo.addItems([
            "eng", "spa", "fra", "deu", "ita", "por", "rus", "chi_sim", "jpn", "kor"
        ])
        tesseract_layout.addRow("Default language:", self.default_language_combo)
        
        self.ocr_confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.ocr_confidence_slider.setRange(0, 100)
        self.ocr_confidence_slider.setValue(70)
        self.ocr_confidence_label = QLabel("70%")
        
        confidence_layout = QHBoxLayout()
        confidence_layout.addWidget(self.ocr_confidence_slider)
        confidence_layout.addWidget(self.ocr_confidence_label)
        
        tesseract_layout.addRow("Minimum confidence:", confidence_layout)
        
        self.preprocess_images_cb = QCheckBox("Preprocess images for better OCR")
        self.preprocess_images_cb.setChecked(True)
        tesseract_layout.addRow(self.preprocess_images_cb)
        
        layout.addWidget(tesseract_group)
        
        # Image Preprocessing
        preprocessing_group = QGroupBox("Image Preprocessing")
        preprocessing_layout = QFormLayout(preprocessing_group)
        
        self.enhance_contrast_cb = QCheckBox("Enhance contrast")
        preprocessing_layout.addRow(self.enhance_contrast_cb)
        
        self.remove_noise_cb = QCheckBox("Remove noise")
        preprocessing_layout.addRow(self.remove_noise_cb)
        
        self.deskew_images_cb = QCheckBox("Deskew images")
        preprocessing_layout.addRow(self.deskew_images_cb)
        
        layout.addWidget(preprocessing_group)
        
        layout.addStretch()
        
        # Connect signals
        self.ocr_confidence_slider.valueChanged.connect(
            lambda v: self.ocr_confidence_label.setText(f"{v}%")
        )
        
    def load_settings(self):
        """Load settings from config."""
        # Load OCR settings from config
        pass
        
    def save_settings(self):
        """Save settings to config."""
        # Save OCR settings to config
        pass
        
    def browse_tesseract_path(self):
        """Browse for Tesseract executable."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Tesseract Executable", "", "Executable Files (*.exe);;All Files (*)"
        )
        if file_path:
            self.tesseract_path_edit.setText(file_path)


class AISettingsTab(QWidget):
    """AI services settings tab."""
    
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # API Settings
        api_group = QGroupBox("AI Service API Settings")
        api_layout = QFormLayout(api_group)
        
        self.openai_api_key_edit = QLineEdit()
        self.openai_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_api_key_edit.setPlaceholderText("Enter OpenAI API key...")
        api_layout.addRow("OpenAI API Key:", self.openai_api_key_edit)
        
        self.default_model_combo = QComboBox()
        self.default_model_combo.addItems([
            "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"
        ])
        api_layout.addRow("Default model:", self.default_model_combo)
        
        self.max_tokens_spinbox = QSpinBox()
        self.max_tokens_spinbox.setRange(100, 4000)
        self.max_tokens_spinbox.setValue(1000)
        api_layout.addRow("Max tokens:", self.max_tokens_spinbox)
        
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setRange(0, 100)
        self.temperature_slider.setValue(70)
        self.temperature_label = QLabel("0.7")
        
        temperature_layout = QHBoxLayout()
        temperature_layout.addWidget(self.temperature_slider)
        temperature_layout.addWidget(self.temperature_label)
        
        api_layout.addRow("Temperature:", temperature_layout)
        
        layout.addWidget(api_group)
        
        # Processing Settings
        processing_group = QGroupBox("AI Processing Settings")
        processing_layout = QFormLayout(processing_group)
        
        self.chunk_size_spinbox = QSpinBox()
        self.chunk_size_spinbox.setRange(500, 5000)
        self.chunk_size_spinbox.setValue(2000)
        processing_layout.addRow("Text chunk size:", self.chunk_size_spinbox)
        
        self.enable_caching_cb = QCheckBox("Cache AI responses")
        self.enable_caching_cb.setChecked(True)
        processing_layout.addRow(self.enable_caching_cb)
        
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(10, 300)
        self.timeout_spinbox.setValue(60)
        self.timeout_spinbox.setSuffix(" seconds")
        processing_layout.addRow("Request timeout:", self.timeout_spinbox)
        
        layout.addWidget(processing_group)
        
        layout.addStretch()
        
        # Connect signals
        self.temperature_slider.valueChanged.connect(
            lambda v: self.temperature_label.setText(f"{v/100:.1f}")
        )
        
    def load_settings(self):
        """Load settings from config."""
        # Load AI settings from config
        pass
        
    def save_settings(self):
        """Save settings to config."""
        # Save AI settings to config
        pass


class SettingsDialog(QDialog):
    """Main settings dialog."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # General settings tab
        self.general_tab = GeneralSettingsTab(self.config)
        self.tab_widget.addTab(self.general_tab, "General")
        
        # OCR settings tab
        self.ocr_tab = OCRSettingsTab(self.config)
        self.tab_widget.addTab(self.ocr_tab, "OCR")
        
        # AI settings tab
        self.ai_tab = AISettingsTab(self.config)
        self.tab_widget.addTab(self.ai_tab, "AI Services")
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept_settings)
        self.ok_btn.setDefault(True)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
        
    def accept_settings(self):
        """Accept and save settings."""
        try:
            # Save settings from all tabs
            self.general_tab.save_settings()
            self.ocr_tab.save_settings()
            self.ai_tab.save_settings()
            
            # Save config to file
            self.config.save()
            
            # Emit signal that settings changed
            self.settings_changed.emit()
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save settings: {str(e)}"
            )
            
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reset config to defaults
            self.config.reset_to_defaults()
            
            # Reload settings in all tabs
            self.general_tab.load_settings()
            self.ocr_tab.load_settings()
            self.ai_tab.load_settings()