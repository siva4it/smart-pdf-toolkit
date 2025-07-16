"""
PDF operations endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List
import logging

from ..models import (
    MergePDFRequest,
    SplitPDFRequest,
    RotatePagesRequest,
    OperationResult,
    FileUploadResponse
)
from ..services import get_pdf_operations_service, get_file_manager
from ..config import get_api_config

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=FileUploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    file_manager = Depends(get_file_manager)
):
    """
    Upload a PDF file for processing.
    
    Args:
        file: PDF file to upload
        file_manager: File manager service
        
    Returns:
        File upload response with file ID
    """
    try:
        # Validate file type
        if not file.content_type or "pdf" not in file.content_type.lower():
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are allowed"
            )
        
        # Save uploaded file
        file_info = await file_manager.save_uploaded_file(file)
        
        logger.info(f"PDF uploaded successfully: {file_info.file_id}")
        return file_info
        
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge", response_model=OperationResult)
async def merge_pdfs(
    request: MergePDFRequest,
    pdf_service = Depends(get_pdf_operations_service),
    file_manager = Depends(get_file_manager)
):
    """
    Merge multiple PDF files into a single document.
    
    Args:
        request: Merge request with file IDs
        pdf_service: PDF operations service
        file_manager: File manager service
        
    Returns:
        Operation result with merged PDF
    """
    try:
        # Get file paths from IDs
        file_paths = []
        for file_id in request.file_ids:
            file_path = await file_manager.get_file_path(file_id)
            if not file_path:
                raise HTTPException(
                    status_code=404,
                    detail=f"File not found: {file_id}"
                )
            file_paths.append(file_path)
        
        # Generate output filename
        output_filename = request.output_filename or "merged_document.pdf"
        output_path = await file_manager.get_output_path(output_filename)
        
        # Perform merge operation
        result = pdf_service.merge_pdfs(file_paths, output_path)
        
        if result.success:
            # Register output file
            await file_manager.register_output_file(output_path)
        
        logger.info(f"PDF merge completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF merge failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/split", response_model=OperationResult)
async def split_pdf(
    request: SplitPDFRequest,
    pdf_service = Depends(get_pdf_operations_service),
    file_manager = Depends(get_file_manager)
):
    """
    Split a PDF into multiple documents based on page ranges.
    
    Args:
        request: Split request with file ID and page ranges
        pdf_service: PDF operations service
        file_manager: File manager service
        
    Returns:
        Operation result with split PDFs
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Convert page ranges to tuples
        page_ranges = [tuple(range_list) for range_list in request.page_ranges]
        
        # Perform split operation
        result = pdf_service.split_pdf(file_path, page_ranges)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"PDF split completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF split failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rotate", response_model=OperationResult)
async def rotate_pages(
    request: RotatePagesRequest,
    pdf_service = Depends(get_pdf_operations_service),
    file_manager = Depends(get_file_manager)
):
    """
    Rotate specific pages in a PDF document.
    
    Args:
        request: Rotation request with file ID and page rotations
        pdf_service: PDF operations service
        file_manager: File manager service
        
    Returns:
        Operation result with rotated PDF
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Perform rotation operation
        result = pdf_service.rotate_pages(file_path, request.page_rotations)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"PDF rotation completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF rotation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-pages", response_model=OperationResult)
async def extract_pages(
    file_id: str,
    pages: List[int],
    pdf_service = Depends(get_pdf_operations_service),
    file_manager = Depends(get_file_manager)
):
    """
    Extract specific pages from a PDF document.
    
    Args:
        file_id: File ID
        pages: List of page numbers to extract
        pdf_service: PDF operations service
        file_manager: File manager service
        
    Returns:
        Operation result with extracted pages
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_id}"
            )
        
        # Perform page extraction
        result = pdf_service.extract_pages(file_path, pages)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"Page extraction completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Page extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reorder-pages", response_model=OperationResult)
async def reorder_pages(
    file_id: str,
    new_order: List[int],
    pdf_service = Depends(get_pdf_operations_service),
    file_manager = Depends(get_file_manager)
):
    """
    Reorder pages in a PDF document.
    
    Args:
        file_id: File ID
        new_order: New page order
        pdf_service: PDF operations service
        file_manager: File manager service
        
    Returns:
        Operation result with reordered PDF
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_id}"
            )
        
        # Perform page reordering
        result = pdf_service.reorder_pages(file_path, new_order)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"Page reordering completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Page reordering failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))