"""
AI services endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Security
import logging

from ..models import (
    SummarizeRequest,
    AnalyzeContentRequest,
    ClassifyDocumentRequest,
    AnswerQuestionRequest,
    TranslateContentRequest,
    ChatSessionRequest,
    ChatMessageRequest,
    ChatResponse,
    OperationResult
)
from ..services import get_ai_services_service, get_file_manager
from ..auth import get_current_active_user, User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/summarize", response_model=OperationResult)
async def summarize_document(
    request: SummarizeRequest,
    ai_service = Depends(get_ai_services_service),
    file_manager = Depends(get_file_manager),
    current_user: User = Security(get_current_active_user)
):
    """
    Generate a summary of a PDF document.
    
    Args:
        request: Summarization request
        ai_service: AI services instance
        file_manager: File manager service
        
    Returns:
        Operation result with document summary
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Perform summarization
        result = ai_service.summarize_document(file_path, request.summary_length)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"Document summarization completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document summarization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=OperationResult)
async def analyze_content(
    request: AnalyzeContentRequest,
    ai_service = Depends(get_ai_services_service),
    file_manager = Depends(get_file_manager),
    current_user: User = Security(get_current_active_user)
):
    """
    Analyze content of a PDF document.
    
    Args:
        request: Content analysis request
        ai_service: AI services instance
        file_manager: File manager service
        
    Returns:
        Operation result with content analysis
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Perform content analysis
        result = ai_service.analyze_content(file_path)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"Content analysis completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify", response_model=OperationResult)
async def classify_document(
    request: ClassifyDocumentRequest,
    ai_service = Depends(get_ai_services_service),
    file_manager = Depends(get_file_manager),
    current_user: User = Security(get_current_active_user)
):
    """
    Classify a PDF document based on its content.
    
    Args:
        request: Document classification request
        ai_service: AI services instance
        file_manager: File manager service
        
    Returns:
        Operation result with document classification
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Perform document classification
        result = ai_service.classify_document(file_path)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"Document classification completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document classification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/question", response_model=OperationResult)
async def answer_question(
    request: AnswerQuestionRequest,
    ai_service = Depends(get_ai_services_service),
    file_manager = Depends(get_file_manager),
    current_user: User = Security(get_current_active_user)
):
    """
    Answer a question about a PDF document.
    
    Args:
        request: Question answering request
        ai_service: AI services instance
        file_manager: File manager service
        
    Returns:
        Operation result with answer
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Answer question
        result = ai_service.answer_question(file_path, request.question)
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"Question answering completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Question answering failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translate", response_model=OperationResult)
async def translate_content(
    request: TranslateContentRequest,
    ai_service = Depends(get_ai_services_service),
    file_manager = Depends(get_file_manager),
    current_user: User = Security(get_current_active_user)
):
    """
    Translate content of a PDF document.
    
    Args:
        request: Translation request
        ai_service: AI services instance
        file_manager: File manager service
        
    Returns:
        Operation result with translated content
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Perform translation
        result = ai_service.translate_content(
            file_path, 
            request.target_language, 
            request.preserve_formatting
        )
        
        if result.success:
            # Register output files
            for output_file in result.output_files:
                await file_manager.register_output_file(output_file)
        
        logger.info(f"Content translation completed: {result.success}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content translation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/start", response_model=dict)
async def start_chat_session(
    request: ChatSessionRequest,
    ai_service = Depends(get_ai_services_service),
    file_manager = Depends(get_file_manager),
    current_user: User = Security(get_current_active_user)
):
    """
    Start an interactive chat session about a PDF document.
    
    Args:
        request: Chat session request
        ai_service: AI services instance
        file_manager: File manager service
        
    Returns:
        Chat session information
    """
    try:
        # Get file path from ID
        file_path = await file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Start chat session
        chat_session = ai_service.interactive_chat(file_path)
        
        if chat_session.get('status') == 'error':
            raise HTTPException(
                status_code=500,
                detail=chat_session.get('error', 'Failed to start chat session')
            )
        
        logger.info(f"Chat session started: {chat_session.get('session_id')}")
        return chat_session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat session start failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/message", response_model=OperationResult)
async def send_chat_message(
    request: ChatMessageRequest,
    ai_service = Depends(get_ai_services_service),
    current_user: User = Security(get_current_active_user)
):
    """
    Send a message in an interactive chat session.
    
    Args:
        request: Chat message request
        ai_service: AI services instance
        
    Returns:
        Operation result with AI response
    """
    try:
        # For simplicity, we'll create a basic chat context
        # In a real implementation, you'd store and retrieve session state
        chat_context = {
            'status': 'active',
            'document_context': '',
            'conversation_history': []
        }
        
        # Continue chat conversation
        result = ai_service.continue_chat(
            request.session_id,
            request.message,
            chat_context
        )
        
        logger.info(f"Chat message processed: {result.success}")
        return result
        
    except Exception as e:
        logger.error(f"Chat message failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{file_id}")
async def download_ai_result(
    file_id: str,
    file_manager = Depends(get_file_manager),
    current_user: User = Security(get_current_active_user)
):
    """
    Download AI processing result file.
    
    Args:
        file_id: File identifier
        file_manager: File manager service
        
    Returns:
        File download response
    """
    try:
        from fastapi.responses import FileResponse
        import os
        
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
            '.pdf': 'application/pdf'
        }
        
        media_type = media_type_map.get(file_ext, 'text/plain')
        
        logger.info(f"AI result download requested: {file_id}")
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI result download failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))