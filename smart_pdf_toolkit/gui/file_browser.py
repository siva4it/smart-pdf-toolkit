"""
File browser widget for Smart PDF Toolkit GUI.
"""

from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QCheckBox, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QContextMenuEvent

from ..core.config import Config


class FileListWidget(QListWidget):
    """Custom list widget with drag and drop support."""
    
    files_dropped = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.DropOnly)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
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
                self.files_dropped.emit(pdf_files)
                event.acceptProposedAction()


class FileBrowser(QWidget):
    """File browser widget with file list and controls."""
    
    files_selected = pyqtSignal(list)
    
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.files: List[Path] = []
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Files")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Select all checkbox
        self.select_all_cb = QCheckBox("Select All")
        header_layout.addWidget(self.select_all_cb)
        
        layout.addLayout(header_layout)
        
        # File list
        self.file_list = FileListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.file_list)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.setEnabled(False)
        controls_layout.addWidget(self.remove_btn)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setEnabled(False)
        controls_layout.addWidget(self.clear_btn)
        
        layout.addLayout(controls_layout)
        
        # File info
        self.info_label = QLabel("Drop PDF files here or use File menu")
        self.info_label.setStyleSheet("color: gray; font-style: italic;")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)
        
    def setup_connections(self):
        """Set up signal connections."""
        self.file_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.file_list.files_dropped.connect(self.on_files_dropped)
        self.select_all_cb.toggled.connect(self.on_select_all_toggled)
        self.remove_btn.clicked.connect(self.remove_selected_files)
        self.clear_btn.clicked.connect(self.clear_files)
        
    def contextMenuEvent(self, event: QContextMenuEvent):
        """Handle context menu events."""
        if self.file_list.itemAt(self.file_list.mapFromGlobal(event.globalPos())):
            menu = QMenu(self)
            
            remove_action = menu.addAction("Remove Selected")
            remove_action.triggered.connect(self.remove_selected_files)
            
            menu.addSeparator()
            
            clear_action = menu.addAction("Clear All")
            clear_action.triggered.connect(self.clear_files)
            
            menu.exec(event.globalPos())
            
    def set_files(self, files: List[Path]):
        """Set the list of files."""
        self.files = files.copy()
        self.update_file_list()
        
    def add_files(self, files: List[Path]):
        """Add files to the current list."""
        # Filter out duplicates
        new_files = [f for f in files if f not in self.files]
        self.files.extend(new_files)
        self.update_file_list()
        
    def update_file_list(self):
        """Update the file list widget."""
        self.file_list.clear()
        
        for file_path in self.files:
            item = QListWidgetItem(file_path.name)
            item.setData(Qt.ItemDataRole.UserRole, str(file_path))
            item.setToolTip(str(file_path))
            self.file_list.addItem(item)
            
        # Update controls
        has_files = len(self.files) > 0
        self.clear_btn.setEnabled(has_files)
        
        # Update info label
        if has_files:
            count = len(self.files)
            self.info_label.setText(f"{count} file{'s' if count != 1 else ''} loaded")
        else:
            self.info_label.setText("Drop PDF files here or use File menu")
            
        # Update select all checkbox
        self.select_all_cb.setEnabled(has_files)
        
    def get_selected_files(self) -> List[Path]:
        """Get the currently selected files."""
        selected_files = []
        for item in self.file_list.selectedItems():
            file_path = Path(item.data(Qt.ItemDataRole.UserRole))
            selected_files.append(file_path)
        return selected_files
        
    def get_all_files(self) -> List[Path]:
        """Get all files in the list."""
        return self.files.copy()
        
    def clear_files(self):
        """Clear all files from the list."""
        if self.files:
            reply = QMessageBox.question(
                self,
                "Clear Files",
                "Are you sure you want to clear all files?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.files.clear()
                self.update_file_list()
                self.files_selected.emit([])
                
    def remove_selected_files(self):
        """Remove selected files from the list."""
        selected_files = self.get_selected_files()
        if selected_files:
            # Remove from files list
            for file_path in selected_files:
                if file_path in self.files:
                    self.files.remove(file_path)
                    
            self.update_file_list()
            self.on_selection_changed()
            
    def on_files_dropped(self, files: List[Path]):
        """Handle files dropped on the list."""
        self.add_files(files)
        
    def on_selection_changed(self):
        """Handle selection change in file list."""
        selected_files = self.get_selected_files()
        has_selection = len(selected_files) > 0
        
        # Update remove button
        self.remove_btn.setEnabled(has_selection)
        
        # Update select all checkbox
        if len(selected_files) == len(self.files) and len(self.files) > 0:
            self.select_all_cb.setChecked(True)
        else:
            self.select_all_cb.setChecked(False)
            
        # Emit selection signal
        self.files_selected.emit(selected_files)
        
    def on_select_all_toggled(self, checked: bool):
        """Handle select all checkbox toggle."""
        if checked:
            self.file_list.selectAll()
        else:
            self.file_list.clearSelection()