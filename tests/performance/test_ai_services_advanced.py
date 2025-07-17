"""
Advanced integration tests for AI Services module.
"""

import unittest
import tempfile
import os
import json
import shutil
from unittest.mock import Mock

from smart_pdf_toolkit.core.ai_services import AIServices


class TestAIServicesAdvanced(unittest.TestCase):
    """Advanced test cases for AIServices integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'ai_api_key': 'test_key',
            'cache_dir': os.path.join(self.temp_dir, 'cache'),
            'enable_cache': True,
            'model_name': 'gpt-3.5-turbo',
            'max_tokens': 1000,
            'temperature': 0.7
        }
        
        # Create sample PDF files for testing
        self.legal_pdf = os.path.join(self.temp_dir, 'legal_contract.pdf')
        with open(self.legal_pdf, 'w') as f:
            f.write('dummy legal pdf')
        
        self.legal_text = """
        EMPLOYMENT AGREEMENT
        
        This Employment Agreement ("Agreement") is entered into on January 1, 2024, 
        between ABC Corporation ("Company") and John Smith ("Employee").
        
        TERMS AND CONDITIONS:
        1. Position: The Employee shall serve as Senior Software Engineer.
        2. Compensation: The Employee shall receive an annual salary of $120,000.
        3. Benefits: The Employee is entitled to health insurance and 401(k) matching.
        4. Termination: Either party may terminate this agreement with 30 days notice.
        
        This agreement shall be governed by the laws of California.
        """
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_comprehensive_document_analysis_workflow(self):
        """Test complete document analysis workflow."""
        # Mock content extractor
        mock_extractor = Mock()
        
        # Create text file for legal document
        legal_text_file = os.path.join(self.temp_dir, 'legal_text.txt')
        with open(legal_text_file, 'w', encoding='utf-8') as f:
            f.write(self.legal_text)
        
        # Mock extraction results
        mock_text_result = Mock()
        mock_text_result.success = True
        mock_text_result.output_files = [legal_text_file]
        
        mock_metadata_result = Mock()
        mock_metadata_result.success = True
        mock_metadata_result.output_files = []
        
        mock_extractor.extract_text.return_value = mock_text_result
        mock_extractor.extract_metadata.return_value = mock_metadata_result
        
        # Create AI services with mocked extractor
        ai_services = AIServices(self.config, content_extractor=mock_extractor)
        
        # Test complete workflow: summarize, analyze, classify, and Q&A
        
        # 1. Summarize document
        summary_result = ai_services.summarize_document(self.legal_pdf, 100)
        self.assertTrue(summary_result.success)
        self.assertGreater(len(summary_result.output_files), 0)
        
        # 2. Analyze content
        analysis_result = ai_services.analyze_content(self.legal_pdf)
        self.assertTrue(analysis_result.success)
        
        # Verify analysis content
        with open(analysis_result.output_files[0], 'r', encoding='utf-8') as f:
            analysis = json.load(f)
        
        self.assertIn('word_count', analysis)
        self.assertIn('topics', analysis)
        self.assertIn('sentiment', analysis)
        self.assertGreater(analysis['word_count'], 0)
        
        # 3. Classify document
        classification_result = ai_services.classify_document(self.legal_pdf)
        self.assertTrue(classification_result.success)
        
        # Verify classification
        with open(classification_result.output_files[0], 'r', encoding='utf-8') as f:
            classification = json.load(f)
        
        self.assertEqual(classification['primary_category'], 'legal')
        self.assertIn('contract', classification['document_type'])
        
        # 4. Answer questions
        qa_result = ai_services.answer_question(
            self.legal_pdf, 
            "What is the annual salary mentioned in the contract?"
        )
        self.assertTrue(qa_result.success)
        
        # Verify answer contains salary information
        with open(qa_result.output_files[0], 'r', encoding='utf-8') as f:
            qa_content = f.read()
        
        self.assertIn("120,000", qa_content)
    
    def test_multilingual_content_analysis(self):
        """Test analysis of multilingual content."""
        ai_services = AIServices(self.config)
        
        # Test Spanish content
        spanish_text = """
        CONTRATO DE TRABAJO
        
        Este contrato de trabajo se celebra entre la empresa ABC y el empleado Juan Pérez.
        El salario anual será de 50,000 euros. El empleado trabajará en el departamento
        de tecnología y tendrá derecho a vacaciones pagadas.
        """
        
        # Test language detection
        detected_language = ai_services._detect_language(spanish_text)
        self.assertEqual(detected_language, 'spanish')
        
        # Test content analysis with Spanish text
        analysis = ai_services._analyze_content(spanish_text)
        
        self.assertIn('word_count', analysis)
        self.assertIn('language', analysis)
        self.assertEqual(analysis['language'], 'spanish')
        
        # Test entity extraction from Spanish text
        entities = ai_services._extract_entities(spanish_text)
        # Should find some entities (names, numbers, etc.)
        self.assertIsInstance(entities, list)
        # Check for numeric entities
        numeric_entities = [e for e in entities if '50,000' in e or '50000' in e]
        self.assertGreater(len(numeric_entities), 0)
    
    def test_large_document_handling(self):
        """Test handling of large documents."""
        ai_services = AIServices(self.config)
        
        # Create a large text content
        large_text = "This is a sentence. " * 1000  # 1000 sentences
        
        # Test extractive summarization with large text
        summary = ai_services._extractive_summarize(large_text, 100)
        
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)
        self.assertLess(len(summary.split()), 150)  # Should be within reasonable bounds
        
        # Test content analysis with large text
        analysis = ai_services._analyze_content(large_text)
        
        self.assertEqual(analysis['word_count'], len(large_text.split()))
        self.assertGreater(analysis['sentence_count'], 900)  # Should count most sentences
    
    def test_edge_cases_and_boundary_conditions(self):
        """Test edge cases and boundary conditions."""
        ai_services = AIServices(self.config)
        
        # Test with very short text
        short_text = "Hi."
        summary = ai_services._extractive_summarize(short_text, 50)
        self.assertIn("Hi", summary)
        
        # Test with empty sentences
        empty_sentences_text = "... ... ..."
        summary = ai_services._extractive_summarize(empty_sentences_text, 50)
        self.assertIsInstance(summary, str)
        
        # Test topic extraction with no meaningful words
        meaningless_text = "a an the and or but in on at to for of with by"
        topics = ai_services._extract_topics(meaningless_text)
        self.assertEqual(len(topics), 0)  # Should find no meaningful topics
        
        # Test entity extraction with no entities
        no_entities_text = "this is just some text without any names or numbers"
        entities = ai_services._extract_entities(no_entities_text)
        # May find some capitalized words but should handle gracefully
        self.assertIsInstance(entities, list)
        
        # Test readability with single word
        single_word = "word"
        readability = ai_services._calculate_readability(single_word)
        self.assertIn('flesch_score', readability)
        self.assertIn('grade_level', readability)
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        # Test with content extraction failure
        mock_extractor = Mock()
        
        # Mock failed extraction
        mock_result = Mock()
        mock_result.success = False
        mock_result.message = "Extraction failed"
        mock_extractor.extract_text.return_value = mock_result
        
        ai_services = AIServices(self.config, content_extractor=mock_extractor)
        
        # Test that AI services handle extraction failure gracefully
        result = ai_services.summarize_document(self.legal_pdf, 50)
        self.assertFalse(result.success)
        self.assertIn("Failed to extract text", result.message)
        
        # Test with corrupted cache
        ai_services_with_cache = AIServices(self.config)
        cache_key = ai_services_with_cache._generate_cache_key(self.legal_pdf, "test")
        cache_file = os.path.join(ai_services_with_cache.cache_dir, f"{cache_key}.json")
        
        # Create corrupted cache file
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w') as f:
            f.write("invalid json content")
        
        # Should handle corrupted cache gracefully
        cached_result = ai_services_with_cache._get_cached_result(cache_key)
        self.assertIsNone(cached_result)
    
    def test_caching_functionality(self):
        """Test caching functionality."""
        ai_services = AIServices(self.config)
        
        # Test cache key generation
        cache_key = ai_services._generate_cache_key(self.legal_pdf, "test_operation")
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
        ai_services._cache_result(cache_key, test_result)
        
        # Retrieve from cache
        cached_result = ai_services._get_cached_result(cache_key)
        
        self.assertIsNotNone(cached_result)
        self.assertEqual(cached_result.success, test_result.success)
        self.assertEqual(cached_result.message, test_result.message)


if __name__ == '__main__':
    unittest.main()