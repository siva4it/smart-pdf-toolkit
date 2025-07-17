# Smart PDF Toolkit - User Guide

Welcome to the Smart PDF Toolkit user guide! This comprehensive guide will help you get the most out of the toolkit's powerful PDF processing capabilities.

## 📚 Table of Contents

1. [Getting Started](getting-started.md)
2. [Installation Guide](installation.md)
3. [Quick Start Tutorial](../QUICKSTART.md)
4. [CLI Reference](cli-reference.md)
5. [API Usage](api-usage.md)
6. [GUI Application](gui-guide.md)
7. [Configuration](configuration.md)
8. [Troubleshooting](troubleshooting.md)

## 🎯 What You Can Do

### Core PDF Operations
- **Merge PDFs**: Combine multiple PDF files into one
- **Split PDFs**: Extract specific pages or ranges
- **Extract Text**: Get text content with OCR support
- **Convert Formats**: PDF ↔ DOCX, HTML, Images
- **Optimize Files**: Reduce file size and improve performance
- **Add Security**: Password protection and encryption

### AI-Powered Features
- **Document Summarization**: Generate concise summaries
- **Content Analysis**: Extract key topics and insights
- **Document Classification**: Automatically categorize documents
- **Question Answering**: Query documents with natural language
- **Translation**: Translate document content

### Batch Processing
- **Multiple Files**: Process hundreds of documents at once
- **Automated Workflows**: Set up recurring processing tasks
- **Progress Tracking**: Monitor processing status in real-time
- **Error Handling**: Robust error recovery and reporting

## 🚀 Quick Examples

### Command Line
```bash
# Extract text from a PDF
smart-pdf extract-text document.pdf -o output.txt

# Merge multiple PDFs
smart-pdf merge file1.pdf file2.pdf file3.pdf -o merged.pdf

# Convert PDF to images
smart-pdf to-images document.pdf -o images/

# AI-powered summarization
smart-pdf summarize document.pdf -o summary.txt
```

### Python API
```python
from smart_pdf_toolkit import PDFProcessor

processor = PDFProcessor()

# Extract text
result = processor.extract_text("document.pdf")
print(result.text)

# Merge PDFs
processor.merge_pdfs(["file1.pdf", "file2.pdf"], "merged.pdf")

# AI analysis
summary = processor.ai_summarize("document.pdf")
print(summary)
```

### REST API
```bash
# Upload and process a PDF
curl -X POST "http://localhost:8000/api/v1/process" \
  -F "file=@document.pdf" \
  -F "operation=extract_text"

# Get processing status
curl "http://localhost:8000/api/v1/status/{task_id}"
```

## 🎨 User Interfaces

### 1. Command Line Interface (CLI)
Perfect for automation, scripting, and power users.
- Cross-platform compatibility
- Scriptable and automatable
- Rich progress indicators
- Comprehensive help system

### 2. REST API
Ideal for web applications and service integration.
- RESTful design
- OpenAPI/Swagger documentation
- Asynchronous processing
- Authentication and rate limiting

### 3. Desktop GUI
User-friendly graphical interface for everyday use.
- Drag-and-drop file handling
- Visual progress tracking
- Batch processing interface
- Settings and preferences

## 🔧 Configuration Options

### Environment Variables
```bash
# API Configuration
SMART_PDF_HOST=0.0.0.0
SMART_PDF_PORT=8000
SMART_PDF_DEBUG=false

# File Processing
SMART_PDF_MAX_FILE_SIZE=104857600  # 100MB
SMART_PDF_OUTPUT_DIR=./output

# AI Services
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
```

### Configuration Files
- `config/development/.env.development` - Development settings
- `config/production/.env.production` - Production settings
- `config/testing/.env.testing` - Testing settings

## 📖 Detailed Guides

### For End Users
- [Installation Guide](installation.md) - Step-by-step installation
- [Quick Start](../QUICKSTART.md) - Get running in 5 minutes
- [GUI Guide](gui-guide.md) - Using the desktop application
- [Common Tasks](common-tasks.md) - Frequently used operations

### For Developers
- [API Reference](../api/) - Complete API documentation
- [Python SDK](python-sdk.md) - Using the Python library
- [Integration Examples](../../examples/) - Real-world examples
- [Plugin Development](plugin-development.md) - Extending functionality

### For System Administrators
- [Deployment Guide](../deployment/) - Production deployment
- [Configuration Management](configuration.md) - System configuration
- [Monitoring and Logging](monitoring.md) - Operational monitoring
- [Security Considerations](security.md) - Security best practices

## 🆘 Getting Help

### Documentation
- Browse the complete documentation in the `docs/` directory
- Check the [FAQ](faq.md) for common questions
- Review [troubleshooting guide](troubleshooting.md) for issues

### Community Support
- GitHub Issues for bug reports and feature requests
- GitHub Discussions for questions and community help
- Example code in the `examples/` directory

### Professional Support
- Email: support@smart-pdf-toolkit.com
- Documentation: https://smart-pdf-toolkit.readthedocs.io
- Commercial support and consulting available

## 🎉 What's Next?

1. **Start with the [Quick Start Guide](../QUICKSTART.md)**
2. **Try the [CLI Examples](../../examples/cli/)**
3. **Explore the [API Documentation](../api/)**
4. **Join our community on GitHub**

Happy PDF processing! 📄✨