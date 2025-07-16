"""
Batch processing endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Security
import logging

from ..models import (
    BatchJobRequest,
    BatchJobResponse,
    BatchJobStatus,
    OperationResult
)
from ..services import get_batch_processor_service, get_file_manager
from ..auth import get_current_active_user, get_current_write_user, User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/jobs", response_model=BatchJobResponse)
async def create_batch_job(
    request: BatchJobRequest,
    batch_service = Depends(get_batch_processor_service),
    file_manager = Depends(get_file_manager),
    current_user: User = Security(get_current_write_user)
):
    """
    Create a new batch processing job.
    
    Args:
        request: Batch job request
        batch_service: Batch processor service
        file_manager: File manager service
        
    Returns:
        Batch job response with job information
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
        
        # Create batch job
        batch_job = batch_service.create_batch_job(
            request.operation,
            file_paths,
            request.parameters
        )
        
        # Convert to response model
        response = BatchJobResponse(
            job_id=batch_job.job_id,
            operation=batch_job.operation,
            status=batch_job.status,
            total_files=batch_job.total_files,
            processed_files=batch_job.processed_files,
            failed_files=batch_job.failed_files,
            created_at=batch_job.created_at,
            completed_at=batch_job.completed_at,
            results=batch_job.results
        )
        
        logger.info(f"Batch job created: {batch_job.job_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch job creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=BatchJobResponse)
async def get_batch_job_status(
    job_id: str,
    batch_service = Depends(get_batch_processor_service),
    current_user: User = Security(get_current_active_user)
):
    """
    Get the status of a batch processing job.
    
    Args:
        job_id: Batch job identifier
        batch_service: Batch processor service
        
    Returns:
        Batch job status information
    """
    try:
        # Get batch job status
        batch_job = batch_service.get_batch_status(job_id)
        
        if not batch_job:
            raise HTTPException(
                status_code=404,
                detail=f"Batch job not found: {job_id}"
            )
        
        # Convert to response model
        response = BatchJobResponse(
            job_id=batch_job.job_id,
            operation=batch_job.operation,
            status=batch_job.status,
            total_files=batch_job.total_files,
            processed_files=batch_job.processed_files,
            failed_files=batch_job.failed_files,
            created_at=batch_job.created_at,
            completed_at=batch_job.completed_at,
            results=batch_job.results
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get batch job status failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def cancel_batch_job(
    job_id: str,
    batch_service = Depends(get_batch_processor_service),
    current_user: User = Security(get_current_write_user)
):
    """
    Cancel a running batch processing job.
    
    Args:
        job_id: Batch job identifier
        batch_service: Batch processor service
        
    Returns:
        Cancellation result
    """
    try:
        # Cancel batch job
        success = batch_service.cancel_batch_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Batch job not found or cannot be cancelled: {job_id}"
            )
        
        logger.info(f"Batch job cancelled: {job_id}")
        return {"message": f"Batch job {job_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel batch job failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/results")
async def get_batch_job_results(
    job_id: str,
    batch_service = Depends(get_batch_processor_service),
    current_user: User = Security(get_current_active_user)
):
    """
    Get detailed results of a completed batch job.
    
    Args:
        job_id: Batch job identifier
        batch_service: Batch processor service
        
    Returns:
        Detailed batch job results
    """
    try:
        # Get batch job
        batch_job = batch_service.get_batch_status(job_id)
        
        if not batch_job:
            raise HTTPException(
                status_code=404,
                detail=f"Batch job not found: {job_id}"
            )
        
        # Get detailed results if available
        try:
            detailed_results = batch_service.generate_batch_report(job_id)
            return detailed_results
        except:
            # Fallback to basic results
            return {
                "job_id": batch_job.job_id,
                "operation": batch_job.operation,
                "status": batch_job.status.value,
                "total_files": batch_job.total_files,
                "processed_files": batch_job.processed_files,
                "failed_files": batch_job.failed_files,
                "results": [
                    {
                        "success": result.success,
                        "message": result.message,
                        "output_files": result.output_files,
                        "execution_time": result.execution_time,
                        "warnings": result.warnings,
                        "errors": result.errors
                    }
                    for result in batch_job.results
                ]
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get batch job results failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def list_batch_jobs(
    batch_service = Depends(get_batch_processor_service),
    current_user: User = Security(get_current_active_user)
):
    """
    List all batch processing jobs.
    
    Args:
        batch_service: Batch processor service
        
    Returns:
        List of batch jobs
    """
    try:
        # This would need to be implemented in the batch processor
        # For now, return a placeholder
        return {
            "message": "Batch job listing not yet implemented",
            "jobs": []
        }
        
    except Exception as e:
        logger.error(f"List batch jobs failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))