"""
AI Services tab for Smart PDF Toolkit GUI.
"""

from pathlib import Path
from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTextEdit, QLineEdit, QCheckBox, QGroupBox, QFormLayout, QSpinBox,
    QSlider, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..core.config import Config


class AIServicesTab(QWidget):
    """Tab for AI-powered document analysis and processing."""
    
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
        
        # Document Summarization section
        summary_group = QGroupBox("Document Summarization")
        summary_layout = QFormLayout(summary_group)
        
        self.summary_length_combo = QComboBox()
        self.summary_length_combo.addItems(["Short", "Medium", "Long", "Custom"])
        summary_layout.addRow("Summary length:", self.summary_length_combo)
        
        self.summary_custom_words = QSpinBox()
        self.summary_custom_words.setRange(50, 1000)
        self.summary_custom_words.setValue(200)
        self.summary_custom_words.setEnabled(False)
        summary_layout.addRow("Custom word count:", self.summary_custom_words)
        
        self.summary_output_edit = QLineEdit()
        self.summary_output_edit.setPlaceholderText("summary.txt")
        summary_layout.addRow("Output file:", self.summary_output_edit)
        
        self.summarize_btn = QPushButton("Generate Summary")
        self.summarize_btn.setEnabled(False)
        summary_layout.addRow(self.summarize_btn)
        
        layout.addWidget(summary_group)
        
        # Content Analysis section
        analysis_group = QGroupBox("Content Analysis")
        analysis_layout = QFormLayout(analysis_group)
        
        # Analysis types
        analysis_types_layout = QVBoxLayout()
        self.extract_topics_cb = QCheckBox("Extract topics")
        self.extract_keywords_cb = QCheckBox("Extract keywords")
        self.classify_document_cb = QCheckBox("Classify document")
        self.sentiment_analysis_cb = QCheckBox("Sentiment analysis")
        
        analysis_types_layout.addWidget(self.extract_topics_cb)
        analysis_types_layout.addWidget(self.extract_keywords_cb)
        analysis_types_layout.addWidget(self.classify_document_cb)
        analysis_types_layout.addWidget(self.sentiment_analysis_cb)
        
        analysis_layout.addRow("Analysis types:", analysis_types_layout)
        
        self.analysis_output_edit = QLineEdit()
        self.analysis_output_edit.setPlaceholderText("analysis.json")
        analysis_layout.addRow("Output file:", self.analysis_output_edit)
        
        self.analyze_btn = QPushButton("Analyze Content")
        self.analyze_btn.setEnabled(False)
        analysis_layout.addRow(self.analyze_btn)
        
        layout.addWidget(analysis_group)
        
        # Question Answering section
        qa_group = QGroupBox("Question Answering")
        qa_layout = QFormLayout(qa_group)
        
        self.question_edit = QTextEdit()
        self.question_edit.setMaximumHeight(80)
        self.question_edit.setPlaceholderText("Enter your question about the document...")
        qa_layout.addRow("Question:", self.question_edit)
        
        self.qa_output_edit = QLineEdit()
        self.qa_output_edit.setPlaceholderText("answer.txt")
        qa_layout.addRow("Output file:", self.qa_output_edit)
        
        self.answer_btn = QPushButton("Get Answer")
        self.answer_btn.setEnabled(False)
        qa_layout.addRow(self.answer_btn)
        
        layout.addWidget(qa_group)
        
        # Translation section
        translation_group = QGroupBox("Document Translation")
        translation_layout = QFormLayout(translation_group)
        
        self.target_language_combo = QComboBox()
        self.target_language_combo.addItems([
            "Spanish", "French", "German", "Italian", "Portuguese",
            "Chinese", "Japanese", "Korean", "Russian", "Arabic"
        ])
        translation_layout.addRow("Target language:", self.target_language_combo)
        
        self.preserve_formatting_cb = QCheckBox("Preserve formatting")
        self.preserve_formatting_cb.setChecked(True)
        translation_layout.addRow(self.preserve_formatting_cb)
        
        self.translation_output_edit = QLineEdit()
        self.translation_output_edit.setPlaceholderText("translated.txt")
        translation_layout.addRow("Output file:", self.translation_output_edit)
        
        self.translate_btn = QPushButton("Translate Document")
        self.translate_btn.setEnabled(False)
        translation_layout.addRow(self.translate_btn)
        
        layout.addWidget(translation_group)
        
        layout.addStretch()
        
    def setup_connections(self):
        """Set up signal connections."""
        self.summary_length_combo.currentTextChanged.connect(self.on_summary_length_changed)
        self.summarize_btn.clicked.connect(self.on_summarize_clicked)
        self.analyze_btn.clicked.connect(self.on_analyze_clicked)
        self.answer_btn.clicked.connect(self.on_answer_clicked)
        self.translate_btn.clicked.connect(self.on_translate_clicked)
        
    def set_selected_files(self, files: List[Path]):
        """Set the selected files."""
        self.selected_files = files
        self.update_button_states()
        
    def update_button_states(self):
        """Update button enabled states based on selection."""
        has_files = len(self.selected_files) > 0
        
        self.summarize_btn.setEnabled(has_files)
        self.analyze_btn.setEnabled(has_files)
        self.answer_btn.setEnabled(has_files)
        self.translate_btn.setEnabled(has_files)
        
    def on_summary_length_changed(self, text: str):
        """Handle summary length combo change."""
        self.summary_custom_words.setEnabled(text == "Custom")
        
    def on_summarize_clicked(self):
        """Handle summarize button click."""
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select files to summarize.")
            return
            
        length = self.summary_length_combo.currentText()
        word_count = None
        if length == "Custom":
            word_count = self.summary_custom_words.value()
            
        output_file = self.summary_output_edit.text().strip()
        if not output_file:
            output_file = "summary.txt"
            
        params = {
            'files': self.selected_files,
            'length': length.lower(),
            'word_count': word_count,
            'output_file': output_file
        }
        
        self.operation_requested.emit('summarize', params)
        
    def on_analyze_clicked(self):
        """Handle analyze button click."""
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select files to analyze.")
            return
            
        analysis_types = []
        if self.extract_topics_cb.isChecked():
            analysis_types.append('topics')
        if self.extract_keywords_cb.isChecked():
            analysis_types.append('keywords')
        if self.classify_document_cb.isChecked():
            analysis_types.append('classification')
        if self.sentiment_analysis_cb.isChecked():
            analysis_types.append('sentiment')
            
        if not analysis_types:
            QMessageBox.warning(self, "Warning", "Please select at least one analysis type.")
            return
            
        output_file = self.analysis_output_edit.text().strip()
        if not output_file:
            output_file = "analysis.json"
            
        params = {
            'files': self.selected_files,
            'analysis_types': analysis_types,
            'output_file': output_file
        }
        
        self.operation_requested.emit('analyze', params)
        
    def on_answer_clicked(self):
        """Handle answer button click."""
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select files to query.")
            return
            
        question = self.question_edit.toPlainText().strip()
        if not question:
            QMessageBox.warning(self, "Warning", "Please enter a question.")
            return
            
        output_file = self.qa_output_edit.text().strip()
        if not output_file:
            output_file = "answer.txt"
            
        params = {
            'files': self.selected_files,
            'question': question,
            'output_file': output_file
        }
        
        self.operation_requested.emit('question', params)
        
    def on_translate_clicked(self):
        """Handle translate button click."""
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select files to translate.")
            return
            
        target_language = self.target_language_combo.currentText().lower()
        output_file = self.translation_output_edit.text().strip()
        if not output_file:
            output_file = "translated.txt"
            
        params = {
            'files': self.selected_files,
            'target_language': target_language,
            'preserve_formatting': self.preserve_formatting_cb.isChecked(),
            'output_file': output_file
        }
        
        self.operation_requested.emit('translate', params)