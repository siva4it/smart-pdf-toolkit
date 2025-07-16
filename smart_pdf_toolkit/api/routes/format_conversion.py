"""
Format conversion endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from typing import List
import logging
import os

from ..models import (
    ConvertToImagesRequest,
    ConvertFromImagesRequest,
    ConvertToOfficeRequest,
    OperationResult
)
from ..services import get_format_converter_service, get_file_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/to-images", response_model=OperationResult)
async def convert_pdf_to_images(
    request: ConvertToImagesRequest,
    format_service = Depends(get_format_converter_service),
    file_manager = Depends(get_file_manager)
):
    """
    Convert PDF to images.
    
    Args:
        request: Image conversion request
        format_service: Format converter service
        file_manager: File manager service
        
    Returns:
        Operation result with converted images
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Perform conversion
        result = format_service.pdf_to_images(
            file_path, 
            request.output_format, 
            request.quality
        )
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"PDF to images conversion completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF to images conversion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/from-images", response_model=OperationResult)
async def convert_images_to_pdf(
    request: ConvertFromImagesRequest,
    format_service = Depends(get_format_converter_service),
    file_manager = Depends(get_file_manager)
):
    """
    Convert images to PDF.
    
    Args:
        request: PDF conversion request
        format_service: Format converter service
        file_manager: File manager service
        
    Returns:
        Operation result with converted PDF
    """
    try:
        # Get file paths from IDs
        image_paths = []
        for file_id in request.file_ids:
            file_path = await file_manager.get_file_path(file_id)
            if not file_path:
                raise HTTPException(
                    status_code=404,
                    detail=f"Image file not found: {file_id}"
                )
            image_paths.append(file_path)
        
        # Generate output filename
        output_filename = request.output_filename or "converted_document.pdf"
        output_path = await file_manager.get_output_path(output_filename)
        
        # Perform conversion
        result = format_service.images_to_pdf(image_paths, output_path)
        
        if result.success:
            # Register output file
            await file_manager.register_output_file(output_path)
        
        logger.info(f"Images to PDF conversion completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Images to PDF conversion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/to-office", response_model=OperationResult)
async def convert_pdf_to_office(
    request: ConvertToOfficeRequest,
    format_service = Depends(get_format_converter_service),
    file_manager = Depends(get_file_manager)
):
    """
    Convert PDF to Office format.
    
    Args:
        request: Office conversion request
        format_service: Format converter service
        file_manager: File manager service
        
    Returns:
        Operation result with converted Office document
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Perform conversion
        result = format_service.pdf_to_office(file_path, request.target_format)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"PDF to Office conversion completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF to Office conversion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-images", response_model=List[dict])
async def upload_images(
    files: List[UploadFile] = File(...),
    file_manager = Depends(get_file_manager)
):
    """
    Upload multiple image files for conversion.
    
    Args:
        files: List of image files to upload
        file_manager: File manager service
        
    Returns:
        List of uploaded file information
    """
    try:
        uploaded_files = []
        
        for file in files:
            # Validate file type
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Only image files are allowed: {file.filename}"
                )
            
            # Save uploaded file
            file_info = await file_manager.save_uploaded_file(file)
            uploaded_files.append({
                "file_id": file_info.file_id,
                "filename": file_info.filename,
                "size": file_info.size
            })
        
        logger.info(f"Images uploaded successfully: {len(uploaded_files)} files")
        return uploaded_files
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{file_id}")
async def download_converted_file(
    file_id: str,
    file_manager = Depends(get_file_manager)
):
    """
    Download converted file.
    
    Args:
        file_id: File identifier
        file_manager: File manager service
        
    Returns:
        File download response
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(file_id)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_id}"
            )
        
        # Get filename and determine media type
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower()
        
        media_type_map = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.tiff': 'image/tiff'
        }
        
        media_type = media_type_map.get(file_ext, 'application/octet-stream')
        
        logger.info(f"Converted file download requested: {file_id}")
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Converted file download failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))