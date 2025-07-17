# Smart PDF Toolkit - Testing Guide

This guide covers comprehensive testing strategies for the Smart PDF Toolkit, including local testing, integration testing, and production validation.

## Table of Contents
- [Quick Start Testing](#quick-start-testing)
- [Local Testing](#local-testing)
- [Integration Testing](#integration-testing)
- [Performance Testing](#performance-testing)
- [Security Testing](#security-testing)
- [AWS Testing](#aws-testing)
- [Continuous Testing](#continuous-testing)

## Quick Start Testing

### 1. Automated Local Testing
Run the comprehensive test suite:

```bash
# Run all local tests
python scripts/local-test.py

# Run specific test categories
pytest tests/unit/ -v                    # Unit tests
pytest tests/integration/ -v             # Integration tests
pytest tests/security/ -v                # Security tests
pytest tests/performance/ -v             # Performance tests
```

### 2. Manual Quick Tests

**CLI Testing:**
```bash
# Install in development mode
pip install -e .

# Test basic commands
smart-pdf --help
smart-pdf info sample.pdf
smart-pdf extract-text sample.pdf -o output.txt
```

**API Testing:**
```bash
# Start API server
python -m smart_pdf_toolkit.api.main

# Test endpoints (in another terminal)
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

**GUI Testing:**
```bash
# Start GUI application
python -m smart_pdf_toolkit.gui.app
```

## Local Testing

### Environment Setup

1. **Create test environment:**
```bash
# Clone repository
git clone https://github.com/siva4it/smart-pdf-toolkit.git
cd smart-pdf-toolkit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"
```

2. **Configure environment:**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# At minimum, set OPENAI_API_KEY if testing AI features
```

### Unit Testing

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=smart_pdf_toolkit --cov-report=html

# Run specific modules
pytest tests/unit/test_core.py -v
pytest tests/unit/test_cli.py -v
pytest tests/unit/test_api.py -v
```

### Integration Testing

```bash
# Test CLI integration
pytest tests/integration/test_cli_integration.py -v

# Test API integration
pytest tests/integration/test_api_integration.py -v

# Test file processing workflows
pytest tests/integration/test_workflows.py -v
```

### Docker Testing

```bash
# Build and test Docker image
docker build -t smart-pdf-toolkit:test .

# Test CLI in container
docker run --rm -v $(pwd)/tests/fixtures:/app/files \
  smart-pdf-toolkit:test info /app/files/sample.pdf

# Test API in container
docker run -d --name smart-pdf-test -p 8000:8000 smart-pdf-toolkit:test
curl http://localhost:8000/health
docker stop smart-pdf-test && docker rm smart-pdf-test

# Test with docker-compose
docker-compose -f docker-compose.yml up -d
curl http://localhost:8000/health
docker-compose down
```

## Integration Testing

### API Integration Tests

Create test files in `tests/integration/`:

```python
# tests/integration/test_api_workflows.py
import pytest
import requests
import tempfile
from pathlib import Path

class TestAPIWorkflows:
    base_url = "http://localhost:8000"
    
    def test_complete_pdf_processing_workflow(self):
        """Test complete PDF processing workflow"""
        # Upload file
        with open("tests/fixtures/sample.pdf", "rb") as f:
            response = requests.post(
                f"{self.base_url}/api/v1/process",
                files={"file": f},
                data={"operation": "extract_text"}
            )
        
        assert response.status_code == 202
        task_id = response.json()["task_id"]
        
        # Check status
        response = requests.get(f"{self.base_url}/api/v1/status/{task_id}")
        assert response.status_code == 200
        
        # Download result (when ready)
        # Implementation depends on your API design
    
    def test_batch_processing(self):
        """Test batch processing functionality"""
        files = [
            ("files", open("tests/fixtures/sample1.pdf", "rb")),
            ("files", open("tests/fixtures/sample2.pdf", "rb"))
        ]
        
        response = requests.post(
            f"{self.base_url}/api/v1/batch-process",
            files=files,
            data={"operation": "merge"}
        )
        
        assert response.status_code == 202
```

### CLI Integration Tests

```python
# tests/integration/test_cli_workflows.py
import subprocess
import tempfile
from pathlib import Path

class TestCLIWorkflows:
    
    def test_pdf_merge_workflow(self):
        """Test PDF merging workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "merged.pdf"
            
            result = subprocess.run([
                "smart-pdf", "merge",
                "tests/fixtures/sample1.pdf",
                "tests/fixtures/sample2.pdf",
                "-o", str(output_file)
            ], capture_output=True, text=True)
            
            assert result.returncode == 0
            assert output_file.exists()
            assert output_file.stat().st_size > 0
    
    def test_text_extraction_workflow(self):
        """Test text extraction workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "extracted.txt"
            
            result = subprocess.run([
                "smart-pdf", "extract-text",
                "tests/fixtures/sample.pdf",
                "-o", str(output_file)
            ], capture_output=True, text=True)
            
            assert result.returncode == 0
            assert output_file.exists()
            assert len(output_file.read_text()) > 0
```

## Performance Testing

### Load Testing with Locust

Create `tests/performance/locustfile.py`:

```python
from locust import HttpUser, task, between
import random

class PDFProcessingUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Setup test data"""
        self.test_files = [
            "tests/fixtures/small.pdf",
            "tests/fixtures/medium.pdf",
            "tests/fixtures/large.pdf"
        ]
    
    @task(3)
    def health_check(self):
        """Test health endpoint"""
        self.client.get("/health")
    
    @task(2)
    def api_docs(self):
        """Test API documentation"""
        self.client.get("/docs")
    
    @task(1)
    def process_pdf(self):
        """Test PDF processing"""
        file_path = random.choice(self.test_files)
        
        with open(file_path, "rb") as f:
            response = self.client.post(
                "/api/v1/process",
                files={"file": f},
                data={"operation": "info"}
            )
        
        if response.status_code == 202:
            task_id = response.json().get("task_id")
            if task_id:
                self.client.get(f"/api/v1/status/{task_id}")
```

Run load tests:
```bash
# Install locust
pip install locust

# Run load test
locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Run headless load test
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
  --users 10 --spawn-rate 2 --run-time 60s --headless
```

### Memory and CPU Testing

```python
# tests/performance/test_resource_usage.py
import psutil
import pytest
import time
from smart_pdf_toolkit.core import PDFProcessor

class TestResourceUsage:
    
    def test_memory_usage_large_file(self):
        """Test memory usage with large files"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Process large file
        processor = PDFProcessor()
        result = processor.process_file("tests/fixtures/large.pdf", "extract_text")
        
        peak_memory = process.memory_info().rss
        memory_increase = peak_memory - initial_memory
        
        # Assert memory increase is reasonable (adjust threshold as needed)
        assert memory_increase < 500 * 1024 * 1024  # 500MB
    
    def test_processing_time_benchmarks(self):
        """Test processing time benchmarks"""
        processor = PDFProcessor()
        
        start_time = time.time()
        result = processor.process_file("tests/fixtures/medium.pdf", "extract_text")
        processing_time = time.time() - start_time
        
        # Assert processing completes within reasonable time
        assert processing_time < 30  # 30 seconds
```

## Security Testing

### Input Validation Tests

```python
# tests/security/test_input_validation.py
import pytest
import requests
from pathlib import Path

class TestInputValidation:
    
    def test_malicious_file_upload(self):
        """Test handling of malicious files"""
        # Create malicious file
        malicious_content = b"<script>alert('xss')</script>" * 1000
        
        response = requests.post(
            "http://localhost:8000/api/v1/process",
            files={"file": ("malicious.pdf", malicious_content, "application/pdf")},
            data={"operation": "extract_text"}
        )
        
        # Should reject malicious content
        assert response.status_code in [400, 422]
    
    def test_oversized_file_rejection(self):
        """Test rejection of oversized files"""
        # Create large dummy file
        large_content = b"A" * (200 * 1024 * 1024)  # 200MB
        
        response = requests.post(
            "http://localhost:8000/api/v1/process",
            files={"file": ("large.pdf", large_content, "application/pdf")},
            data={"operation": "extract_text"}
        )
        
        assert response.status_code == 413  # Payload too large
    
    def test_path_traversal_protection(self):
        """Test protection against path traversal attacks"""
        response = requests.post(
            "http://localhost:8000/api/v1/process",
            files={"file": ("../../../etc/passwd", b"content", "application/pdf")},
            data={"operation": "extract_text"}
        )
        
        assert response.status_code in [400, 422]
```

### Authentication and Authorization Tests

```python
# tests/security/test_auth.py
import pytest
import requests

class TestAuthentication:
    
    def test_protected_endpoints_require_auth(self):
        """Test that protected endpoints require authentication"""
        protected_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/settings",
        ]
        
        for endpoint in protected_endpoints:
            response = requests.get(f"http://localhost:8000{endpoint}")
            assert response.status_code == 401
    
    def test_invalid_token_rejection(self):
        """Test rejection of invalid tokens"""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = requests.get(
            "http://localhost:8000/api/v1/admin/users",
            headers=headers
        )
        
        assert response.status_code == 401
```

## AWS Testing

### Pre-deployment Testing

```bash
# Test Docker image locally before pushing to ECR
docker build -t smart-pdf-toolkit:aws-test --target production .
docker run -d --name aws-test -p 8000:8000 \
  -e SMART_PDF_OUTPUT_DIR=/app/output \
  -e SMART_PDF_MAX_FILE_SIZE=104857600 \
  smart-pdf-toolkit:aws-test

# Test the container
curl http://localhost:8000/health
curl -X POST -F "file=@tests/fixtures/sample.pdf" \
  -F "operation=info" http://localhost:8000/api/v1/process

# Cleanup
docker stop aws-test && docker rm aws-test
```

### Infrastructure Testing

```bash
# Validate CloudFormation template
aws cloudformation validate-template \
  --template-body file://aws/cloudformation-template.yaml

# Test deployment in staging environment
ENVIRONMENT=staging ./aws/deploy.sh

# Run integration tests against staging
pytest tests/integration/ --base-url=https://staging-alb-url.amazonaws.com
```

### Production Smoke Tests

```python
# tests/aws/test_production_smoke.py
import pytest
import requests
import os

class TestProductionSmoke:
    
    @pytest.fixture
    def base_url(self):
        return os.getenv("PRODUCTION_URL", "https://your-production-url.com")
    
    def test_health_endpoint(self, base_url):
        """Test production health endpoint"""
        response = requests.get(f"{base_url}/health", timeout=10)
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_api_documentation_accessible(self, base_url):
        """Test API documentation is accessible"""
        response = requests.get(f"{base_url}/docs", timeout=10)
        assert response.status_code == 200
    
    def test_basic_file_processing(self, base_url):
        """Test basic file processing works"""
        with open("tests/fixtures/small.pdf", "rb") as f:
            response = requests.post(
                f"{base_url}/api/v1/process",
                files={"file": f},
                data={"operation": "info"},
                timeout=30
            )
        
        assert response.status_code in [200, 202]
```

### Load Testing on AWS

```bash
# Run load test against AWS deployment
locust -f tests/performance/locustfile.py \
  --host=https://your-aws-alb-url.amazonaws.com \
  --users 50 --spawn-rate 5 --run-time 300s --headless

# Monitor CloudWatch metrics during load test
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=smart-pdf-toolkit-service \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T01:00:00Z \
  --period 300 \
  --statistics Average,Maximum
```

## Continuous Testing

### GitHub Actions Workflow

Create `.github/workflows/test.yml`:

```yaml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr libreoffice wkhtmltopdf poppler-utils
    
    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -e ".[dev]"
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=smart_pdf_toolkit --cov-report=xml
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
    
    - name: Run security tests
      run: |
        pytest tests/security/ -v
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  docker-test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t smart-pdf-toolkit:test .
    
    - name: Test Docker image
      run: |
        docker run -d --name test-container -p 8000:8000 smart-pdf-toolkit:test
        sleep 30
        curl -f http://localhost:8000/health || exit 1
        docker stop test-container
```

### Pre-commit Hooks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  
  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest-unit
        entry: pytest tests/unit/ -v
        language: system
        pass_filenames: false
        always_run: true
```

Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

This comprehensive testing guide ensures your Smart PDF Toolkit is thoroughly tested before deployment and maintains quality in production.