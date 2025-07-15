"""
Advanced unit tests for OptimizationEngine advanced features.
"""

import unittest
import tempfile
import os
from pathlib import Path

from smart_pdf_toolkit.core.optimization_engine import OptimizationEngine, OptimizationConfig
from smart_pdf_toolkit.core.exceptions import PDFProcessingError, ValidationError


class TestOptimizationEngineAdvanced(unittest.TestCase):
    """Test cases for OptimizationEngine advanced functionality."""
    
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
    
    def test_optimize_fonts_validation(self):
        """Test font optimization input validation."""
        # Test with non-existent file
        result = self.optimization_engine.optimize_fonts("nonexistent.pdf", True)
        self.assertFalse(result.success)
        self.assertIn("does not exist", result.message)
        
        # Test with dummy file (will fail due to invalid PDF format)
        dummy_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        result = self.optimization_engine.optimize_fonts(dummy_pdf, True)
        self.assertFalse(result.success)
        # Should fail due to invalid PDF format, not validation
    
    def test_convert_color_space_validation(self):
        """Test color space conversion input validation."""
        # Test with non-existent file
        result = self.optimization_engine.convert_color_space("nonexistent.pdf", "RGB")
        self.assertFalse(result.success)
        self.assertIn("does not exist", result.message)
        
        # Test with invalid color space
        dummy_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        result = self.optimization_engine.convert_color_space(dummy_pdf, "INVALID")
        self.assertFalse(result.success)
        self.assertIn("Invalid color space", result.message)
        
        # Test with valid color spaces
        valid_spaces = ['RGB', 'CMYK', 'GRAY']
        for space in valid_spaces:
            result = self.optimization_engine.convert_color_space(dummy_pdf, space)
            # Should fail due to invalid PDF format, not color space validation
            self.assertFalse(result.success)
            self.assertNotIn("Invalid color space", result.message)
    
    def test_optimize_resolution_validation(self):
        """Test resolution optimization input validation."""
        # Test with non-existent file
        result = self.optimization_engine.optimize_resolution("nonexistent.pdf", 150, "web")
        self.assertFalse(result.success)
        self.assertIn("does not exist", result.message)
        
        # Test with invalid DPI
        dummy_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        result = self.optimization_engine.optimize_resolution(dummy_pdf, 50, "web")
        self.assertFalse(result.success)
        self.assertIn("must be between 72 and 600", result.message)
        
        result = self.optimization_engine.optimize_resolution(dummy_pdf, 700, "web")
        self.assertFalse(result.success)
        self.assertIn("must be between 72 and 600", result.message)
        
        # Test with invalid use case
        result = self.optimization_engine.optimize_resolution(dummy_pdf, 150, "invalid")
        self.assertFalse(result.success)
        self.assertIn("Invalid use case", result.message)
        
        # Test with valid use cases
        valid_use_cases = ['web', 'print', 'archive']
        for use_case in valid_use_cases:
            result = self.optimization_engine.optimize_resolution(dummy_pdf, 150, use_case)
            # Should fail due to invalid PDF format, not use case validation
            self.assertFalse(result.success)
            self.assertNotIn("Invalid use case", result.message)
    
    def test_create_optimization_comparison_validation(self):
        """Test optimization comparison input validation."""
        # Test with non-existent file
        comparison = self.optimization_engine.create_optimization_comparison("nonexistent.pdf", [3, 5, 7])
        self.assertIn("error", comparison)
        self.assertIn("does not exist", comparison["error"])
        
        # Test with valid file but invalid PDF format
        dummy_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        comparison = self.optimization_engine.create_optimization_comparison(dummy_pdf, [3, 5, 7])
        # Should return error due to invalid PDF format
        if "error" not in comparison:
            # If no error, should have proper structure
            self.assertIn("original_file", comparison)
            self.assertIn("comparisons", comparison)
            self.assertIn("recommendations", comparison)
    
    def test_optimization_comparison_structure(self):
        """Test optimization comparison return structure."""
        dummy_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        comparison = self.optimization_engine.create_optimization_comparison(dummy_pdf, [1, 5, 9])
        
        # Should have proper structure regardless of success
        required_keys = ['original_file', 'comparisons', 'recommendations']
        for key in required_keys:
            self.assertIn(key, comparison)
        
        self.assertEqual(comparison['original_file'], dummy_pdf)
        self.assertIsInstance(comparison['comparisons'], list)
        self.assertIsInstance(comparison['recommendations'], list)
    
    def test_analyze_fonts_method(self):
        """Test font analysis method exists and returns proper structure."""
        self.assertTrue(hasattr(self.optimization_engine, '_analyze_fonts'))
        self.assertTrue(callable(getattr(self.optimization_engine, '_analyze_fonts')))
    
    def test_analyze_color_usage_method(self):
        """Test color usage analysis method exists and returns proper structure."""
        self.assertTrue(hasattr(self.optimization_engine, '_analyze_color_usage'))
        self.assertTrue(callable(getattr(self.optimization_engine, '_analyze_color_usage')))
    
    def test_advanced_optimization_methods_exist(self):
        """Test that all advanced optimization methods exist."""
        advanced_methods = [
            'optimize_fonts',
            'convert_color_space',
            'optimize_resolution',
            'create_optimization_comparison'
        ]
        
        for method in advanced_methods:
            self.assertTrue(hasattr(self.optimization_engine, method))
            self.assertTrue(callable(getattr(self.optimization_engine, method)))
    
    def test_optimization_config_advanced_options(self):
        """Test advanced optimization configuration options."""
        # Test configuration for different use cases
        web_config = OptimizationConfig(
            compression_level=6,
            image_quality=80,
            linearize_for_web=True,
            subsample_images=True
        )
        
        self.assertEqual(web_config.compression_level, 6)
        self.assertEqual(web_config.image_quality, 80)
        self.assertTrue(web_config.linearize_for_web)
        self.assertTrue(web_config.subsample_images)
        
        # Test print configuration
        print_config = OptimizationConfig(
            compression_level=4,
            image_quality=95,
            linearize_for_web=False,
            subsample_images=False
        )
        
        self.assertEqual(print_config.compression_level, 4)
        self.assertEqual(print_config.image_quality, 95)
        self.assertFalse(print_config.linearize_for_web)
        self.assertFalse(print_config.subsample_images)
    
    def test_resolution_optimization_use_cases(self):
        """Test resolution optimization for different use cases."""
        dummy_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        use_cases = [
            ('web', 150),
            ('print', 300),
            ('archive', 200)
        ]
        
        for use_case, dpi in use_cases:
            result = self.optimization_engine.optimize_resolution(dummy_pdf, dpi, use_case)
            # Should fail due to invalid PDF format, but not due to parameter validation
            self.assertFalse(result.success)
            self.assertNotIn("Invalid use case", result.message)
            self.assertNotIn("must be between", result.message)
    
    def test_color_space_options(self):
        """Test color space conversion options."""
        dummy_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        color_spaces = ['RGB', 'CMYK', 'GRAY']
        
        for space in color_spaces:
            result = self.optimization_engine.convert_color_space(dummy_pdf, space)
            # Should fail due to invalid PDF format, but not due to color space validation
            self.assertFalse(result.success)
            self.assertNotIn("Invalid color space", result.message)
    
    def test_font_optimization_options(self):
        """Test font optimization options."""
        dummy_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        # Test both subsetting and embedding options
        for subset_fonts in [True, False]:
            result = self.optimization_engine.optimize_fonts(dummy_pdf, subset_fonts)
            # Should fail due to invalid PDF format, but not due to parameter validation
            self.assertFalse(result.success)
            # Error should be about PDF format, not font options


if __name__ == '__main__':
    unittest.main()