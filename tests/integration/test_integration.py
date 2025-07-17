"""
Integration tests for core components.
"""

import unittest
import tempfile
import shutil
from smart_pdf_toolkit import (
    config_manager, ApplicationConfig, FileManager, 
    Validator, plugin_manager, setup_logging
)


class TestCoreIntegration(unittest.TestCase):
    """Integration tests for core components."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_config_and_logging_integration(self):
        """Test configuration and logging integration."""
        # Create custom config
        config = ApplicationConfig(
            temp_directory=self.temp_dir,
            log_level="DEBUG"
        )
        
        # Set up logging with config
        logger = setup_logging(config.log_level)
        
        self.assertIsNotNone(logger)
        self.assertEqual(logger.level, 10)  # DEBUG level
    
    def test_file_manager_with_config(self):
        """Test FileManager with configuration."""
        config = ApplicationConfig(temp_directory=self.temp_dir)
        
        with FileManager(config.temp_directory) as fm:
            temp_file = fm.create_temp_file(suffix=".pdf")
            self.assertTrue(temp_file.startswith(self.temp_dir))
            self.assertTrue(temp_file.endswith(".pdf"))
    
    def test_plugin_manager_initialization(self):
        """Test plugin manager initialization."""
        # Discover plugins (should not fail even with no plugins)
        discovered = plugin_manager.discover_plugins()
        self.assertIsInstance(discovered, list)
        
        # List available plugins
        available = plugin_manager.list_available_plugins()
        self.assertIsInstance(available, list)
        
        # List loaded plugins (should be empty initially)
        loaded = plugin_manager.list_loaded_plugins()
        self.assertEqual(len(loaded), 0)
    
    def test_validator_functionality(self):
        """Test validator functionality."""
        # Test compression level validation
        Validator.validate_compression_level(5)
        
        with self.assertRaises(Exception):
            Validator.validate_compression_level(15)
        
        # Test image format validation
        Validator.validate_image_format("png")
        
        with self.assertRaises(Exception):
            Validator.validate_image_format("invalid")


if __name__ == '__main__':
    unittest.main()