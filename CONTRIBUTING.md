# Contributing to Smart PDF Toolkit

Thank you for your interest in contributing to Smart PDF Toolkit! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues
1. Check existing issues to avoid duplicates
2. Use the issue templates when available
3. Provide clear, detailed descriptions
4. Include steps to reproduce bugs
5. Add relevant labels and assignees

### Submitting Pull Requests
1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes following our coding standards
4. Add tests for new functionality
5. Update documentation as needed
6. Submit a pull request with a clear description

## 🏗️ Development Setup

### Prerequisites
- Python 3.8 or higher
- Git
- Docker (optional but recommended)

### Local Development
```bash
# Clone the repository
git clone https://github.com/siva4it/smart-pdf-toolkit.git
cd smart-pdf-toolkit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt
pip install -e .

# Set up pre-commit hooks
pre-commit install

# Run tests to verify setup
python -m pytest tests/unit/ -v
```

### Project Structure
```
smart-pdf-toolkit/
├── src/smart_pdf_toolkit/    # Main source code
├── tests/                    # Test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   ├── e2e/                 # End-to-end tests
│   ├── performance/         # Performance tests
│   └── security/            # Security tests
├── docs/                    # Documentation
├── deployment/              # Deployment configurations
├── tools/                   # Development tools
├── examples/                # Usage examples
└── config/                  # Environment configurations
```

## 📝 Coding Standards

### Python Code Style
- Follow PEP 8 guidelines
- Use Black for code formatting
- Use isort for import sorting
- Maximum line length: 88 characters
- Use type hints where appropriate

### Code Quality Tools
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Security scanning
bandit -r src/
```

### Testing Requirements
- Write tests for all new functionality
- Maintain test coverage above 80%
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Mock external dependencies

### Documentation
- Update docstrings for new functions/classes
- Follow Google docstring format
- Update relevant documentation files
- Add examples for new features

## 🧪 Testing Guidelines

### Running Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/ -v           # Unit tests
pytest tests/integration/ -v    # Integration tests
pytest tests/security/ -v       # Security tests

# Run with coverage
pytest --cov=smart_pdf_toolkit --cov-report=html

# Run performance tests
pytest tests/performance/ -v --benchmark-only
```

### Test Categories
- **Unit Tests**: Test individual functions/classes in isolation
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete user workflows
- **Performance Tests**: Test performance and benchmarks
- **Security Tests**: Test security vulnerabilities

### Writing Tests
```python
# Example unit test
def test_pdf_merger_combines_files():
    """Test that PDF merger correctly combines multiple files."""
    # Arrange
    merger = PDFMerger()
    files = ["file1.pdf", "file2.pdf"]
    
    # Act
    result = merger.merge(files, output="merged.pdf")
    
    # Assert
    assert result.success
    assert result.output_file.exists()
    assert result.page_count == expected_pages
```

## 🔧 Development Workflow

### Branch Naming
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Critical fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages
Follow conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(api): add PDF password protection endpoint
fix(cli): resolve file path handling on Windows
docs(readme): update installation instructions
test(core): add unit tests for PDF merger
```

### Pull Request Process
1. Ensure all tests pass
2. Update documentation
3. Add changelog entry
4. Request review from maintainers
5. Address review feedback
6. Squash commits if requested

## 🏷️ Release Process

### Version Numbering
We follow Semantic Versioning (SemVer):
- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes (backward compatible)

### Release Checklist
- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md`
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Create release tag
- [ ] Deploy to staging
- [ ] Deploy to production

## 🎯 Areas for Contribution

### High Priority
- Performance optimizations
- Additional file format support
- Enhanced security features
- Mobile/web interface
- Plugin development

### Good First Issues
- Documentation improvements
- Unit test additions
- Bug fixes
- Code cleanup
- Example applications

### Advanced Contributions
- AI/ML model improvements
- Cloud deployment enhancements
- Performance profiling
- Security auditing
- Architecture improvements

## 📚 Resources

### Documentation
- [API Documentation](docs/api/)
- [User Guide](docs/user-guide/)
- [Developer Guide](docs/developer-guide/)
- [Deployment Guide](docs/deployment/)

### External Resources
- [Python Style Guide](https://pep8.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PyQt6 Documentation](https://doc.qt.io/qtforpython/)
- [pytest Documentation](https://docs.pytest.org/)

## 💬 Communication

### Getting Help
- GitHub Issues for bug reports and feature requests
- GitHub Discussions for questions and ideas
- Email maintainers for security issues

### Code of Conduct
Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing to Smart PDF Toolkit! 🎉