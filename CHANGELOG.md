# Changelog

All notable changes to the Smart PDF Toolkit project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive project restructuring following industry standards
- Organized source code into `src/` directory structure
- Categorized tests into unit, integration, e2e, performance, and security
- Environment-specific configuration files
- Enhanced deployment infrastructure with AWS CloudFormation
- Comprehensive documentation structure
- Development tools and CI/CD improvements

### Changed
- Moved source code from root to `src/smart_pdf_toolkit/`
- Reorganized deployment files into `deployment/` directory
- Split requirements into production and development dependencies
- Updated project structure to follow Python packaging best practices

### Fixed
- Fixed pytest.ini configuration syntax errors
- Resolved import path issues after restructuring

## [1.0.0] - 2024-01-15

### Added
- Initial release of Smart PDF Toolkit
- Core PDF processing functionality
- CLI interface for PDF operations
- REST API with FastAPI
- Desktop GUI application with PyQt6
- Plugin system for extensibility
- AI-powered document analysis
- Batch processing capabilities
- Security features and input validation
- Docker containerization
- Comprehensive test suite

### Features
- **PDF Operations**: Merge, split, extract text, convert formats
- **OCR Support**: Text extraction from scanned documents
- **AI Integration**: Document summarization and analysis
- **Format Conversion**: PDF to/from DOCX, HTML, images
- **Security**: Password protection, encryption, malware scanning
- **Batch Processing**: Handle multiple files simultaneously
- **Plugin System**: Extensible architecture for custom functionality
- **Multi-Interface**: CLI, API, and GUI access methods

### Supported Formats
- Input: PDF, DOCX, XLSX, PPTX, TXT, MD, images
- Output: PDF, DOCX, HTML, TXT, images

### Deployment Options
- Local installation
- Docker containers
- AWS ECS with Fargate
- Kubernetes (experimental)

### Dependencies
- Python 3.8+
- PyMuPDF for PDF processing
- FastAPI for REST API
- PyQt6 for GUI
- OpenAI for AI features
- Tesseract for OCR