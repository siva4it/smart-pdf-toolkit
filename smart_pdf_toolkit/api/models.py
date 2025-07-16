"""
Pydantic models for API request and response schemas.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OperationResult(BaseModel):
    """Standard operation result model."""
    success: bool
    message: str
    output_files: List[str] = []
    execution_time: float
    warnings: List[str] = []
    errors: List[str] = []


class FileUploadResponse(BaseModel):
    """Response model for file uploads."""
    file_id: str
    filename: str
    size: int
    content_type: str
    upload_time: datetime


# PDF Operations Models
class MergePDFRequest(BaseModel):
    """Request model for PDF merge operation."""
    file_ids: List[str] = Field(..., min_items=2, description="List of file IDs to merge")
    output_filename: Optional[str] = Field(None, description="Output filename")


class SplitPDFRequest(BaseModel):
    """Request model for PDF split operation."""
    file_id: str = Field(..., description="File ID to split")
    page_ranges: List[List[int]] = Field(..., description="Page ranges to split")
    
    @validator('page_ranges')
    def validate_page_ranges(cls, v):
        for page_range in v:
            if len(page_range) != 2 or page_range[0] > page_range[1]:
                raise ValueError("Each page range must be [start, end] with start <= end")
        return v


class RotatePagesRequest(BaseModel):
    """Request model for page rotation."""
    file_id: str = Field(..., description="File ID")
    page_rotations: Dict[int, int] = Field(..., description="Page number to rotation angle mapping")
    
    @validator('page_rotations')
    def validate_rotations(cls, v):
        valid_angles = [90, 180, 270, -90, -180, -270]
        for page, angle in v.items():
            if angle not in valid_angles:
                raise ValueError(f"Invalid rotation angle: {angle}. Must be one of {valid_angles}")
        return v


# Content Extraction Models
class ExtractTextRequest(BaseModel):
    """Request model for text extraction."""
    file_id: str = Field(..., description="File ID")
    preserve_layout: bool = Field(True, description="Whether to preserve text layout")


class ExtractImagesRequest(BaseModel):
    """Request model for image extraction."""
    file_id: str = Field(..., description="File ID")
    output_format: str = Field("png", description="Output image format")
    
    @validator('output_format')
    def validate_format(cls, v):
        valid_formats = ['png', 'jpeg', 'jpg', 'tiff']
        if v.lower() not in valid_formats:
            raise ValueError(f"Invalid format: {v}. Must be one of {valid_formats}")
        return v.lower()


class ExtractTablesRequest(BaseModel):
    """Request model for table extraction."""
    file_id: str = Field(..., description="File ID")
    output_format: str = Field("csv", description="Output format for tables")
    
    @validator('output_format')
    def validate_format(cls, v):
        valid_formats = ['csv', 'excel', 'json']
        if v.lower() not in valid_formats:
            raise ValueError(f"Invalid format: {v}. Must be one of {valid_formats}")
        return v.lower()


# AI Services Models
class SummarizeRequest(BaseModel):
    """Request model for document summarization."""
    file_id: str = Field(..., description="File ID")
    summary_length: int = Field(500, ge=50, le=2000, description="Desired summary length in words")


class AnalyzeContentRequest(BaseModel):
    """Request model for content analysis."""
    file_id: str = Field(..., description="File ID")


class ClassifyDocumentRequest(BaseModel):
    """Request model for document classification."""
    file_id: str = Field(..., description="File ID")


class AnswerQuestionRequest(BaseModel):
    """Request model for question answering."""
    file_id: str = Field(..., description="File ID")
    question: str = Field(..., min_length=1, description="Question to answer")


class TranslateContentRequest(BaseModel):
    """Request model for content translation."""
    file_id: str = Field(..., description="File ID")
    target_language: str = Field(..., min_length=1, description="Target language")
    preserve_formatting: bool = Field(True, description="Whether to preserve formatting")


class ChatSessionRequest(BaseModel):
    """Request model for starting a chat session."""
    file_id: str = Field(..., description="File ID")


class ChatMessageRequest(BaseModel):
    """Request model for chat messages."""
    session_id: str = Field(..., description="Chat session ID")
    message: str = Field(..., min_length=1, description="User message")


class ChatResponse(BaseModel):
    """Response model for chat interactions."""
    session_id: str
    response: str
    conversation_history: List[Dict[str, Any]]
    timestamp: datetime


# Batch Processing Models
class BatchJobRequest(BaseModel):
    """Request model for batch job creation."""
    operation: str = Field(..., description="Operation to perform")
    file_ids: List[str] = Field(..., min_items=1, description="List of file IDs")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")


class BatchJobResponse(BaseModel):
    """Response model for batch jobs."""
    job_id: str
    operation: str
    status: JobStatus
    total_files: int
    processed_files: int
    failed_files: int
    created_at: datetime
    completed_at: Optional[datetime]
    results: List[OperationResult] = []


class BatchJobStatus(BaseModel):
    """Model for batch job status."""
    job_id: str
    status: JobStatus
    progress: float = Field(ge=0.0, le=100.0, description="Progress percentage")
    total_files: int
    processed_files: int
    failed_files: int
    estimated_completion: Optional[datetime]


# Format Conversion Models
class ConvertToImagesRequest(BaseModel):
    """Request model for PDF to images conversion."""
    file_id: str = Field(..., description="File ID")
    output_format: str = Field("png", description="Output image format")
    quality: int = Field(95, ge=1, le=100, description="Image quality (1-100)")
    dpi: int = Field(150, ge=72, le=300, description="DPI for image conversion")


class ConvertFromImagesRequest(BaseModel):
    """Request model for images to PDF conversion."""
    file_ids: List[str] = Field(..., min_items=1, description="List of image file IDs")
    output_filename: Optional[str] = Field(None, description="Output PDF filename")


class ConvertToOfficeRequest(BaseModel):
    """Request model for PDF to Office conversion."""
    file_id: str = Field(..., description="File ID")
    target_format: str = Field(..., description="Target Office format")
    
    @validator('target_format')
    def validate_format(cls, v):
        valid_formats = ['docx', 'xlsx', 'pptx']
        if v.lower() not in valid_formats:
            raise ValueError(f"Invalid format: {v}. Must be one of {valid_formats}")
        return v.lower()


# Security Models
class AddPasswordRequest(BaseModel):
    """Request model for adding password protection."""
    file_id: str = Field(..., description="File ID")
    user_password: str = Field(..., min_length=1, description="User password")
    owner_password: Optional[str] = Field(None, description="Owner password")


class RemovePasswordRequest(BaseModel):
    """Request model for removing password protection."""
    file_id: str = Field(..., description="File ID")
    password: str = Field(..., min_length=1, description="Current password")


class SetPermissionsRequest(BaseModel):
    """Request model for setting PDF permissions."""
    file_id: str = Field(..., description="File ID")
    permissions: Dict[str, bool] = Field(..., description="Permission settings")


class AddWatermarkRequest(BaseModel):
    """Request model for adding watermarks."""
    file_id: str = Field(..., description="File ID")
    watermark_text: Optional[str] = Field(None, description="Watermark text")
    watermark_image: Optional[str] = Field(None, description="Watermark image file ID")
    position: str = Field("center", description="Watermark position")
    opacity: float = Field(0.5, ge=0.0, le=1.0, description="Watermark opacity")


# Optimization Models
class OptimizePDFRequest(BaseModel):
    """Request model for PDF optimization."""
    file_id: str = Field(..., description="File ID")
    compression_level: int = Field(3, ge=1, le=5, description="Compression level (1-5)")
    optimize_images: bool = Field(True, description="Whether to optimize images")
    image_quality: int = Field(85, ge=1, le=100, description="Image quality after optimization")


# Health Check Models
class HealthResponse(BaseModel):
    """Response model for health checks."""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]


# Error Models
class ErrorResponse(BaseModel):
    """Error response model."""
    error: Dict[str, Any]