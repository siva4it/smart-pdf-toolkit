"""
Content extraction endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from ..models import (
    ExtractTextRequest,
    ExtractImagesRequest,
    ExtractTablesRequest,
    OperationResult
)
from ..services import get_content_extractor_service, get_file_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/text", response_model=OperationResult)
async def extract_text(
    request: ExtractTextRequest,
    content_service = Depends(get_content_extractor_service),
    file_manager = Depends(get_file_manager)
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
    file_manager = Depends(get_file_manager)
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
    file_manager = Depends(get_file_manager)
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
    file_manager = Depends(get_file_manager)
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
    file_manager = Depends(get_file_manager)
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