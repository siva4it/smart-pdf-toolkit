"""
AI services endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
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

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/summarize", response_model=OperationResult)
async def summarize_document(
    request: SummarizeRequest,
    ai_service = Depends(get_ai_services_service),
    file_manager = Depends(get_file_manager)
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
    file_manager = Depends(get_file_manager)
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
    file_manager = Depends(get_file_manager)
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
    file_manager = Depends(get_file_manager)
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
    file_manager = Depends(get_file_manager)
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
    file_manager = Depends(get_file_manager)
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
    ai_service = Depends(get_ai_services_service)
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