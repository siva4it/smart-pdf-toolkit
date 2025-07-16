"""
Batch processing dialog for Smart PDF Toolkit GUI.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QComboBox, QLineEdit, QCheckBox,
    QGroupBox, QFormLayout, QFileDialog, QMessageBox, QTextEdit,
    QProgressBar, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont

from ..core.config import Config


class BatchJobItem:
    """Represents a batch processing job."""
    
    def __init__(self, files: List[Path], operation: str, params: Dict[str, Any]):
        self.files = files
        self.operation = operation
        self.params = params
        self.status = "Pending"
        self.progress = 0
        self.error_message = ""
        
    def __str__(self):
        return f"{self.operation} - {len(self.files)} file(s)"


class BatchJobWidget(QWidget):
    """Widget for configuring batch jobs."""
    
    job_added = pyqtSignal(object)  # BatchJobItem
    
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.selected_files: List[Path] = []
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # File Selection
        files_group = QGroupBox("Files")
        files_layout = QVBoxLayout(files_group)
        
        file_buttons_layout = QHBoxLayout()
        
        self.add_files_btn = QPushButton("Add Files...")
        self.add_folder_btn = QPushButton("Add Folder...")
        self.clear_files_btn = QPushButton("Clear Files")
        
        file_buttons_layout.addWidget(self.add_files_btn)
        file_buttons_layout.addWidget(self.add_folder_btn)
        file_buttons_layout.addWidget(self.clear_files_btn)
        file_buttons_layout.addStretch()
        
        files_layout.addLayout(file_buttons_layout)
        
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(120)
        files_layout.addWidget(self.files_list)
        
        layout.addWidget(files_group)
        
        # Operation Selection
        operation_group = QGroupBox("Operation")
        operation_layout = QFormLayout(operation_group)
        
        self.operation_combo = QComboBox()
        self.operation_combo.addItems([
            "Extract Text", "Extract Images", "Extract Tables",
            "Merge PDFs", "Split PDFs", "Rotate Pages",
            "Add Password", "Remove Password", "Add Watermark",
            "Optimize PDF", "Convert to Images", "OCR Processing",
            "AI Summarization", "AI Analysis"
        ])
        operation_layout.addRow("Operation:", self.operation_combo)
        
        # Dynamic parameters area
        self.params_widget = QWidget()
        self.params_layout = QFormLayout(self.params_widget)
        operation_layout.addRow("Parameters:", self.params_widget)
        
        layout.addWidget(operation_group)
        
        # Output Settings
        output_group = QGroupBox("Output")
        output_layout = QFormLayout(output_group)
        
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText(str(self.config.output_dir))
        
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_edit)
        
        self.output_browse_btn = QPushButton("Browse...")
        output_dir_layout.addWidget(self.output_browse_btn)
        
        output_layout.addRow("Output directory:", output_dir_layout)
        
        self.preserve_structure_cb = QCheckBox("Preserve folder structure")
        output_layout.addRow(self.preserve_structure_cb)
        
        layout.addWidget(output_group)
        
        # Add Job Button
        self.add_job_btn = QPushButton("Add Job to Queue")
        self.add_job_btn.setEnabled(False)
        layout.addWidget(self.add_job_btn)
        
        # Update parameters when operation changes
        self.update_parameters()
        
    def setup_connections(self):
        """Set up signal connections."""
        self.add_files_btn.clicked.connect(self.add_files)
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.clear_files_btn.clicked.connect(self.clear_files)
        self.output_browse_btn.clicked.connect(self.browse_output_dir)
        self.operation_combo.currentTextChanged.connect(self.update_parameters)
        self.add_job_btn.clicked.connect(self.add_job)
        
    def add_files(self):
        """Add files to the batch."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files", str(Path.home()),
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if files:
            new_files = [Path(f) for f in files if Path(f) not in self.selected_files]
            self.selected_files.extend(new_files)
            self.update_files_list()
            
    def add_folder(self):
        """Add all PDF files from a folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder", str(Path.home())
        )
        
        if folder:
            folder_path = Path(folder)
            pdf_files = list(folder_path.rglob("*.pdf"))
            new_files = [f for f in pdf_files if f not in self.selected_files]
            self.selected_files.extend(new_files)
            self.update_files_list()
            
    def clear_files(self):
        """Clear all selected files."""
        self.selected_files.clear()
        self.update_files_list()
        
    def update_files_list(self):
        """Update the files list widget."""
        self.files_list.clear()
        
        for file_path in self.selected_files:
            item = QListWidgetItem(file_path.name)
            item.setToolTip(str(file_path))
            self.files_list.addItem(item)
            
        self.add_job_btn.setEnabled(len(self.selected_files) > 0)
        
    def browse_output_dir(self):
        """Browse for output directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.output_dir_edit.text()
        )
        
        if directory:
            self.output_dir_edit.setText(directory)
            
    def update_parameters(self):
        """Update parameter widgets based on selected operation."""
        # Clear existing parameters
        for i in reversed(range(self.params_layout.count())):
            child = self.params_layout.takeAt(i).widget()
            if child:
                child.deleteLater()
                
        operation = self.operation_combo.currentText()
        
        # Add operation-specific parameters
        if operation == "Extract Text":
            self.preserve_layout_cb = QCheckBox("Preserve layout")
            self.params_layout.addRow(self.preserve_layout_cb)
            
        elif operation == "Extract Images":
            self.image_format_combo = QComboBox()
            self.image_format_combo.addItems(["PNG", "JPEG", "TIFF"])
            self.params_layout.addRow("Format:", self.image_format_combo)
            
        elif operation == "Split PDFs":
            self.split_pages_edit = QLineEdit()
            self.split_pages_edit.setPlaceholderText("1-3,5,7-9 or leave empty")
            self.params_layout.addRow("Page ranges:", self.split_pages_edit)
            
        elif operation == "Rotate Pages":
            self.rotation_edit = QLineEdit()
            self.rotation_edit.setPlaceholderText("1:90,3:180,5-7:270")
            self.params_layout.addRow("Rotations:", self.rotation_edit)
            
        elif operation == "Add Password":
            self.password_edit = QLineEdit()
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.params_layout.addRow("Password:", self.password_edit)
            
        elif operation == "Convert to Images":
            self.image_dpi_spinbox = QSpinBox()
            self.image_dpi_spinbox.setRange(72, 600)
            self.image_dpi_spinbox.setValue(300)
            self.params_layout.addRow("DPI:", self.image_dpi_spinbox)
            
        elif operation == "AI Summarization":
            self.summary_length_combo = QComboBox()
            self.summary_length_combo.addItems(["Short", "Medium", "Long"])
            self.params_layout.addRow("Length:", self.summary_length_combo)
            
    def get_operation_params(self) -> Dict[str, Any]:
        """Get parameters for the selected operation."""
        operation = self.operation_combo.currentText()
        params = {
            'output_dir': self.output_dir_edit.text(),
            'preserve_structure': self.preserve_structure_cb.isChecked()
        }
        
        # Add operation-specific parameters
        if operation == "Extract Text" and hasattr(self, 'preserve_layout_cb'):
            params['preserve_layout'] = self.preserve_layout_cb.isChecked()
            
        elif operation == "Extract Images" and hasattr(self, 'image_format_combo'):
            params['format'] = self.image_format_combo.currentText()
            
        elif operation == "Split PDFs" and hasattr(self, 'split_pages_edit'):
            params['pages'] = self.split_pages_edit.text().strip()
            
        elif operation == "Rotate Pages" and hasattr(self, 'rotation_edit'):
            params['rotations'] = self.rotation_edit.text().strip()
            
        elif operation == "Add Password" and hasattr(self, 'password_edit'):
            params['password'] = self.password_edit.text().strip()
            
        elif operation == "Convert to Images" and hasattr(self, 'image_dpi_spinbox'):
            params['dpi'] = self.image_dpi_spinbox.value()
            
        elif operation == "AI Summarization" and hasattr(self, 'summary_length_combo'):
            params['length'] = self.summary_length_combo.currentText().lower()
            
        return params
        
    def add_job(self):
        """Add a job to the queue."""
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select files for processing.")
            return
            
        operation = self.operation_combo.currentText()
        params = self.get_operation_params()
        
        # Validate operation-specific requirements
        if operation == "Add Password" and not params.get('password'):
            QMessageBox.warning(self, "Warning", "Please enter a password.")
            return
            
        job = BatchJobItem(self.selected_files.copy(), operation, params)
        self.job_added.emit(job)
        
        # Clear files after adding job
        self.clear_files()


