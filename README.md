# Smart PDF Toolkit

A comprehensive Python application that provides users with a complete suite of tools for PDF manipulation, analysis, and processing.

## Features

- **PDF Operations**: Merge, split, rotate, extract, and reorder PDF pages
- **Content Extraction**: Extract text, images, tables, metadata, and links from PDFs
- **OCR Processing**: Convert scanned PDFs to searchable text with language detection
- **Format Conversion**: Convert between PDF and various formats (images, Office documents, HTML)
- **Security Features**: Password protection, permissions, watermarks, digital signatures
- **Batch Processing**: Process multiple files efficiently
- **AI-Powered Features**: Document summarization, content analysis, Q&A
- **Multiple Interfaces**: GUI, CLI, and REST API access

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from smart_pdf_toolkit.core.pdf_operations import PDFOperationsManager
from smart_pdf_toolkit.core.content_extractor import ContentExtractor

# Basic PDF operations
pdf_ops = PDFOperationsManager()
result = pdf_ops.merge_pdfs(['file1.pdf', 'file2.pdf'], 'merged.pdf')

# Content extraction
extractor = ContentExtractor()
text_result = extractor.extract_text('document.pdf')
```

## Project Structure

```
smart-pdf-toolkit/
├── smart_pdf_toolkit/          # Main package
│   ├── core/                   # Core PDF processing engine
│   ├── api/                    # REST API implementation
│   ├── cli/                    # Command-line interface
│   ├── gui/                    # Desktop GUI application
│   ├── web/                    # Web interface
│   ├── plugins/                # Plugin system
│   └── utils/                  # Shared utilities
├── tests/                      # Test suites
├── docs/                       # Documentation
├── .kiro/                      # Kiro IDE specifications
└── requirements.txt            # Dependencies
```

## Development Status

- ✅ Core PDF Operations (merge, split, rotate, extract, reorder)
- ✅ Content Extraction (text, images, tables, metadata, links)
- ✅ OCR Processing with tesseract integration
- ✅ Format Conversion (images, Office documents, HTML)
- ✅ Plugin System Foundation
- 🔄 Security Features (in progress)
- 🔄 Optimization Engine (in progress)
- 🔄 Batch Processing (in progress)
- 🔄 AI Services (in progress)
- 🔄 User Interfaces (in progress)

## License

MIT License