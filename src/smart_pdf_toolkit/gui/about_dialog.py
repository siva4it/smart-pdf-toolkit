"""
About dialog for Smart PDF Toolkit GUI.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap

from ..core.config import Config


class AboutDialog(QDialog):
    """About dialog showing application information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("About Smart PDF Toolkit")
        self.setModal(True)
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Header with logo and title
        header_layout = QHBoxLayout()
        
        # Logo placeholder (you can add an actual logo later)
        logo_label = QLabel("📄")
        logo_label.setFont(QFont("", 48))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(logo_label)
        
        # Title and version
        title_layout = QVBoxLayout()
        
        title_label = QLabel("Smart PDF Toolkit")
        title_label.setFont(QFont("", 18, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        
        version_label = QLabel("Version 1.0.0")
        version_label.setFont(QFont("", 12))
        title_layout.addWidget(version_label)
        
        subtitle_label = QLabel("Comprehensive PDF Processing and Analysis Tool")
        subtitle_label.setFont(QFont("", 10))
        subtitle_label.setStyleSheet("color: gray;")
        title_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Tab widget for different information sections
        tab_widget = QTabWidget()
        
        # About tab
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setHtml("""
        <h3>About Smart PDF Toolkit</h3>
        <p>Smart PDF Toolkit is a comprehensive PDF processing and analysis tool that provides:</p>
        <ul>
            <li><b>PDF Operations:</b> Merge, split, rotate, and manipulate PDF documents</li>
            <li><b>Content Extraction:</b> Extract text, images, and tables from PDFs</li>
            <li><b>OCR Processing:</b> Convert scanned documents to searchable text</li>
            <li><b>Format Conversion:</b> Convert between PDF and various formats</li>
            <li><b>AI-Powered Analysis:</b> Document summarization and content analysis</li>
            <li><b>Security Features:</b> Password protection and digital signatures</li>
            <li><b>Batch Processing:</b> Process multiple files efficiently</li>
            <li><b>Plugin System:</b> Extend functionality with custom plugins</li>
        </ul>
        <p>The toolkit is designed for both individual users and enterprise environments, 
        providing both GUI and command-line interfaces for maximum flexibility.</p>
        """)
        about_layout.addWidget(about_text)
        
        tab_widget.addTab(about_tab, "About")
        
        # Credits tab
        credits_tab = QWidget()
        credits_layout = QVBoxLayout(credits_tab)
        
        credits_text = QTextEdit()
        credits_text.setReadOnly(True)
        credits_text.setHtml("""
        <h3>Credits and Acknowledgments</h3>
        <p><b>Development Team:</b></p>
        <ul>
            <li>Smart PDF Toolkit Development Team</li>
        </ul>
        
        <p><b>Third-Party Libraries:</b></p>
        <ul>
            <li><b>PyMuPDF:</b> PDF processing and manipulation</li>
            <li><b>pdfplumber:</b> PDF content extraction</li>
            <li><b>Pillow:</b> Image processing</li>
            <li><b>pytesseract:</b> OCR functionality</li>
            <li><b>PyQt6:</b> GUI framework</li>
            <li><b>FastAPI:</b> REST API framework</li>
            <li><b>python-docx:</b> Word document processing</li>
            <li><b>openpyxl:</b> Excel document processing</li>
            <li><b>cryptography:</b> Security and encryption</li>
        </ul>
        
        <p><b>Special Thanks:</b></p>
        <ul>
            <li>The open-source community for providing excellent libraries</li>
            <li>Contributors and beta testers</li>
        </ul>
        """)
        credits_layout.addWidget(credits_text)
        
        tab_widget.addTab(credits_tab, "Credits")
        
        # License tab
        license_tab = QWidget()
        license_layout = QVBoxLayout(license_tab)
        
        license_text = QTextEdit()
        license_text.setReadOnly(True)
        license_text.setPlainText("""
MIT License

Copyright (c) 2024 Smart PDF Toolkit

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
        """)
        license_layout.addWidget(license_text)
        
        tab_widget.addTab(license_tab, "License")
        
        # System info tab
        system_tab = QWidget()
        system_layout = QVBoxLayout(system_tab)
        
        system_text = QTextEdit()
        system_text.setReadOnly(True)
        
        # Get system information
        import sys
        import platform
        
        system_info = f"""
<h3>System Information</h3>
<p><b>Python Version:</b> {sys.version}</p>
<p><b>Platform:</b> {platform.platform()}</p>
<p><b>Architecture:</b> {platform.architecture()[0]}</p>
<p><b>Processor:</b> {platform.processor()}</p>
<p><b>Machine:</b> {platform.machine()}</p>

<h3>Installed Packages</h3>
<p>Key dependencies and their versions:</p>
<ul>
"""
        
        # Try to get package versions
        try:
            import PyQt6
            system_info += f"<li><b>PyQt6:</b> {PyQt6.QtCore.PYQT_VERSION_STR}</li>"
        except:
            system_info += "<li><b>PyQt6:</b> Not available</li>"
            
        try:
            import fitz
            system_info += f"<li><b>PyMuPDF:</b> {fitz.version[0]}</li>"
        except:
            system_info += "<li><b>PyMuPDF:</b> Not available</li>"
            
        try:
            import pdfplumber
            system_info += f"<li><b>pdfplumber:</b> {pdfplumber.__version__}</li>"
        except:
            system_info += "<li><b>pdfplumber:</b> Not available</li>"
            
        try:
            import PIL
            system_info += f"<li><b>Pillow:</b> {PIL.__version__}</li>"
        except:
            system_info += "<li><b>Pillow:</b> Not available</li>"
            
        try:
            import fastapi
            system_info += f"<li><b>FastAPI:</b> {fastapi.__version__}</li>"
        except:
            system_info += "<li><b>FastAPI:</b> Not available</li>"
            
        system_info += "</ul>"
        
        system_text.setHtml(system_info)
        system_layout.addWidget(system_text)
        
        tab_widget.addTab(system_tab, "System Info")
        
        layout.addWidget(tab_widget)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)