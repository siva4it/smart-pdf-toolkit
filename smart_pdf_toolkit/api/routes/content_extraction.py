"""
Content extraction endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Security
from fastapi.responses import FileResponse
import logging
import os

from ..models import (
    ExtractTextRequest,
    ExtractImagesRequest,
    ExtractTablesRequest,
    OperationResult
)
from ..services import get_content_extractor_service, get_file_manager
from ..auth import get_current_active_user, User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/text", response_model=OperationResult)
async def extract_text(
    request: ExtractTextRequest,
    content_service = Depends(get_content_extractor_service),
    file_manager = Depends(get_file_manager),
    current_user: User = Security(get_current_active_user)
):
    """
    Extract text content from a PDF document.
    
    Args:
        request: Text extraction request
        content_service: Content extractor service
        file_manager: File manager service
        
    Returns:
        Operation result with extracted text
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Perform text extraction
        result = content_service.extract_text(file_path, request.preserve_layout)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"Text extraction completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/images", response_model=OperationResult)
async def extract_images(
    request: ExtractImagesRequest,
    content_service = Depends(get_content_extractor_service),
    file_manager = Depends(get_file_manager),
    current_user: User = Security(get_current_active_user)
):
    """
    Extract images from a PDF document.
    
    Args:
        request: Image extraction request
        content_service: Content extractor service
        file_manager: File manager service
        
    Returns:
        Operation result with extracted images
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Create output directory for images
        output_dir = await file_manager.get_output_path(f"images_{request.file_id}")
        
        # Perform image extraction
        result = content_service.extract_images(file_path, output_dir)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"Image extraction completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tables", response_model=OperationResult)
async def extract_tables(
    request: ExtractTablesRequest,
    content_service = Depends(get_content_extractor_service),
    file_manager = Depends(get_file_manager),
    current_user: User = Security(get_current_active_user)
):
    """
    Extract tables from a PDF document.
    
    Args:
        request: Table extraction request
        content_service: Content extractor service
        file_manager: File manager service
        
    Returns:
        Operation result with extracted tables
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Perform table extraction
        result = content_service.extract_tables(file_path, request.output_format)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"Table extraction completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Table extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metadata", response_model=OperationResult)
async def extract_metadata(
    file_id: str,
    content_service = Depends(get_content_extractor_service),
    file_manager = Depends(get_file_manager),
    current_user: User = Security(get_current_active_user)
):
    """
    Extract metadata from a PDF document.
    
    Args:
        file_id: File identifier
        content_service: Content extractor service
        file_manager: File manager service
        
    Returns:
        Operation result with extracted metadata
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_id}"
            )
        
        # Perform metadata extraction
        result = content_service.extract_metadata(file_path)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"Metadata extraction completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metadata extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/links", response_model=OperationResult)
async def extract_links(
    file_id: str,
    content_service = Depends(get_content_extractor_service),
    file_manager = Depends(get_file_manager),
    current_user: User = Security(get_current_active_user)
):
    """
    Extract links from a PDF document.
    
    Args:
        file_id: File identifier
        content_service: Content extractor service
        file_manager: File manager service
        
    Returns:
        Operation result with extracted links
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_id}"
            )
        
        # Perform link extraction
        result = content_service.extract_links(file_path)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"Link extraction completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Link extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocr", response_model=OperationResult)
async def perform_ocr(
    file_id: str,
    languages: list = None,
    file_manager = Depends(get_file_manager),
    current_user: User = Security(get_current_active_user)
):
    """
    Perform OCR on a PDF document.
    
    Args:
        file_id: File identifier
        languages: List of languages for OCR (optional)
        file_manager: File manager service
        
    Returns:
        Operation result with OCR text
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_id}"
            )
        
        # Import OCR service
        from ..services import get_ocr_processor_service
        ocr_service = get_ocr_processor_service()
        
        # Perform OCR
        result = ocr_service.perform_ocr(file_path, languages or ['eng'])
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"OCR processing completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{file_id}")
async def download_extracted_content(
    file_id: str,
    file_manager = Depends(get_file_manager),
    current_user: User = Security(get_current_active_user)
):
    """
    Download extracted content file.
    
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
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.csv': 'text/csv',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg'
        }
        
        media_type = media_type_map.get(file_ext, 'application/octet-stream')
        
        logger.info(f"Content download requested: {file_id}")
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content download failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))