"""
PDF security endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from ..models import (
    AddPasswordRequest,
    RemovePasswordRequest,
    SetPermissionsRequest,
    AddWatermarkRequest,
    OperationResult
)
from ..services import get_security_manager_service, get_file_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/add-password", response_model=OperationResult)
async def add_password_protection(
    request: AddPasswordRequest,
    security_service = Depends(get_security_manager_service),
    file_manager = Depends(get_file_manager)
):
    """
    Add password protection to a PDF document.
    
    Args:
        request: Password protection request
        security_service: Security manager service
        file_manager: File manager service
        
    Returns:
        Operation result with protected PDF
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Add password protection
        result = security_service.add_password(
            file_path,
            request.user_password,
            request.owner_password
        )
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"Password protection added: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add password protection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remove-password", response_model=OperationResult)
async def remove_password_protection(
    request: RemovePasswordRequest,
    security_service = Depends(get_security_manager_service),
    file_manager = Depends(get_file_manager)
):
    """
    Remove password protection from a PDF document.
    
    Args:
        request: Password removal request
        security_service: Security manager service
        file_manager: File manager service
        
    Returns:
        Operation result with unprotected PDF
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Remove password protection
        result = security_service.remove_password(file_path, request.password)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"Password protection removed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remove password protection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set-permissions", response_model=OperationResult)
async def set_pdf_permissions(
    request: SetPermissionsRequest,
    security_service = Depends(get_security_manager_service),
    file_manager = Depends(get_file_manager)
):
    """
    Set permissions for a PDF document.
    
    Args:
        request: Permissions request
        security_service: Security manager service
        file_manager: File manager service
        
    Returns:
        Operation result with permission-controlled PDF
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Set permissions
        result = security_service.set_permissions(file_path, request.permissions)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"PDF permissions set: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Set PDF permissions failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-watermark", response_model=OperationResult)
async def add_watermark(
    request: AddWatermarkRequest,
    security_service = Depends(get_security_manager_service),
    file_manager = Depends(get_file_manager)
):
    """
    Add watermark to a PDF document.
    
    Args:
        request: Watermark request
        security_service: Security manager service
        file_manager: File manager service
        
    Returns:
        Operation result with watermarked PDF
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Prepare watermark configuration
        watermark_config = {
            "text": request.watermark_text,
            "image_path": None,
            "position": request.position,
            "opacity": request.opacity
        }
        
        # If watermark image is provided, get its path
        if request.watermark_image:
            image_path = await file_manager.get_file_path(request.watermark_image)
            if image_path:
                watermark_config["image_path"] = image_path
        
        # Add watermark
        result = security_service.add_watermark(file_path, watermark_config)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"Watermark added: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add watermark failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))