"""
Health check endpoints for the API.
"""

from fastapi import APIRouter, Depends
from datetime import datetime
import psutil
import os

from ..models import HealthResponse
from ..config import get_api_config, APIConfig

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check(config: APIConfig = Depends(get_api_config)):
    """
    Basic health check endpoint.
    
    Returns:
        Health status information
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0",
        services={
            "api": "healthy",
            "storage": "healthy" if os.path.exists(config.temp_dir) else "unhealthy"
        }
    )


@router.get("/detailed")
async def detailed_health_check(config: APIConfig = Depends(get_api_config)):
    """
    Detailed health check with system information.
    
    Returns:
        Detailed health status and system metrics
    """
    # Get system metrics
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "1.0.0",
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
        },
        "services": {
            "api": "healthy",
            "storage": "healthy" if os.path.exists(config.temp_dir) else "unhealthy",
            "upload_dir": "healthy" if os.path.exists(config.upload_dir) else "unhealthy",
            "output_dir": "healthy" if os.path.exists(config.output_dir) else "unhealthy"
        },
        "configuration": {
            "max_file_size": config.max_file_size,
            "max_concurrent_jobs": config.max_concurrent_jobs,
            "debug_mode": config.debug
        }
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration.
    
    Returns:
        Simple ready status
    """
    return {"status": "ready", "timestamp": datetime.now()}