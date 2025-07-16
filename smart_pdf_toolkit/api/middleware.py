"""
Middleware configuration for the FastAPI application.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import logging
from typing import Callable

from .config import APIConfig

logger = logging.getLogger(__name__)


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware for request/response logging.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/endpoint function
        
    Returns:
        Response object
    """
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(
        f"Response: {response.status_code} - "
        f"Processing time: {process_time:.3f}s"
    )
    
    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


async def security_headers_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware for adding security headers.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/endpoint function
        
    Returns:
        Response object with security headers
    """
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response


def setup_middleware(app: FastAPI, config: APIConfig) -> None:
    """
    Setup all middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
        config: API configuration
    """
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=config.cors_methods,
        allow_headers=config.cors_headers,
    )
    
    # Gzip compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Trusted host middleware (for production)
    if not config.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", config.host]
        )
    
    # Custom middleware
    app.middleware("http")(logging_middleware)
    app.middleware("http")(security_headers_middleware)