class BatchQueueWidget(QWidget):
    """Widget for managing the batch processing queue."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.jobs: List[BatchJobItem] = []
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Queue controls
        controls_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Processing")
        self.start_btn.setEnabled(False)
        
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setEnabled(False)
        
        self.clear_btn = QPushButton("Clear Queue")
        
        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.pause_btn)
        controls_layout.addWidget(self.clear_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Jobs table
        self.jobs_table = QTableWidget()
        self.jobs_table.setColumnCount(5)
        self.jobs_table.setHorizontalHeaderLabels([
            "Operation", "Files", "Status", "Progress", "Error"
        ])
        
        header = self.jobs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.jobs_table)
        
        # Overall progress
        self.overall_progress = QProgressBar()
        layout.addWidget(self.overall_progress)
        
    def setup_connections(self):
        """Set up signal connections."""
        self.start_btn.clicked.connect(self.start_processing)
        self.pause_btn.clicked.connect(self.pause_processing)
        self.clear_btn.clicked.connect(self.clear_queue)
        
    def add_job(self, job: BatchJobItem):
        """Add a job to the queue."""
        self.jobs.append(job)
        self.update_jobs_table()
        self.start_btn.setEnabled(True)
        
    def update_jobs_table(self):
        """Update the jobs table."""
        self.jobs_table.setRowCount(len(self.jobs))
        
        for i, job in enumerate(self.jobs):
            self.jobs_table.setItem(i, 0, QTableWidgetItem(job.operation))
            self.jobs_table.setItem(i, 1, QTableWidgetItem(str(len(job.files))))
            self.jobs_table.setItem(i, 2, QTableWidgetItem(job.status))
            
            # Progress bar
            progress_bar = QProgressBar()
            progress_bar.setValue(job.progress)
            self.jobs_table.setCellWidget(i, 3, progress_bar)
            
            self.jobs_table.setItem(i, 4, QTableWidgetItem(job.error_message))
            
    def start_processing(self):
        """Start batch processing."""
        # TODO: Implement actual batch processing
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        
        # Simulate processing
        QMessageBox.information(self, "Processing", "Batch processing started!")
        
    def pause_processing(self):
        """Pause batch processing."""
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        
    def clear_queue(self):
        """Clear the processing queue."""
        if self.jobs:
            reply = QMessageBox.question(
                self, "Clear Queue",
                "Are you sure you want to clear all jobs from the queue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.jobs.clear()
                self.update_jobs_table()
                self.start_btn.setEnabled(False)


class BatchProcessingDialog(QDialog):
    """Main batch processing dialog."""
    
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Batch Processing")
        self.setModal(False)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Job configuration tab
        self.job_widget = BatchJobWidget(self.config)
        self.tab_widget.addTab(self.job_widget, "Configure Jobs")
        
        # Queue management tab
        self.queue_widget = BatchQueueWidget()
        self.tab_widget.addTab(self.queue_widget, "Processing Queue")
        
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
        self.job_widget.job_added.connect(self.queue_widget.add_job)
        self.job_widget.job_added.connect(lambda: self.tab_widget.setCurrentIndex(1))