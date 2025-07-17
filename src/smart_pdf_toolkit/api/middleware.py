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
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline';"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


async def sql_injection_protection_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware for basic SQL injection protection.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/endpoint function
        
    Returns:
        Response object
    """
    import re
    
    # Check query parameters for SQL injection patterns
    for param, value in request.query_params.items():
        if isinstance(value, str) and _contains_sql_injection(value):
            logger.warning(f"Potential SQL injection detected in query parameter: {param}={value}")
            return Response(
                content="Invalid request",
                status_code=400,
                media_type="text/plain"
            )
    
    # Continue processing the request
    response = await call_next(request)
    
    return response


def _contains_sql_injection(value: str) -> bool:
    """
    Check if a string contains SQL injection patterns.
    
    Args:
        value: String to check
        
    Returns:
        True if SQL injection pattern found, False otherwise
    """
    import re
    
    # Simple SQL injection patterns
    patterns = [
        r"(?i)\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC)\b.*\b(FROM|INTO|TABLE|DATABASE|SCHEMA)\b",
        r"(?i)\b(UNION|JOIN)\b.*\b(SELECT)\b",
        r"(?i)\b(OR|AND)\b.*\b(TRUE|FALSE|1|0)\b.*--",
        r"(?i)\b(OR|AND)\b.*\b(TRUE|FALSE|1|0)\b.*#",
        r"(?i)\b(OR|AND)\b.*\b(TRUE|FALSE|1|0)\b.*//",
        r"(?i)\b(OR|AND)\b.*\b(TRUE|FALSE|1|0)\b.*\*\/",
        r"(?i)\b(OR|AND)\b.*\b(TRUE|FALSE|1|0)\b.*;",
        r"(?i)'; DROP TABLE"
    ]
    
    for pattern in patterns:
        if re.search(pattern, value):
            return True
    
    return False


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
    app.middleware("http")(sql_injection_protection_middleware)