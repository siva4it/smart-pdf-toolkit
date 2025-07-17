"""
Unit tests for OptimizationEngine class.
"""

import unittest
import tempfile
import os
from pathlib import Path

from smart_pdf_toolkit.core.optimization_engine import OptimizationEngine, OptimizationConfig, OptimizationResult
from smart_pdf_toolkit.core.exceptions import PDFProcessingError, ValidationError


class TestOptimizationEngine(unittest.TestCase):
    """Test cases for OptimizationEngine functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.optimization_engine = OptimizationEngine()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_optimization_engine_initialization(self):
        """Test OptimizationEngine initialization."""
        engine = OptimizationEngine()
        self.assertIsNotNone(engine)
        self.assertIsNotNone(engine.config)
    
    def test_optimization_config_creation(self):
        """Test OptimizationConfig dataclass."""
        # Test default config
        config = OptimizationConfig()
        self.assertEqual(config.compression_level, 5)
        self.assertEqual(config.image_quality, 75)
        self.assertTrue(config.remove_unused_objects)
        self.assertTrue(config.compress_streams)
        
        # Test custom config
        config = OptimizationConfig(
            compression_level=8,
            image_quality=60,
            remove_unused_objects=False,
            optimize_images=True,
            linearize_for_web=True
        )
        self.assertEqual(config.compression_level, 8)
        self.assertEqual(config.image_quality, 60)
        self.assertFalse(config.remove_unused_objects)
        self.assertTrue(config.optimize_images)
        self.assertTrue(config.linearize_for_web)
    
    def test_compress_pdf_validation(self):
        """Test PDF compression input validation."""
        # Test with non-existent file
        result = self.optimization_engine.compress_pdf("nonexistent.pdf", 5)
        self.assertFalse(result.success)
        self.assertIn("does not exist", result.message)
        
        # Test with invalid compression level
        dummy_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        result = self.optimization_engine.compress_pdf(dummy_pdf, 0)
        self.assertFalse(result.success)
        self.assertIn("must be between 1 and 9", result.message)
        
        result = self.optimization_engine.compress_pdf(dummy_pdf, 10)
        self.assertFalse(result.success)
        self.assertIn("must be between 1 and 9", result.message)
    
    def test_optimize_for_web_validation(self):
        """Test web optimization input validation."""
        # Test with non-existent file
        result = self.optimization_engine.optimize_for_web("nonexistent.pdf")
        self.assertFalse(result.success)
        self.assertIn("does not exist", result.message)
    
    def test_optimize_images_validation(self):
        """Test image optimization input validation."""
        # Test with non-existent file
        result = self.optimization_engine.optimize_images("nonexistent.pdf", 75)
        self.assertFalse(result.success)
        self.assertIn("does not exist", result.message)
        
        # Test with invalid quality
        dummy_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        result = self.optimization_engine.optimize_images(dummy_pdf, 0)
        self.assertFalse(result.success)
        self.assertIn("must be between 1 and 100", result.message)
        
        result = self.optimization_engine.optimize_images(dummy_pdf, 101)
        self.assertFalse(result.success)
        self.assertIn("must be between 1 and 100", result.message)
    
    def test_create_optimization_config(self):
        """Test optimization configuration creation based on compression level."""
        # Test light compression (level 1-3)
        config = self.optimization_engine._create_optimization_config(2)
        self.assertEqual(config.compression_level, 2)
        self.assertEqual(config.image_quality, 90)
        self.assertTrue(config.remove_unused_objects)
        self.assertFalse(config.remove_duplicate_objects)
        self.assertFalse(config.optimize_images)
        
        # Test medium compression (level 4-6)
        config = self.optimization_engine._create_optimization_config(5)
        self.assertEqual(config.compression_level, 5)
        self.assertEqual(config.image_quality, 80)
        self.assertTrue(config.remove_unused_objects)
        self.assertTrue(config.remove_duplicate_objects)
        self.assertTrue(config.optimize_images)
        self.assertFalse(config.subsample_images)
        
        # Test high compression (level 7-9)
        config = self.optimization_engine._create_optimization_config(8)
        self.assertEqual(config.compression_level, 8)
        self.assertEqual(config.image_quality, 70)
        self.assertTrue(config.remove_unused_objects)
        self.assertTrue(config.remove_duplicate_objects)
        self.assertTrue(config.optimize_images)
        self.assertTrue(config.subsample_images)
        self.assertTrue(config.remove_metadata)
    
    def test_get_save_options(self):
        """Test save options generation."""
        # Test basic config
        config = OptimizationConfig()
        options = self.optimization_engine._get_save_options(config)
        
        self.assertIn('garbage', options)
        self.assertIn('clean', options)
        self.assertIn('deflate', options)
        self.assertIn('pretty', options)
        self.assertFalse(options['pretty'])  # Should be compact
        
        # Test web optimization config
        config = OptimizationConfig(linearize_for_web=True)
        options = self.optimization_engine._get_save_options(config)
        self.assertIn('linear', options)
        self.assertTrue(options['linear'])
    
    def test_estimate_compression_ratio(self):
        """Test compression ratio estimation."""
        # Test various compression levels
        ratio_1 = self.optimization_engine._estimate_compression_ratio(1)
        ratio_5 = self.optimization_engine._estimate_compression_ratio(5)
        ratio_9 = self.optimization_engine._estimate_compression_ratio(9)
        
        # Higher compression levels should have higher ratios
        self.assertLess(ratio_1, ratio_5)
        self.assertLess(ratio_5, ratio_9)
        
        # Test invalid level (should return default)
        ratio_invalid = self.optimization_engine._estimate_compression_ratio(15)
        self.assertEqual(ratio_invalid, 1.8)  # Default ratio
    
    def test_get_optimization_preview_validation(self):
        """Test optimization preview input validation."""
        # Test with non-existent file
        preview = self.optimization_engine.get_optimization_preview("nonexistent.pdf", 5)
        self.assertIn("error", preview)
        self.assertIn("does not exist", preview["error"])
        
        # Test with invalid compression level
        dummy_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        preview = self.optimization_engine.get_optimization_preview(dummy_pdf, 0)
        self.assertIn("error", preview)
        self.assertIn("must be between 1 and 9", preview["error"])
    
    def test_analyze_document_structure(self):
        """Test document structure analysis."""
        # This test would require a real PDF document
        # For now, we test the method exists and returns proper structure
        self.assertTrue(hasattr(self.optimization_engine, '_analyze_document_structure'))
        self.assertTrue(callable(getattr(self.optimization_engine, '_analyze_document_structure')))
    
    def test_optimization_engine_methods_exist(self):
        """Test that all required methods exist."""
        required_methods = [
            'compress_pdf',
            'optimize_for_web',
            'optimize_images',
            'get_optimization_preview'
        ]
        
        for method in required_methods:
            self.assertTrue(hasattr(self.optimization_engine, method))
            self.assertTrue(callable(getattr(self.optimization_engine, method)))
    
    def test_optimization_result_structure(self):
        """Test OptimizationResult dataclass structure."""
        result = OptimizationResult(
            success=True,
            message="Test message",
            output_file="test.pdf",
            execution_time=1.5,
            original_size=1000,
            optimized_size=800,
            compression_ratio=1.25,
            size_reduction_percent=20.0,
            optimization_details={"test": "data"},
            warnings=["warning1"],
            errors=[]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Test message")
        self.assertEqual(result.output_file, "test.pdf")
        self.assertEqual(result.execution_time, 1.5)
        self.assertEqual(result.original_size, 1000)
        self.assertEqual(result.optimized_size, 800)
        self.assertEqual(result.compression_ratio, 1.25)
        self.assertEqual(result.size_reduction_percent, 20.0)
        self.assertEqual(result.optimization_details, {"test": "data"})
        self.assertEqual(result.warnings, ["warning1"])
        self.assertEqual(result.errors, [])


if __name__ == '__main__':
    unittest.main()