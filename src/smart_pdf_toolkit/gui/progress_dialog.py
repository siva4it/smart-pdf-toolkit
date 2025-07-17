"""
Progress dialog for Smart PDF Toolkit GUI operations.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QMovie


class ProgressDialog(QDialog):
    """Progress dialog with cancellation support."""
    
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_cancellable = True
        self.is_cancelled = False
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Processing...")
        self.setModal(True)
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout(self)
        
        # Message label
        self.message_label = QLabel("Processing files...")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Details text (initially hidden)
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(80)
        self.details_text.setVisible(False)
        layout.addWidget(self.details_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.details_btn = QPushButton("Show Details")
        self.details_btn.clicked.connect(self.toggle_details)
        button_layout.addWidget(self.details_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
    def setup_connections(self):
        """Set up signal connections."""
        pass
        
    def set_message(self, message: str):
        """Set the progress message."""
        self.message_label.setText(message)
        
    def set_progress(self, value: int):
        """Set the progress value (0-100)."""
        self.progress_bar.setValue(value)
        
    def set_indeterminate(self, indeterminate: bool = True):
        """Set indeterminate progress mode."""
        if indeterminate:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
            
    def set_cancellable(self, cancellable: bool):
        """Set whether the operation can be cancelled."""
        self.is_cancellable = cancellable
        self.cancel_btn.setEnabled(cancellable)
        
    def add_detail(self, detail: str):
        """Add a detail message to the details text."""
        self.details_text.append(detail)
        
    def clear_details(self):
        """Clear the details text."""
        self.details_text.clear()
        
    def toggle_details(self):
        """Toggle the visibility of the details text."""
        if self.details_text.isVisible():
            self.details_text.setVisible(False)
            self.details_btn.setText("Show Details")
            self.setFixedSize(400, 200)
        else:
            self.details_text.setVisible(True)
            self.details_btn.setText("Hide Details")
            self.setFixedSize(400, 300)
            
    def on_cancel_clicked(self):
        """Handle cancel button click."""
        if self.is_cancellable:
            self.is_cancelled = True
            self.cancelled.emit()
            self.close()
            
    def reset(self):
        """Reset the dialog to initial state."""
        self.is_cancelled = False
        self.set_progress(0)
        self.set_indeterminate(False)
        self.set_message("Processing files...")
        self.clear_details()
        self.set_cancellable(True)
        
        # Hide details if shown
        if self.details_text.isVisible():
            self.toggle_details()
            
    def closeEvent(self, event):
        """Handle close event."""
        if self.is_cancellable and not self.is_cancelled:
            self.on_cancel_clicked()
        event.accept()


class SimpleProgressDialog(QDialog):
    """Simple progress dialog without cancellation."""
    
    def __init__(self, message: str = "Processing...", parent=None):
        super().__init__(parent)
        self.init_ui(message)
        
    def init_ui(self, message: str):
        """Initialize the user interface."""
        self.setWindowTitle("Please Wait")
        self.setModal(True)
        self.setFixedSize(300, 100)
        
        # Remove window controls
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.CustomizeWindowHint
        )
        
        layout = QVBoxLayout(self)
        
        # Message label
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message_label)
        
        # Progress bar (indeterminate)
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(progress_bar)