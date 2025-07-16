"""
Exception handlers for the FastAPI application.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from typing import Union

from ..core.exceptions import (
    PDFToolkitError,
    PDFProcessingError,
    SecurityError,
    ConversionError,
    OCRError,
    AIServiceError,
    ValidationError,
    FileOperationError
)

logger = logging.getLogger(__name__)


async def pdf_toolkit_exception_handler(request: Request, exc: PDFToolkitError) -> JSONResponse:
    """
    Handle PDFToolkitError and its subclasses.
    
    Args:
        request: FastAPI request object
        exc: PDFToolkitError exception
        
    Returns:
        JSON error response
    """
    logger.error(f"PDFToolkitError: {exc.message}")
    
    # Map exception types to HTTP status codes
    status_code_map = {
        ValidationError: 400,
        FileOperationError: 404,
        SecurityError: 403,
        ConversionError: 422,
        OCRError: 422,
        AIServiceError: 503,
        PDFProcessingError: 500,
        PDFToolkitError: 500
    }
    
    status_code = status_code_map.get(type(exc), 500)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message,
                "code": exc.error_code,
                "details": exc.details
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle request validation errors.
    
    Args:
        request: FastAPI request object
        exc: RequestValidationError exception
        
    Returns:
        JSON error response
    """
    logger.error(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "ValidationError",
                "message": "Request validation failed",
                "details": exc.errors()
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions.
    
    Args:
        request: FastAPI request object
        exc: HTTPException
        
    Returns:
        JSON error response
    """
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPException",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle general exceptions.
    
    Args:
        request: FastAPI request object
        exc: General exception
        
    Returns:
        JSON error response
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An internal server error occurred",
                "details": str(exc) if logger.level <= logging.DEBUG else None
            }
        }
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Setup exception handlers for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    
    # Register exception handlers
    app.add_exception_handler(PDFToolkitError, pdf_toolkit_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)