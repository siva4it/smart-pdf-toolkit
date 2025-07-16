"""
Main FastAPI application for Smart PDF Toolkit.

This module sets up the FastAPI application with all routes, middleware,
and configuration for the PDF processing API.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
from typing import Dict, Any

from .config import APIConfig, get_api_config
from .middleware import setup_middleware
from .routes import health
from .routes import auth
from .routes import pdf_operations
from .routes import content_extraction
from .routes import ai_services
from .routes import batch_processing
from .routes import format_conversion
from .routes import security
from .routes import optimization
from .exceptions import setup_exception_handlers
from ..core.exceptions import PDFToolkitError


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Smart PDF Toolkit API...")
    
    # Initialize services
    config = get_api_config()
    
    # Create necessary directories
    os.makedirs(config.upload_dir, exist_ok=True)
    os.makedirs(config.temp_dir, exist_ok=True)
    os.makedirs(config.output_dir, exist_ok=True)
    
    logger.info(f"API started on {config.host}:{config.port}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Smart PDF Toolkit API...")


def create_app(config: APIConfig = None) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        config: Optional API configuration
        
    Returns:
        Configured FastAPI application
    """
    if config is None:
        config = get_api_config()
    
    # Create FastAPI app
    app = FastAPI(
        title="Smart PDF Toolkit API",
        description="Comprehensive PDF processing and analysis API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Setup middleware
    setup_middleware(app, config)
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Add root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "Smart PDF Toolkit API",
            "version": "1.0.0",
            "description": "Comprehensive PDF processing and analysis API",
            "docs": "/docs",
            "health": "/health"
        }
    
    # Include routers
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(pdf_operations.router, prefix="/api/v1/pdf", tags=["PDF Operations"])
    app.include_router(content_extraction.router, prefix="/api/v1/extract", tags=["Content Extraction"])
    app.include_router(ai_services.router, prefix="/api/v1/ai", tags=["AI Services"])
    app.include_router(batch_processing.router, prefix="/api/v1/batch", tags=["Batch Processing"])
    app.include_router(format_conversion.router, prefix="/api/v1/convert", tags=["Format Conversion"])
    app.include_router(security.router, prefix="/api/v1/security", tags=["Security"])
    app.include_router(optimization.router, prefix="/api/v1/optimize", tags=["Optimization"])
    
    return app


# Create the main application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    config = get_api_config()
    uvicorn.run(
        "smart_pdf_toolkit.api.main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info" if not config.debug else "debug"
    )