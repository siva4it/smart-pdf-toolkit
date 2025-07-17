"""
Tests for configuration management.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from smart_pdf_toolkit.core.config import ConfigManager, ApplicationConfig, PluginConfig


class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_default_config_creation(self):
        """Test creation of default configuration."""
        config = self.config_manager.load_config()
        
        self.assertIsInstance(config, ApplicationConfig)
        self.assertEqual(config.compression_default, 5)
        self.assertEqual(config.batch_size_limit, 100)
        self.assertIn("eng", config.ocr_languages)
    
    def test_config_save_and_load(self):
        """Test saving and loading configuration."""
        # Create custom config
        custom_config = ApplicationConfig(
            temp_directory="/custom/temp",
            max_file_size=50 * 1024 * 1024,
            compression_default=7
        )
        
        # Save config
        self.config_manager.save_config(custom_config)
        
        # Load config
        loaded_config = self.config_manager.load_config()
        
        self.assertEqual(loaded_config.temp_directory, "/custom/temp")
        self.assertEqual(loaded_config.max_file_size, 50 * 1024 * 1024)
        self.assertEqual(loaded_config.compression_default, 7)
    
    def test_plugin_config_management(self):
        """Test plugin configuration management."""
        plugin_config = PluginConfig(
            name="test_plugin",
            enabled=True,
            settings={"setting1": "value1"}
        )
        
        # Set plugin config
        self.config_manager.set_plugin_config("test_plugin", plugin_config)
        
        # Get plugin config
        loaded_config = self.config_manager.get_plugin_config("test_plugin")
        
        self.assertIsNotNone(loaded_config)
        self.assertEqual(loaded_config.name, "test_plugin")
        self.assertTrue(loaded_config.enabled)
        self.assertEqual(loaded_config.settings["setting1"], "value1")


if __name__ == '__main__':
    unittest.main()