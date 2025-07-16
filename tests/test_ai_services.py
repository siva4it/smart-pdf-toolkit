"""
Unit tests for AI Services module.
"""

import unittest
import tempfile
import os
import json
import shutil
from unittest.mock import Mock, patch, MagicMock

from smart_pdf_toolkit.core.ai_services import AIServices
from smart_pdf_toolkit.core.exceptions import AIServiceError, ValidationError, FileOperationError


class TestAIServices(unittest.TestCase):
    """Test cases for AIServices class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'ai_api_key': 'test_key',
            'cache_dir': os.path.join(self.temp_dir, 'cache'),
            'enable_cache': True
        }
        self.ai_services = AIServices(self.config)
        
        # Create a sample PDF file path (we'll mock the actual PDF operations)
        self.sample_pdf = os.path.join(self.temp_dir, 'sample.pdf')
        with open(self.sample_pdf, 'w') as f:
            f.write('dummy pdf content')
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test AIServices initialization."""
        # Test with config
        ai_services = AIServices(self.config)
        self.assertEqual(ai_services.ai_api_key, 'test_key')
        self.assertTrue(ai_services.enable_cache)
        
        # Test without config
        ai_services_no_config = AIServices()
        self.assertIsNone(ai_services_no_config.ai_api_key)
        self.assertTrue(ai_services_no_config.enable_cache)  # Default
    
    def test_summarize_document_success(self):
        """Test successful document summarization."""
        # Mock content extractor
        mock_extractor = Mock()
        
        # Mock text extraction result
        text_file = os.path.join(self.temp_dir, 'extracted_text.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write("This is a sample document with multiple sentences. It contains important information about various topics. The document discusses key concepts and provides detailed analysis.")
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.output_files = [text_file]
        mock_extractor.extract_text.return_value = mock_result
        
        # Create AI services with mocked extractor
        ai_services = AIServices(self.config, content_extractor=mock_extractor)
        
        # Test summarization
        result = ai_services.summarize_document(self.sample_pdf, 50)
        
        self.assertTrue(result.success)
        self.assertIn("summarized successfully", result.message)
        self.assertEqual(len(result.output_files), 1)
        self.assertTrue(os.path.exists(result.output_files[0]))
        self.assertEqual(len(result.errors), 0)
    
    def test_summarize_document_no_text(self):
        """Test document summarization with no extractable text."""
        # Mock content extractor
        mock_extractor = Mock()
        
        # Mock empty text extraction result
        text_file = os.path.join(self.temp_dir, 'empty_text.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write("")
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.output_files = [text_file]
        mock_extractor.extract_text.return_value = mock_result
        
        # Create AI services with mocked extractor
        ai_services = AIServices(self.config, content_extractor=mock_extractor)
        
        # Test summarization
        result = ai_services.summarize_document(self.sample_pdf, 50)
        
        self.assertFalse(result.success)
        self.assertIn("No text content found", result.message)
        self.assertEqual(len(result.output_files), 0)
        self.assertGreater(len(result.errors), 0)
    
    def test_summarize_document_invalid_file(self):
        """Test document summarization with invalid file path."""
        result = self.ai_services.summarize_document("nonexistent.pdf", 50)
        
        self.assertFalse(result.success)
        self.assertIn("not found", result.message)
        self.assertEqual(len(result.output_files), 0)
        self.assertGreater(len(result.errors), 0)
    
    def test_summarize_document_invalid_length(self):
        """Test document summarization with invalid summary length."""
        result = self.ai_services.summarize_document(self.sample_pdf, -10)
        
        self.assertFalse(result.success)
        self.assertIn("must be positive", result.message)
        self.assertEqual(len(result.output_files), 0)
        self.assertGreater(len(result.errors), 0)
    
    def test_analyze_content_success(self):
        """Test successful content analysis."""
        # Mock content extractor
        mock_extractor = Mock()
        
        # Mock text extraction result
        text_file = os.path.join(self.temp_dir, 'extracted_text.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write("This is a comprehensive research document about artificial intelligence and machine learning technologies. The study examines various algorithms and their applications in modern software development.")
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.output_files = [text_file]
        mock_extractor.extract_text.return_value = mock_result
        
        # Create AI services with mocked extractor
        ai_services = AIServices(self.config, content_extractor=mock_extractor)
        
        # Test content analysis
        result = ai_services.analyze_content(self.sample_pdf)
        
        self.assertTrue(result.success)
        self.assertIn("analysis completed", result.message)
        self.assertEqual(len(result.output_files), 1)
        self.assertTrue(os.path.exists(result.output_files[0]))
        
        # Check analysis file content
        with open(result.output_files[0], 'r', encoding='utf-8') as f:
            analysis = json.load(f)
        
        self.assertIn('word_count', analysis)
        self.assertIn('topics', analysis)
        self.assertIn('sentiment', analysis)
        self.assertIn('readability', analysis)
        self.assertGreater(analysis['word_count'], 0)
    
    def test_classify_document_success(self):
        """Test successful document classification."""
        # Mock content extractor
        mock_extractor = Mock()
        
        # Mock text extraction result
        text_file = os.path.join(self.temp_dir, 'extracted_text.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write("This is a legal contract agreement between parties. The terms and conditions specify the obligations and rights of each party involved in this legal document.")
        
        # Mock metadata extraction result
        metadata_file = os.path.join(self.temp_dir, 'metadata.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump({'title': 'Contract Agreement', 'author': 'Legal Department'}, f)
        
        mock_text_result = Mock()
        mock_text_result.success = True
        mock_text_result.output_files = [text_file]
        
        mock_metadata_result = Mock()
        mock_metadata_result.success = True
        mock_metadata_result.output_files = [metadata_file]
        
        mock_extractor.extract_text.return_value = mock_text_result
        mock_extractor.extract_metadata.return_value = mock_metadata_result
        
        # Create AI services with mocked extractor
        ai_services = AIServices(self.config, content_extractor=mock_extractor)
        
        # Test classification
        result = ai_services.classify_document(self.sample_pdf)
        
        self.assertTrue(result.success)
        self.assertIn("classified as", result.message)
        self.assertEqual(len(result.output_files), 1)
        self.assertTrue(os.path.exists(result.output_files[0]))
        
        # Check classification file content
        with open(result.output_files[0], 'r', encoding='utf-8') as f:
            classification = json.load(f)
        
        self.assertIn('primary_category', classification)
        self.assertIn('document_type', classification)
        self.assertIn('confidence', classification)
        self.assertEqual(classification['primary_category'], 'legal')
    
    def test_answer_question_success(self):
        """Test successful question answering."""
        # Mock content extractor
        mock_extractor = Mock()
        
        # Mock text extraction result
        text_file = os.path.join(self.temp_dir, 'extracted_text.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write("The company was founded in 2020 by John Smith. The headquarters is located in New York. The main product is a software application for data analysis.")
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.output_files = [text_file]
        mock_extractor.extract_text.return_value = mock_result
        
        # Create AI services with mocked extractor
        ai_services = AIServices(self.config, content_extractor=mock_extractor)
        
        # Test question answering
        result = ai_services.answer_question(self.sample_pdf, "When was the company founded?")
        
        self.assertTrue(result.success)
        self.assertIn("answered successfully", result.message)
        self.assertEqual(len(result.output_files), 1)
        self.assertTrue(os.path.exists(result.output_files[0]))
        
        # Check Q&A file content
        with open(result.output_files[0], 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("When was the company founded?", content)
        self.assertIn("2020", content)  # Should find the answer in the text
    
    def test_answer_question_empty_question(self):
        """Test question answering with empty question."""
        result = self.ai_services.answer_question(self.sample_pdf, "")
        
        self.assertFalse(result.success)
        self.assertIn("cannot be empty", result.message)
        self.assertEqual(len(result.output_files), 0)
        self.assertGreater(len(result.errors), 0)
    
    def test_extractive_summarize(self):
        """Test extractive summarization method."""
        text = "This is the first sentence. This is the second sentence with important information. This is the third sentence. This is the fourth sentence with key details."
        
        summary = self.ai_services._extractive_summarize(text, 20)
        
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)
        self.assertTrue(summary.endswith('.'))
    
    def test_extract_topics(self):
        """Test topic extraction method."""
        text = "This document discusses artificial intelligence and machine learning algorithms. The research focuses on neural networks and deep learning applications."
        
        topics = self.ai_services._extract_topics(text)
        
        self.assertIsInstance(topics, list)
        self.assertIn('artificial', topics)
        self.assertIn('intelligence', topics)
        self.assertIn('machine', topics)
        self.assertIn('learning', topics)
    
    def test_extract_entities(self):
        """Test entity extraction method."""
        text = "John Smith founded the company in 2020. The revenue was $1.5 million in the first year. The meeting is scheduled for 12/25/2023."
        
        entities = self.ai_services._extract_entities(text)
        
        self.assertIsInstance(entities, list)
        # Should extract names, dates, and amounts
        self.assertTrue(any('John Smith' in entity for entity in entities))
        self.assertTrue(any('$1.5' in entity or '1.5' in entity for entity in entities))
        self.assertTrue(any('12/25/2023' in entity for entity in entities))
    
    def test_analyze_sentiment(self):
        """Test sentiment analysis method."""
        positive_text = "This is an excellent document with great insights and valuable information."
        negative_text = "This is a poor document with bad analysis and terrible conclusions."
        neutral_text = "This document contains information about various topics."
        
        positive_sentiment = self.ai_services._analyze_sentiment(positive_text)
        negative_sentiment = self.ai_services._analyze_sentiment(negative_text)
        neutral_sentiment = self.ai_services._analyze_sentiment(neutral_text)
        
        self.assertEqual(positive_sentiment, 'positive')
        self.assertEqual(negative_sentiment, 'negative')
        self.assertEqual(neutral_sentiment, 'neutral')
    
    def test_calculate_readability(self):
        """Test readability calculation method."""
        text = "This is a simple sentence. This is another simple sentence with more words."
        
        readability = self.ai_services._calculate_readability(text)
        
        self.assertIsInstance(readability, dict)
        self.assertIn('flesch_score', readability)
        self.assertIn('grade_level', readability)
        self.assertGreater(readability['flesch_score'], 0)
        self.assertGreater(readability['grade_level'], 0)
    
    def test_detect_language(self):
        """Test language detection method."""
        english_text = "This is an English document with the and or but in on at to for of with by."
        spanish_text = "Este es un documento en español con el la y o pero en de con por para."
        
        english_lang = self.ai_services._detect_language(english_text)
        spanish_lang = self.ai_services._detect_language(spanish_text)
        
        self.assertEqual(english_lang, 'english')
        self.assertEqual(spanish_lang, 'spanish')
    
    def test_classify_document_content(self):
        """Test document classification based on content."""
        legal_text = "This contract agreement specifies the terms and conditions between the parties."
        financial_text = "The financial report shows revenue of $1M and profit margins of 15%."
        
        legal_metadata = {'title': 'Contract Agreement'}
        financial_metadata = {'title': 'Financial Report'}
        
        legal_classification = self.ai_services._classify_document(legal_text, legal_metadata)
        financial_classification = self.ai_services._classify_document(financial_text, financial_metadata)
        
        self.assertEqual(legal_classification['primary_category'], 'legal')
        self.assertEqual(financial_classification['primary_category'], 'financial')
    
    def test_keyword_answer_question(self):
        """Test keyword-based question answering."""
        text = "The company was founded in 2020 by John Smith. The headquarters is located in New York City."
        question = "Where is the headquarters located?"
        
        answer = self.ai_services._keyword_answer_question(text, question)
        
        self.assertIsInstance(answer, str)
        self.assertIn("New York", answer)
    
    def test_keyword_answer_question_no_match(self):
        """Test keyword-based question answering with no matches."""
        text = "The company was founded in 2020 by John Smith."
        question = "What is the weather like today?"
        
        answer = self.ai_services._keyword_answer_question(text, question)
        
        self.assertIsInstance(answer, str)
        self.assertIn("couldn't find information", answer)
    
    def test_cache_functionality(self):
        """Test caching functionality."""
        # Test cache key generation
        cache_key = self.ai_services._generate_cache_key(self.sample_pdf, "test_operation")
        self.assertIsInstance(cache_key, str)
        self.assertEqual(len(cache_key), 32)  # MD5 hash length
        
        # Test cache storage and retrieval
        from smart_pdf_toolkit.core.interfaces import OperationResult
        test_result = OperationResult(
            success=True,
            message="Test result",
            output_files=["test.txt"],
            execution_time=1.0,
            warnings=[],
            errors=[]
        )
        
        # Cache the result
        self.ai_services._cache_result(cache_key, test_result)
        
        # Retrieve from cache
        cached_result = self.ai_services._get_cached_result(cache_key)
        
        self.assertIsNotNone(cached_result)
        self.assertEqual(cached_result.success, test_result.success)
        self.assertEqual(cached_result.message, test_result.message)
    
    def test_save_methods(self):
        """Test file saving methods."""
        # Test save summary
        summary = "This is a test summary."
        summary_file = self.ai_services._save_summary(self.sample_pdf, summary)
        self.assertTrue(os.path.exists(summary_file))
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn(summary, content)
        
        # Test save analysis
        analysis = {'word_count': 100, 'topics': ['test', 'analysis']}
        analysis_file = self.ai_services._save_analysis(self.sample_pdf, analysis)
        self.assertTrue(os.path.exists(analysis_file))
        
        with open(analysis_file, 'r', encoding='utf-8') as f:
            saved_analysis = json.load(f)
        self.assertEqual(saved_analysis['word_count'], 100)
        
        # Test save classification
        classification = {'primary_category': 'test', 'confidence': 0.8}
        classification_file = self.ai_services._save_classification(self.sample_pdf, classification)
        self.assertTrue(os.path.exists(classification_file))
        
        with open(classification_file, 'r', encoding='utf-8') as f:
            saved_classification = json.load(f)
        self.assertEqual(saved_classification['primary_category'], 'test')
        
        # Test save Q&A
        question = "What is this about?"
        answer = "This is about testing."
        qa_file = self.ai_services._save_qa(self.sample_pdf, question, answer)
        self.assertTrue(os.path.exists(qa_file))
        
        with open(qa_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn(question, content)
        self.assertIn(answer, content)


if __name__ == '__main__':
    unittest.main()