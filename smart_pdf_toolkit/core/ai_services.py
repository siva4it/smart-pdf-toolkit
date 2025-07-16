"""
AI Services implementation for Smart PDF Toolkit.

This module provides AI-powered features including document summarization,
content analysis, document classification, and question-answering capabilities.
"""

import os
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import time

from .interfaces import IAIServices, OperationResult
from .exceptions import AIServiceError, ValidationError, FileOperationError
from .content_extractor import ContentExtractor


class AIServices(IAIServices):
    """
    AI Services implementation providing document analysis and AI-powered features.
    
    This class integrates with various AI services and provides fallback mechanisms
    for when AI services are unavailable.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, content_extractor: Optional[Any] = None):
        """
        Initialize AI Services.
        
        Args:
            config: Configuration dictionary with AI service settings
            content_extractor: Optional content extractor instance (for testing)
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize content extractor for text processing
        if content_extractor:
            self.content_extractor = content_extractor
        else:
            from .content_extractor import ContentExtractor
            self.content_extractor = ContentExtractor()
        
        # AI service configuration
        self.ai_api_key = self.config.get('ai_api_key')
        self.ai_service_url = self.config.get('ai_service_url', 'https://api.openai.com/v1')
        self.model_name = self.config.get('model_name', 'gpt-3.5-turbo')
        self.max_tokens = self.config.get('max_tokens', 1000)
        self.temperature = self.config.get('temperature', 0.7)
        
        # Cache settings
        self.enable_cache = self.config.get('enable_cache', True)
        self.cache_dir = self.config.get('cache_dir', 'temp/ai_cache')
        
        # Ensure cache directory exists
        if self.enable_cache:
            os.makedirs(self.cache_dir, exist_ok=True)
        
        self.logger.info("AI Services initialized")
    
    def summarize_document(self, pdf_path: str, summary_length: int = 500) -> OperationResult:
        """
        Generate a summary of the PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            summary_length: Desired length of summary in words
            
        Returns:
            OperationResult with summary content
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            if not os.path.exists(pdf_path):
                raise FileOperationError(f"PDF file not found: {pdf_path}")
            
            if summary_length <= 0:
                raise ValidationError("Summary length must be positive")
            
            self.logger.info(f"Starting document summarization for {pdf_path}")
            
            # Extract text content
            text_result = self.content_extractor.extract_text(pdf_path, preserve_layout=False)
            if not text_result.success:
                raise AIServiceError(f"Failed to extract text: {text_result.message}")
            
            # Read extracted text
            text_content = ""
            if text_result.output_files:
                with open(text_result.output_files[0], 'r', encoding='utf-8') as f:
                    text_content = f.read()
            
            if not text_content.strip():
                return OperationResult(
                    success=False,
                    message="No text content found in PDF",
                    output_files=[],
                    execution_time=time.time() - start_time,
                    warnings=["Document appears to be empty or image-based"],
                    errors=["No extractable text content"]
                )
            
            # Check cache first
            cache_key = self._generate_cache_key(pdf_path, f"summary_{summary_length}")
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.logger.info("Using cached summary result")
                return cached_result
            
            # Generate summary
            summary = self._generate_summary(text_content, summary_length)
            
            # Save summary to file
            output_file = self._save_summary(pdf_path, summary)
            
            # Create result
            result = OperationResult(
                success=True,
                message=f"Document summarized successfully ({len(summary.split())} words)",
                output_files=[output_file],
                execution_time=time.time() - start_time,
                warnings=[],
                errors=[]
            )
            
            # Cache result
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            error_msg = f"Document summarization failed: {str(e)}"
            self.logger.error(error_msg)
            return OperationResult(
                success=False,
                message=error_msg,
                output_files=[],
                execution_time=time.time() - start_time,
                warnings=[],
                errors=[str(e)]
            )
    
    def analyze_content(self, pdf_path: str) -> OperationResult:
        """
        Analyze document content for topics, entities, and themes.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            OperationResult with content analysis
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            if not os.path.exists(pdf_path):
                raise FileOperationError(f"PDF file not found: {pdf_path}")
            
            self.logger.info(f"Starting content analysis for {pdf_path}")
            
            # Extract text content
            text_result = self.content_extractor.extract_text(pdf_path, preserve_layout=False)
            if not text_result.success:
                raise AIServiceError(f"Failed to extract text: {text_result.message}")
            
            # Read extracted text
            text_content = ""
            if text_result.output_files:
                with open(text_result.output_files[0], 'r', encoding='utf-8') as f:
                    text_content = f.read()
            
            if not text_content.strip():
                return OperationResult(
                    success=False,
                    message="No text content found for analysis",
                    output_files=[],
                    execution_time=time.time() - start_time,
                    warnings=["Document appears to be empty or image-based"],
                    errors=["No extractable text content"]
                )
            
            # Check cache first
            cache_key = self._generate_cache_key(pdf_path, "content_analysis")
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.logger.info("Using cached content analysis result")
                return cached_result
            
            # Perform content analysis
            analysis = self._analyze_content(text_content)
            
            # Save analysis to file
            output_file = self._save_analysis(pdf_path, analysis)
            
            # Create result
            result = OperationResult(
                success=True,
                message="Content analysis completed successfully",
                output_files=[output_file],
                execution_time=time.time() - start_time,
                warnings=[],
                errors=[]
            )
            
            # Cache result
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            error_msg = f"Content analysis failed: {str(e)}"
            self.logger.error(error_msg)
            return OperationResult(
                success=False,
                message=error_msg,
                output_files=[],
                execution_time=time.time() - start_time,
                warnings=[],
                errors=[str(e)]
            )
    
    def classify_document(self, pdf_path: str) -> OperationResult:
        """
        Classify document based on content and structure.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            OperationResult with document classification
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            if not os.path.exists(pdf_path):
                raise FileOperationError(f"PDF file not found: {pdf_path}")
            
            self.logger.info(f"Starting document classification for {pdf_path}")
            
            # Extract text content and metadata
            text_result = self.content_extractor.extract_text(pdf_path, preserve_layout=False)
            metadata_result = self.content_extractor.extract_metadata(pdf_path)
            
            if not text_result.success:
                raise AIServiceError(f"Failed to extract text: {text_result.message}")
            
            # Read extracted text
            text_content = ""
            if text_result.output_files:
                with open(text_result.output_files[0], 'r', encoding='utf-8') as f:
                    text_content = f.read()
            
            # Get metadata
            metadata = {}
            if metadata_result.success and metadata_result.output_files:
                with open(metadata_result.output_files[0], 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            # Check cache first
            cache_key = self._generate_cache_key(pdf_path, "classification")
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.logger.info("Using cached classification result")
                return cached_result
            
            # Perform classification
            classification = self._classify_document(text_content, metadata)
            
            # Save classification to file
            output_file = self._save_classification(pdf_path, classification)
            
            # Create result
            result = OperationResult(
                success=True,
                message=f"Document classified as: {classification.get('primary_category', 'Unknown')}",
                output_files=[output_file],
                execution_time=time.time() - start_time,
                warnings=[],
                errors=[]
            )
            
            # Cache result
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            error_msg = f"Document classification failed: {str(e)}"
            self.logger.error(error_msg)
            return OperationResult(
                success=False,
                message=error_msg,
                output_files=[],
                execution_time=time.time() - start_time,
                warnings=[],
                errors=[str(e)]
            )
    
    def answer_question(self, pdf_path: str, question: str) -> OperationResult:
        """
        Answer questions about document content.
        
        Args:
            pdf_path: Path to the PDF file
            question: Question to answer
            
        Returns:
            OperationResult with answer
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            if not os.path.exists(pdf_path):
                raise FileOperationError(f"PDF file not found: {pdf_path}")
            
            if not question.strip():
                raise ValidationError("Question cannot be empty")
            
            self.logger.info(f"Answering question about {pdf_path}: {question[:50]}...")
            
            # Extract text content
            text_result = self.content_extractor.extract_text(pdf_path, preserve_layout=False)
            if not text_result.success:
                raise AIServiceError(f"Failed to extract text: {text_result.message}")
            
            # Read extracted text
            text_content = ""
            if text_result.output_files:
                with open(text_result.output_files[0], 'r', encoding='utf-8') as f:
                    text_content = f.read()
            
            if not text_content.strip():
                return OperationResult(
                    success=False,
                    message="No text content found to answer question",
                    output_files=[],
                    execution_time=time.time() - start_time,
                    warnings=["Document appears to be empty or image-based"],
                    errors=["No extractable text content"]
                )
            
            # Check cache first
            cache_key = self._generate_cache_key(pdf_path, f"qa_{hashlib.md5(question.encode()).hexdigest()}")
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.logger.info("Using cached Q&A result")
                return cached_result
            
            # Generate answer
            answer = self._answer_question(text_content, question)
            
            # Save Q&A to file
            output_file = self._save_qa(pdf_path, question, answer)
            
            # Create result
            result = OperationResult(
                success=True,
                message="Question answered successfully",
                output_files=[output_file],
                execution_time=time.time() - start_time,
                warnings=[],
                errors=[]
            )
            
            # Cache result
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            error_msg = f"Question answering failed: {str(e)}"
            self.logger.error(error_msg)
            return OperationResult(
                success=False,
                message=error_msg,
                output_files=[],
                execution_time=time.time() - start_time,
                warnings=[],
                errors=[str(e)]
            )
    
    def _generate_summary(self, text_content: str, summary_length: int) -> str:
        """
        Generate summary using AI service or fallback method.
        
        Args:
            text_content: Text to summarize
            summary_length: Desired summary length
            
        Returns:
            Generated summary
        """
        try:
            # Try AI service first if available
            if self.ai_api_key:
                return self._ai_summarize(text_content, summary_length)
            else:
                # Fallback to extractive summarization
                return self._extractive_summarize(text_content, summary_length)
        except Exception as e:
            self.logger.warning(f"AI summarization failed, using fallback: {str(e)}")
            return self._extractive_summarize(text_content, summary_length)
    
    def _ai_summarize(self, text_content: str, summary_length: int) -> str:
        """
        Generate summary using AI service (placeholder for actual AI integration).
        
        Args:
            text_content: Text to summarize
            summary_length: Desired summary length
            
        Returns:
            AI-generated summary
        """
        # This is a placeholder for actual AI service integration
        # In a real implementation, this would call OpenAI, Anthropic, or other AI APIs
        
        prompt = f"""
        Please provide a concise summary of the following document in approximately {summary_length} words.
        Focus on the main points, key findings, and important conclusions.
        
        Document text:
        {text_content[:4000]}  # Limit text to avoid token limits
        """
        
        # Placeholder response - in real implementation, this would be an API call
        return self._extractive_summarize(text_content, summary_length)
    
    def _extractive_summarize(self, text_content: str, summary_length: int) -> str:
        """
        Generate extractive summary using simple heuristics.
        
        Args:
            text_content: Text to summarize
            summary_length: Desired summary length
            
        Returns:
            Extractive summary
        """
        # Split into sentences
        sentences = [s.strip() for s in text_content.split('.') if s.strip()]
        
        if not sentences:
            return "No content available for summarization."
        
        # Score sentences based on simple heuristics
        sentence_scores = {}
        
        # Calculate word frequencies
        words = text_content.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Skip short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Score sentences
        for i, sentence in enumerate(sentences):
            sentence_words = sentence.lower().split()
            score = 0
            
            # Frequency score
            for word in sentence_words:
                if word in word_freq:
                    score += word_freq[word]
            
            # Position score (earlier sentences get higher scores)
            position_score = len(sentences) - i
            score += position_score * 0.1
            
            # Length penalty (very short or very long sentences get lower scores)
            length_penalty = 1.0
            if len(sentence_words) < 5 or len(sentence_words) > 50:
                length_penalty = 0.5
            
            sentence_scores[i] = score * length_penalty
        
        # Select top sentences
        sorted_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Build summary
        summary_sentences = []
        current_length = 0
        target_words = summary_length
        
        for sentence_idx, score in sorted_sentences:
            sentence = sentences[sentence_idx]
            sentence_words = len(sentence.split())
            
            if current_length + sentence_words <= target_words:
                summary_sentences.append((sentence_idx, sentence))
                current_length += sentence_words
            
            if current_length >= target_words * 0.8:  # Allow 80% of target
                break
        
        # Sort by original order and join
        summary_sentences.sort(key=lambda x: x[0])
        summary = '. '.join([s[1] for s in summary_sentences])
        
        if not summary:
            # Fallback: take first few sentences
            summary = '. '.join(sentences[:3])
        
        return summary + '.'
    
    def _analyze_content(self, text_content: str) -> Dict[str, Any]:
        """
        Analyze content for topics, entities, and themes.
        
        Args:
            text_content: Text to analyze
            
        Returns:
            Content analysis results
        """
        analysis = {
            'word_count': len(text_content.split()),
            'character_count': len(text_content),
            'sentence_count': len([s for s in text_content.split('.') if s.strip()]),
            'paragraph_count': len([p for p in text_content.split('\n\n') if p.strip()]),
            'topics': self._extract_topics(text_content),
            'entities': self._extract_entities(text_content),
            'sentiment': self._analyze_sentiment(text_content),
            'readability': self._calculate_readability(text_content),
            'language': self._detect_language(text_content),
            'generated_at': datetime.now().isoformat()
        }
        
        return analysis
    
    def _extract_topics(self, text_content: str) -> List[str]:
        """Extract main topics from text using keyword analysis."""
        # Simple keyword-based topic extraction
        words = text_content.lower().split()
        word_freq = {}
        
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
        
        for word in words:
            # Clean word of punctuation
            clean_word = ''.join(c for c in word if c.isalnum()).lower()
            if len(clean_word) > 3 and clean_word not in stop_words:
                word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
        
        # Get top keywords as topics (lower threshold for better results)
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        topics = [word for word, freq in sorted_words[:10] if freq >= 1]
        
        return topics
    
    def _extract_entities(self, text_content: str) -> List[str]:
        """Extract named entities from text using simple patterns."""
        import re
        
        entities = []
        
        # Extract potential names (capitalized words)
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        names = re.findall(name_pattern, text_content)
        entities.extend(names[:10])  # Limit to top 10
        
        # Extract dates
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'
        dates = re.findall(date_pattern, text_content)
        entities.extend(dates)
        
        # Extract numbers/amounts (more flexible pattern)
        number_pattern = r'\$\d+(?:[.,]\d+)*|\b\d+[.,]\d+|\b\d+\s*(?:percent|%|million|billion|thousand|euros?)\b'
        numbers = re.findall(number_pattern, text_content, re.IGNORECASE)
        entities.extend(numbers)
        
        return list(set(entities))  # Remove duplicates
    
    def _analyze_sentiment(self, text_content: str) -> str:
        """Analyze sentiment using simple keyword-based approach."""
        positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'benefit', 'advantage', 'improve', 'better', 'best', 'effective', 'efficient', 'valuable', 'important', 'significant']
        negative_words = ['bad', 'poor', 'negative', 'problem', 'issue', 'concern', 'disadvantage', 'worse', 'worst', 'ineffective', 'inefficient', 'difficult', 'challenge', 'risk']
        
        words = text_content.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        if positive_count > negative_count * 1.2:
            return 'positive'
        elif negative_count > positive_count * 1.2:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_readability(self, text_content: str) -> Dict[str, float]:
        """Calculate readability metrics."""
        sentences = [s for s in text_content.split('.') if s.strip()]
        words = text_content.split()
        
        if not sentences or not words:
            return {'flesch_score': 0.0, 'grade_level': 0.0}
        
        # Simple readability approximation
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Simplified Flesch Reading Ease approximation
        flesch_score = max(0, 206.835 - (1.015 * avg_sentence_length) - (84.6 * (avg_word_length / 4.7)))
        
        # Approximate grade level
        grade_level = max(1, (0.39 * avg_sentence_length) + (11.8 * (avg_word_length / 4.7)) - 15.59)
        
        return {
            'flesch_score': round(flesch_score, 2),
            'grade_level': round(grade_level, 2)
        }
    
    def _detect_language(self, text_content: str) -> str:
        """Detect document language using simple heuristics."""
        # Simple language detection based on common words
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        spanish_words = ['el', 'la', 'y', 'o', 'pero', 'en', 'de', 'con', 'por', 'para']
        french_words = ['le', 'la', 'et', 'ou', 'mais', 'dans', 'de', 'avec', 'par', 'pour']
        
        words = text_content.lower().split()
        
        english_count = sum(1 for word in words if word in english_words)
        spanish_count = sum(1 for word in words if word in spanish_words)
        french_count = sum(1 for word in words if word in french_words)
        
        if english_count > spanish_count and english_count > french_count:
            return 'english'
        elif spanish_count > french_count:
            return 'spanish'
        elif french_count > 0:
            return 'french'
        else:
            return 'unknown'
    
    def _classify_document(self, text_content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify document based on content and metadata.
        
        Args:
            text_content: Document text content
            metadata: Document metadata
            
        Returns:
            Classification results
        """
        classification = {
            'primary_category': 'general',
            'secondary_categories': [],
            'confidence': 0.0,
            'document_type': 'text',
            'subject_area': 'general',
            'generated_at': datetime.now().isoformat()
        }
        
        # Analyze content for classification clues
        content_lower = text_content.lower()
        
        # Document type classification
        if any(word in content_lower for word in ['contract', 'agreement', 'terms', 'conditions', 'legal']):
            classification['primary_category'] = 'legal'
            classification['document_type'] = 'contract'
            classification['confidence'] = 0.8
        elif any(word in content_lower for word in ['financial', 'budget', 'revenue', 'profit', 'expense', 'accounting']):
            classification['primary_category'] = 'financial'
            classification['document_type'] = 'financial_report'
            classification['confidence'] = 0.7
        elif any(word in content_lower for word in ['research', 'study', 'analysis', 'methodology', 'results', 'conclusion']):
            classification['primary_category'] = 'academic'
            classification['document_type'] = 'research_paper'
            classification['confidence'] = 0.7
        elif any(word in content_lower for word in ['manual', 'instructions', 'guide', 'how to', 'procedure', 'steps']):
            classification['primary_category'] = 'technical'
            classification['document_type'] = 'manual'
            classification['confidence'] = 0.6
        elif any(word in content_lower for word in ['report', 'summary', 'overview', 'findings', 'recommendations']):
            classification['primary_category'] = 'business'
            classification['document_type'] = 'report'
            classification['confidence'] = 0.6
        
        # Subject area classification
        if any(word in content_lower for word in ['technology', 'software', 'computer', 'digital', 'internet']):
            classification['subject_area'] = 'technology'
        elif any(word in content_lower for word in ['medical', 'health', 'patient', 'treatment', 'diagnosis']):
            classification['subject_area'] = 'healthcare'
        elif any(word in content_lower for word in ['education', 'learning', 'student', 'teacher', 'curriculum']):
            classification['subject_area'] = 'education'
        elif any(word in content_lower for word in ['marketing', 'sales', 'customer', 'product', 'service']):
            classification['subject_area'] = 'marketing'
        
        # Use metadata for additional classification
        if metadata:
            title = metadata.get('title', '').lower()
            author = metadata.get('author', '').lower()
            
            if 'invoice' in title or 'bill' in title:
                classification['primary_category'] = 'financial'
                classification['document_type'] = 'invoice'
                classification['confidence'] = 0.9
            elif 'resume' in title or 'cv' in title:
                classification['primary_category'] = 'personal'
                classification['document_type'] = 'resume'
                classification['confidence'] = 0.9
        
        return classification
    
    def _answer_question(self, text_content: str, question: str) -> str:
        """
        Answer question based on document content.
        
        Args:
            text_content: Document text content
            question: Question to answer
            
        Returns:
            Answer to the question
        """
        try:
            # Try AI service first if available
            if self.ai_api_key:
                return self._ai_answer_question(text_content, question)
            else:
                # Fallback to simple keyword-based answering
                return self._keyword_answer_question(text_content, question)
        except Exception as e:
            self.logger.warning(f"AI question answering failed, using fallback: {str(e)}")
            return self._keyword_answer_question(text_content, question)
    
    def _ai_answer_question(self, text_content: str, question: str) -> str:
        """
        Answer question using AI service (placeholder for actual AI integration).
        
        Args:
            text_content: Document text content
            question: Question to answer
            
        Returns:
            AI-generated answer
        """
        # This is a placeholder for actual AI service integration
        # In a real implementation, this would call OpenAI, Anthropic, or other AI APIs
        
        prompt = f"""
        Based on the following document, please answer this question: {question}
        
        Document text:
        {text_content[:3000]}  # Limit text to avoid token limits
        
        If the answer is not found in the document, please say so.
        """
        
        # Placeholder response - in real implementation, this would be an API call
        return self._keyword_answer_question(text_content, question)
    
    def _keyword_answer_question(self, text_content: str, question: str) -> str:
        """
        Answer question using simple keyword matching.
        
        Args:
            text_content: Document text content
            question: Question to answer
            
        Returns:
            Keyword-based answer
        """
        # Extract keywords from question
        question_words = [word.lower().strip('?.,!') for word in question.split() if len(word) > 3]
        
        # Split document into sentences
        sentences = [s.strip() for s in text_content.split('.') if s.strip()]
        
        # Score sentences based on keyword matches
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            score = 0
            
            for word in question_words:
                if word in sentence_lower:
                    score += 1
            
            if score > 0:
                sentence_scores[i] = score
        
        if not sentence_scores:
            return "I couldn't find information related to your question in the document."
        
        # Get the best matching sentences
        best_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Build answer from top sentences
        answer_parts = []
        for sentence_idx, score in best_sentences:
            answer_parts.append(sentences[sentence_idx])
        
        answer = ' '.join(answer_parts)
        
        if len(answer) > 500:
            answer = answer[:500] + "..."
        
        return answer
    
    def translate_content(self, pdf_path: str, target_language: str, preserve_formatting: bool = True) -> OperationResult:
        """
        Translate PDF content while preserving formatting.
        
        Args:
            pdf_path: Path to the PDF file
            target_language: Target language for translation
            preserve_formatting: Whether to preserve original formatting
            
        Returns:
            OperationResult with translated content
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            if not os.path.exists(pdf_path):
                raise FileOperationError(f"PDF file not found: {pdf_path}")
            
            if not target_language.strip():
                raise ValidationError("Target language cannot be empty")
            
            self.logger.info(f"Starting content translation for {pdf_path} to {target_language}")
            
            # Extract text content
            text_result = self.content_extractor.extract_text(pdf_path, preserve_layout=preserve_formatting)
            if not text_result.success:
                raise AIServiceError(f"Failed to extract text: {text_result.message}")
            
            # Read extracted text
            text_content = ""
            if text_result.output_files:
                with open(text_result.output_files[0], 'r', encoding='utf-8') as f:
                    text_content = f.read()
            
            if not text_content.strip():
                return OperationResult(
                    success=False,
                    message="No text content found for translation",
                    output_files=[],
                    execution_time=time.time() - start_time,
                    warnings=["Document appears to be empty or image-based"],
                    errors=["No extractable text content"]
                )
            
            # Check cache first
            cache_key = self._generate_cache_key(pdf_path, f"translate_{target_language}_{preserve_formatting}")
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.logger.info("Using cached translation result")
                return cached_result
            
            # Perform translation
            translated_content = self._translate_text(text_content, target_language, preserve_formatting)
            
            # Save translated content to file
            output_file = self._save_translation(pdf_path, translated_content, target_language)
            
            # Create result
            result = OperationResult(
                success=True,
                message=f"Content translated to {target_language} successfully",
                output_files=[output_file],
                execution_time=time.time() - start_time,
                warnings=[],
                errors=[]
            )
            
            # Cache result
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            error_msg = f"Content translation failed: {str(e)}"
            self.logger.error(error_msg)
            return OperationResult(
                success=False,
                message=error_msg,
                output_files=[],
                execution_time=time.time() - start_time,
                warnings=[],
                errors=[str(e)]
            )
    
    def interactive_chat(self, pdf_path: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Start an interactive chat session about the PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            conversation_history: Previous conversation messages
            
        Returns:
            Dictionary with chat session information
        """
        try:
            if not os.path.exists(pdf_path):
                raise FileOperationError(f"PDF file not found: {pdf_path}")
            
            # Initialize conversation history if not provided
            if conversation_history is None:
                conversation_history = []
            
            # Extract document content for context
            text_result = self.content_extractor.extract_text(pdf_path, preserve_layout=False)
            if not text_result.success:
                raise AIServiceError(f"Failed to extract text: {text_result.message}")
            
            # Read extracted text
            document_context = ""
            if text_result.output_files:
                with open(text_result.output_files[0], 'r', encoding='utf-8') as f:
                    document_context = f.read()
            
            # Create chat session
            chat_session = {
                'pdf_path': pdf_path,
                'document_context': document_context[:2000],  # Limit context size
                'conversation_history': conversation_history,
                'session_id': hashlib.md5(f"{pdf_path}_{datetime.now().isoformat()}".encode()).hexdigest(),
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            return chat_session
            
        except Exception as e:
            self.logger.error(f"Failed to start interactive chat: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'created_at': datetime.now().isoformat()
            }
    
    def continue_chat(self, session_id: str, user_message: str, chat_context: Dict[str, Any]) -> OperationResult:
        """
        Continue an interactive chat conversation.
        
        Args:
            session_id: Chat session identifier
            user_message: User's message/question
            chat_context: Chat session context
            
        Returns:
            OperationResult with AI response
        """
        start_time = time.time()
        
        try:
            if not user_message.strip():
                raise ValidationError("User message cannot be empty")
            
            if not chat_context or chat_context.get('status') != 'active':
                raise ValidationError("Invalid or inactive chat session")
            
            self.logger.info(f"Processing chat message for session {session_id}")
            
            # Get document context
            document_context = chat_context.get('document_context', '')
            conversation_history = chat_context.get('conversation_history', [])
            
            # Generate response using document context and conversation history
            response = self._generate_chat_response(user_message, document_context, conversation_history)
            
            # Update conversation history
            conversation_history.append({
                'role': 'user',
                'message': user_message,
                'timestamp': datetime.now().isoformat()
            })
            conversation_history.append({
                'role': 'assistant',
                'message': response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Save conversation to file
            output_file = self._save_chat_conversation(session_id, conversation_history)
            
            # Create result
            result = OperationResult(
                success=True,
                message=response,
                output_files=[output_file],
                execution_time=time.time() - start_time,
                warnings=[],
                errors=[]
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Chat conversation failed: {str(e)}"
            self.logger.error(error_msg)
            return OperationResult(
                success=False,
                message=error_msg,
                output_files=[],
                execution_time=time.time() - start_time,
                warnings=[],
                errors=[str(e)]
            )
    
    def _translate_text(self, text_content: str, target_language: str, preserve_formatting: bool) -> str:
        """
        Translate text content to target language.
        
        Args:
            text_content: Text to translate
            target_language: Target language
            preserve_formatting: Whether to preserve formatting
            
        Returns:
            Translated text
        """
        try:
            # Try AI service first if available
            if self.ai_api_key:
                return self._ai_translate(text_content, target_language, preserve_formatting)
            else:
                # Fallback to simple translation mapping
                return self._simple_translate(text_content, target_language, preserve_formatting)
        except Exception as e:
            self.logger.warning(f"AI translation failed, using fallback: {str(e)}")
            return self._simple_translate(text_content, target_language, preserve_formatting)
    
    def _ai_translate(self, text_content: str, target_language: str, preserve_formatting: bool) -> str:
        """
        Translate text using AI service (placeholder for actual AI integration).
        
        Args:
            text_content: Text to translate
            target_language: Target language
            preserve_formatting: Whether to preserve formatting
            
        Returns:
            AI-translated text
        """
        # This is a placeholder for actual AI service integration
        # In a real implementation, this would call translation APIs like Google Translate, DeepL, etc.
        
        formatting_instruction = "while preserving the original formatting, structure, and layout" if preserve_formatting else ""
        
        prompt = f"""
        Please translate the following text to {target_language} {formatting_instruction}.
        Maintain any special characters, line breaks, and document structure.
        
        Text to translate:
        {text_content[:3000]}  # Limit text to avoid token limits
        """
        
        # Placeholder response - in real implementation, this would be an API call
        return self._simple_translate(text_content, target_language, preserve_formatting)
    
    def _simple_translate(self, text_content: str, target_language: str, preserve_formatting: bool) -> str:
        """
        Simple translation fallback using basic word mapping.
        
        Args:
            text_content: Text to translate
            target_language: Target language
            preserve_formatting: Whether to preserve formatting
            
        Returns:
            Translated text (basic fallback)
        """
        # Basic translation mappings for common words
        translation_maps = {
            'spanish': {
                'hello': 'hola',
                'goodbye': 'adiós',
                'thank you': 'gracias',
                'please': 'por favor',
                'yes': 'sí',
                'no': 'no',
                'document': 'documento',
                'page': 'página',
                'text': 'texto',
                'content': 'contenido',
                'information': 'información',
                'data': 'datos',
                'report': 'informe',
                'analysis': 'análisis',
                'summary': 'resumen',
                'conclusion': 'conclusión'
            },
            'french': {
                'hello': 'bonjour',
                'goodbye': 'au revoir',
                'thank you': 'merci',
                'please': 's\'il vous plaît',
                'yes': 'oui',
                'no': 'non',
                'document': 'document',
                'page': 'page',
                'text': 'texte',
                'content': 'contenu',
                'information': 'information',
                'data': 'données',
                'report': 'rapport',
                'analysis': 'analyse',
                'summary': 'résumé',
                'conclusion': 'conclusion'
            },
            'german': {
                'hello': 'hallo',
                'goodbye': 'auf wiedersehen',
                'thank you': 'danke',
                'please': 'bitte',
                'yes': 'ja',
                'no': 'nein',
                'document': 'dokument',
                'page': 'seite',
                'text': 'text',
                'content': 'inhalt',
                'information': 'information',
                'data': 'daten',
                'report': 'bericht',
                'analysis': 'analyse',
                'summary': 'zusammenfassung',
                'conclusion': 'schlussfolgerung'
            }
        }
        
        target_lang_lower = target_language.lower()
        if target_lang_lower not in translation_maps:
            # If language not supported, return original with note
            return f"[Translation to {target_language} not available in offline mode]\n\n{text_content}"
        
        translation_map = translation_maps[target_lang_lower]
        translated_text = text_content.lower()
        
        # Apply basic word replacements
        for english_word, translated_word in translation_map.items():
            translated_text = translated_text.replace(english_word, translated_word)
        
        # Preserve formatting if requested
        if preserve_formatting:
            # Keep original line breaks and structure
            lines = text_content.split('\n')
            translated_lines = translated_text.split('\n')
            
            # Ensure we have the same number of lines
            if len(translated_lines) != len(lines):
                translated_lines = lines  # Fallback to original structure
            
            translated_text = '\n'.join(translated_lines)
        
        return f"[Basic translation to {target_language}]\n\n{translated_text}"
    
    def _generate_chat_response(self, user_message: str, document_context: str, conversation_history: List[Dict[str, str]]) -> str:
        """
        Generate response for interactive chat.
        
        Args:
            user_message: User's message
            document_context: Document content for context
            conversation_history: Previous conversation
            
        Returns:
            AI response
        """
        try:
            # Try AI service first if available
            if self.ai_api_key:
                return self._ai_chat_response(user_message, document_context, conversation_history)
            else:
                # Fallback to enhanced keyword-based response
                return self._enhanced_keyword_response(user_message, document_context, conversation_history)
        except Exception as e:
            self.logger.warning(f"AI chat response failed, using fallback: {str(e)}")
            return self._enhanced_keyword_response(user_message, document_context, conversation_history)
    
    def _ai_chat_response(self, user_message: str, document_context: str, conversation_history: List[Dict[str, str]]) -> str:
        """
        Generate chat response using AI service (placeholder for actual AI integration).
        
        Args:
            user_message: User's message
            document_context: Document content
            conversation_history: Previous conversation
            
        Returns:
            AI-generated response
        """
        # This is a placeholder for actual AI service integration
        # In a real implementation, this would call OpenAI, Anthropic, or other conversational AI APIs
        
        # Build conversation context
        context_messages = []
        for msg in conversation_history[-5:]:  # Last 5 messages for context
            context_messages.append(f"{msg['role']}: {msg['message']}")
        
        conversation_context = "\n".join(context_messages)
        
        prompt = f"""
        You are an AI assistant helping users understand and analyze a PDF document.
        
        Document context:
        {document_context[:1500]}
        
        Recent conversation:
        {conversation_context}
        
        User's current question: {user_message}
        
        Please provide a helpful, accurate response based on the document content and conversation context.
        """
        
        # Placeholder response - in real implementation, this would be an API call
        return self._enhanced_keyword_response(user_message, document_context, conversation_history)
    
    def _enhanced_keyword_response(self, user_message: str, document_context: str, conversation_history: List[Dict[str, str]]) -> str:
        """
        Generate enhanced keyword-based response for chat.
        
        Args:
            user_message: User's message
            document_context: Document content
            conversation_history: Previous conversation
            
        Returns:
            Enhanced response
        """
        user_message_lower = user_message.lower()
        
        # Check for summary requests first (higher priority)
        summary_keywords = ['summary', 'summarize', 'overview', 'main points', 'key points']
        if any(keyword in user_message_lower for keyword in summary_keywords):
            # Generate a quick summary from document context
            sentences = [s.strip() for s in document_context.split('.') if s.strip()][:3]
            summary = '. '.join(sentences) + '.'
            return f"Here's a brief summary of the document:\n\n{summary}\n\nWould you like me to elaborate on any specific aspect?"
        
        # Check for greeting patterns (only if not a summary request)
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
        if any(greeting in user_message_lower for greeting in greetings) and not any(keyword in user_message_lower for keyword in summary_keywords):
            return "Hello! I'm here to help you understand and analyze this PDF document. What would you like to know about it?"
        
        # Check for specific questions
        question_words = ['what', 'when', 'where', 'who', 'why', 'how']
        if any(word in user_message.lower() for word in question_words):
            # Use existing question-answering logic
            answer = self._keyword_answer_question(document_context, user_message)
            if "couldn't find information" not in answer:
                return answer
        
        # Check for help requests
        help_keywords = ['help', 'assist', 'support', 'guide']
        if any(keyword in user_message.lower() for keyword in help_keywords):
            return """I can help you with various tasks related to this PDF document:

• Ask questions about the content
• Request summaries or explanations
• Find specific information
• Analyze key topics and themes
• Translate content to other languages

What would you like to explore?"""
        
        # Default response with document-based suggestions
        return f"""I understand you're asking about: "{user_message}"

Based on the document content, I can help you with:
• Specific questions about the content
• Summaries and key points
• Finding particular information
• Content analysis

Could you please be more specific about what you'd like to know?"""
    
    def _save_translation(self, pdf_path: str, translated_content: str, target_language: str) -> str:
        """Save translated content to file."""
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_file = f"temp/{base_name}_translated_{target_language}.txt"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Translated Content ({target_language})\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source: {pdf_path}\n")
            f.write(f"{'='*50}\n\n")
            f.write(translated_content)
        
        return output_file
    
    def _save_chat_conversation(self, session_id: str, conversation_history: List[Dict[str, str]]) -> str:
        """Save chat conversation to file."""
        output_file = f"temp/chat_session_{session_id}.json"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        chat_data = {
            'session_id': session_id,
            'conversation_history': conversation_history,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)
        
        return output_file
    
    def _generate_cache_key(self, pdf_path: str, operation: str) -> str:
        """Generate cache key for operation."""
        # Use file path, modification time, and operation to create unique key
        try:
            mtime = os.path.getmtime(pdf_path)
            key_string = f"{pdf_path}_{mtime}_{operation}"
            return hashlib.md5(key_string.encode()).hexdigest()
        except:
            # Fallback to simple hash
            key_string = f"{pdf_path}_{operation}"
            return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[OperationResult]:
        """Get cached result if available."""
        if not self.enable_cache:
            return None
        
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check if cache is still valid (24 hours)
                cached_time = datetime.fromisoformat(data.get('cached_at', ''))
                if (datetime.now() - cached_time).total_seconds() < 86400:  # 24 hours
                    return OperationResult(**data['result'])
        except Exception as e:
            self.logger.warning(f"Failed to load cached result: {str(e)}")
        
        return None
    
    def _cache_result(self, cache_key: str, result: OperationResult) -> None:
        """Cache operation result."""
        if not self.enable_cache:
            return
        
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            cache_data = {
                'cached_at': datetime.now().isoformat(),
                'result': {
                    'success': result.success,
                    'message': result.message,
                    'output_files': result.output_files,
                    'execution_time': result.execution_time,
                    'warnings': result.warnings,
                    'errors': result.errors
                }
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to cache result: {str(e)}")
    
    def _save_summary(self, pdf_path: str, summary: str) -> str:
        """Save summary to file."""
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_file = f"temp/{base_name}_summary.txt"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Document Summary\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source: {pdf_path}\n")
            f.write(f"{'='*50}\n\n")
            f.write(summary)
        
        return output_file
    
    def _save_analysis(self, pdf_path: str, analysis: Dict[str, Any]) -> str:
        """Save content analysis to file."""
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_file = f"temp/{base_name}_analysis.json"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        return output_file
    
    def _save_classification(self, pdf_path: str, classification: Dict[str, Any]) -> str:
        """Save document classification to file."""
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_file = f"temp/{base_name}_classification.json"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(classification, f, indent=2, ensure_ascii=False)
        
        return output_file
    
    def _save_qa(self, pdf_path: str, question: str, answer: str) -> str:
        """Save question and answer to file."""
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"temp/{base_name}_qa_{timestamp}.txt"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Question & Answer\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source: {pdf_path}\n")
            f.write(f"{'='*50}\n\n")
            f.write(f"Question: {question}\n\n")
            f.write(f"Answer: {answer}\n")
        
        return output_file