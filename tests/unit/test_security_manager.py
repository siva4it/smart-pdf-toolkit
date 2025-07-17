"""
Unit tests for SecurityManager class.
"""

import unittest
import tempfile
import os
from pathlib import Path

from smart_pdf_toolkit.core.security_manager import SecurityManager, PermissionSet, WatermarkConfig
from smart_pdf_toolkit.core.exceptions import SecurityError, ValidationError


class TestSecurityManager(unittest.TestCase):
    """Test cases for SecurityManager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.security_manager = SecurityManager()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_security_manager_initialization(self):
        """Test SecurityManager initialization."""
        manager = SecurityManager()
        self.assertIsNotNone(manager)
        self.assertIsNotNone(manager.config)
    
    def test_permission_set_creation(self):
        """Test PermissionSet dataclass."""
        # Test default permissions
        perm_set = PermissionSet()
        self.assertTrue(perm_set.print_document)
        self.assertTrue(perm_set.modify_document)
        self.assertTrue(perm_set.copy_content)
        
        # Test custom permissions
        perm_set = PermissionSet(
            print_document=False,
            modify_document=False,
            copy_content=True
        )
        self.assertFalse(perm_set.print_document)
        self.assertFalse(perm_set.modify_document)
        self.assertTrue(perm_set.copy_content)
    
    def test_watermark_config_creation(self):
        """Test WatermarkConfig dataclass."""
        # Test default config
        config = WatermarkConfig()
        self.assertIsNone(config.text)
        self.assertIsNone(config.image_path)
        self.assertEqual(config.opacity, 0.5)
        self.assertEqual(config.rotation, 45)
        
        # Test custom config
        config = WatermarkConfig(
            text="CONFIDENTIAL",
            opacity=0.3,
            rotation=30,
            position="top-right"
        )
        self.assertEqual(config.text, "CONFIDENTIAL")
        self.assertEqual(config.opacity, 0.3)
        self.assertEqual(config.rotation, 30)
        self.assertEqual(config.position, "top-right")
    
    def test_add_password_validation(self):
        """Test password addition input validation."""
        # Test with non-existent file
        result = self.security_manager.add_password("nonexistent.pdf", "password123")
        self.assertFalse(result.success)
        self.assertIn("does not exist", result.message)
        
        # Test with empty password
        # Create a dummy file for testing
        dummy_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        result = self.security_manager.add_password(dummy_pdf, "")
        self.assertFalse(result.success)
        self.assertIn("cannot be empty", result.message)
    
    def test_remove_password_validation(self):
        """Test password removal input validation."""
        # Test with non-existent file
        result = self.security_manager.remove_password("nonexistent.pdf", "password123")
        self.assertFalse(result.success)
        self.assertIn("does not exist", result.message)
        
        # Test with empty password
        dummy_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        result = self.security_manager.remove_password(dummy_pdf, "")
        self.assertFalse(result.success)
        self.assertIn("cannot be empty", result.message)
    
    def test_set_permissions_validation(self):
        """Test permission setting input validation."""
        # Test with non-existent file
        result = self.security_manager.set_permissions("nonexistent.pdf", {"print": False})
        self.assertFalse(result.success)
        self.assertIn("does not exist", result.message)
        
        # Test with empty permissions
        dummy_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        result = self.security_manager.set_permissions(dummy_pdf, {})
        self.assertFalse(result.success)
        self.assertIn("cannot be empty", result.message)
    
    def test_add_watermark_validation(self):
        """Test watermark addition input validation."""
        # Test with non-existent file
        result = self.security_manager.add_watermark("nonexistent.pdf", {"text": "DRAFT"})
        self.assertFalse(result.success)
        self.assertIn("does not exist", result.message)
        
        # Test with empty config
        dummy_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        result = self.security_manager.add_watermark(dummy_pdf, {})
        self.assertFalse(result.success)
        self.assertIn("cannot be empty", result.message)
        
        # Test with invalid config (no text or image)
        result = self.security_manager.add_watermark(dummy_pdf, {"opacity": 0.5})
        self.assertFalse(result.success)
        self.assertIn("text or image_path must be provided", result.message)
    
    def test_get_security_info_validation(self):
        """Test security info retrieval validation."""
        # Test with non-existent file
        info = self.security_manager.get_security_info("nonexistent.pdf")
        self.assertIn("error", info)
        self.assertIn("does not exist", info["error"])
    
    def test_security_manager_methods_exist(self):
        """Test that all required methods exist."""
        required_methods = [
            'add_password',
            'remove_password', 
            'set_permissions',
            'add_watermark',
            'get_security_info'
        ]
        
        for method in required_methods:
            self.assertTrue(hasattr(self.security_manager, method))
            self.assertTrue(callable(getattr(self.security_manager, method)))


if __name__ == '__main__':
    unittest.main()