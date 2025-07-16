# Multi-stage Dockerfile for Smart PDF Toolkit
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    tesseract-ocr-deu \
    tesseract-ocr-spa \
    libreoffice \
    wkhtmltopdf \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy requirements first for better caching
COPY --chown=app:app requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --user --no-cache-dir -e ".[dev]"

# Copy source code
COPY --chown=app:app . .

# Expose ports
EXPOSE 8000

# Default command for development
CMD ["python", "-m", "smart_pdf_toolkit.api.main"]

# Production stage
FROM base as production

# Copy only necessary files
COPY --chown=app:app smart_pdf_toolkit/ ./smart_pdf_toolkit/
COPY --chown=app:app pyproject.toml setup.py README.md ./

# Install the package
RUN pip install --user --no-cache-dir .

# Create directories for file processing
RUN mkdir -p uploads temp output

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "-m", "smart_pdf_toolkit.api.main", "--host", "0.0.0.0", "--port", "8000"]

# CLI-only stage
FROM base as cli

# Copy only CLI-related files
COPY --chown=app:app smart_pdf_toolkit/ ./smart_pdf_toolkit/
COPY --chown=app:app pyproject.toml setup.py README.md ./

# Install the package
RUN pip install --user --no-cache-dir .

# Create directories for file processing
RUN mkdir -p uploads temp output

# Default command
ENTRYPOINT ["python", "-m", "smart_pdf_toolkit.cli.main"]
CMD ["--help"]