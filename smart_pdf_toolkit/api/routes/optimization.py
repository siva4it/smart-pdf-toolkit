"""
PDF optimization endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from ..models import (
    OptimizePDFRequest,
    OperationResult
)
from ..services import get_optimization_engine_service, get_file_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/compress", response_model=OperationResult)
async def compress_pdf(
    request: OptimizePDFRequest,
    optimization_service = Depends(get_optimization_engine_service),
    file_manager = Depends(get_file_manager)
):
    """
    Compress a PDF document.
    
    Args:
        request: PDF compression request
        optimization_service: Optimization engine service
        file_manager: File manager service
        
    Returns:
        Operation result with compressed PDF
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Compress PDF
        result = optimization_service.compress_pdf(file_path, request.compression_level)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"PDF compression completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF compression failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-web", response_model=OperationResult)
async def optimize_for_web(
    file_id: str,
    optimization_service = Depends(get_optimization_engine_service),
    file_manager = Depends(get_file_manager)
):
    """
    Optimize PDF for web viewing.
    
    Args:
        file_id: File identifier
        optimization_service: Optimization engine service
        file_manager: File manager service
        
    Returns:
        Operation result with web-optimized PDF
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_id}"
            )
        
        # Optimize for web
        result = optimization_service.optimize_for_web(file_path)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"Web optimization completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Web optimization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-images", response_model=OperationResult)
async def optimize_images(
    file_id: str,
    quality: int = 85,
    optimization_service = Depends(get_optimization_engine_service),
    file_manager = Depends(get_file_manager)
):
    """
    Optimize images within a PDF document.
    
    Args:
        file_id: File identifier
        quality: Image quality (1-100)
        optimization_service: Optimization engine service
        file_manager: File manager service
        
    Returns:
        Operation result with image-optimized PDF
    """
    try:
        # Validate quality parameter
        if not 1 <= quality <= 100:
            raise HTTPException(
                status_code=400,
                detail="Quality must be between 1 and 100"
            )
        
        # Get file path from ID
        file_path = await file_manager.get_file_path(file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_id}"
            )
        
        # Optimize images
        result = optimization_service.optimize_images(file_path, quality)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"Image optimization completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image optimization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/{file_id}")
async def analyze_pdf_size(
    file_id: str,
    file_manager = Depends(get_file_manager)
):
    """
    Analyze PDF file size and optimization potential.
    
    Args:
        file_id: File identifier
        file_manager: File manager service
        
    Returns:
        PDF size analysis information
    """
    try:
        import os
        
        # Get file path from ID
        file_path = await file_manager.get_file_path(file_id)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_id}"
            )
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Basic analysis (in a real implementation, this would be more sophisticated)
        analysis = {
            "file_id": file_id,
            "current_size": file_size,
            "current_size_mb": round(file_size / (1024 * 1024), 2),
            "estimated_compression": {
                "low": round(file_size * 0.9),
                "medium": round(file_size * 0.7),
                "high": round(file_size * 0.5)
            },
            "recommendations": []
        }
        
        # Add recommendations based on file size
        if file_size > 10 * 1024 * 1024:  # > 10MB
            analysis["recommendations"].append("Consider high compression for large file")
        if file_size > 5 * 1024 * 1024:   # > 5MB
            analysis["recommendations"].append("Image optimization recommended")
        
        analysis["recommendations"].append("Web optimization for faster loading")
        
        logger.info(f"PDF size analysis completed for: {file_id}")
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF size analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))