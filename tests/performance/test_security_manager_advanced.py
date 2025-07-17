"""
Advanced unit tests for SecurityManager digital signature and advanced features.
"""

import unittest
import tempfile
import os
from pathlib import Path

from smart_pdf_toolkit.core.security_manager import SecurityManager, CertificateInfo
from smart_pdf_toolkit.core.exceptions import SecurityError, ValidationError


class TestSecurityManagerAdvanced(unittest.TestCase):
    """Test cases for SecurityManager advanced functionality."""
    
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
    
    def test_certificate_info_creation(self):
        """Test CertificateInfo dataclass."""
        # Test default certificate info
        cert_info = CertificateInfo(common_name="Test User")
        self.assertEqual(cert_info.common_name, "Test User")
        self.assertEqual(cert_info.organization, "Smart PDF Toolkit")
        self.assertEqual(cert_info.country, "US")
        self.assertEqual(cert_info.validity_days, 365)
        
        # Test custom certificate info
        cert_info = CertificateInfo(
            common_name="John Doe",
            organization="Test Corp",
            country="CA",
            state="ON",
            locality="Toronto",
            email="john@test.com",
            validity_days=730
        )
        self.assertEqual(cert_info.common_name, "John Doe")
        self.assertEqual(cert_info.organization, "Test Corp")
        self.assertEqual(cert_info.country, "CA")
        self.assertEqual(cert_info.state, "ON")
        self.assertEqual(cert_info.locality, "Toronto")
        self.assertEqual(cert_info.email, "john@test.com")
        self.assertEqual(cert_info.validity_days, 730)
    
    def test_digital_signature_validation(self):
        """Test digital signature input validation."""
        # Test with non-existent file
        result = self.security_manager.add_digital_signature(
            "nonexistent.pdf", 
            {"common_name": "Test User"}
        )
        self.assertFalse(result.success)
        self.assertIn("does not exist", result.message)
        
        # Test with empty certificate info
        dummy_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        result = self.security_manager.add_digital_signature(dummy_pdf, {})
        self.assertFalse(result.success)
        self.assertIn("cannot be empty", result.message)
    
    def test_digital_signature_crypto_availability(self):
        """Test digital signature when cryptography library is not available."""
        # Mock CRYPTO_AVAILABLE to False
        original_crypto = self.security_manager.__class__.__module__
        
        # Create a dummy PDF file
        dummy_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        # Test should handle missing cryptography gracefully
        # (This test assumes cryptography is installed, so we test the validation path)
        result = self.security_manager.add_digital_signature(
            dummy_pdf,
            {"common_name": "Test User"}
        )
        
        # Should fail due to invalid PDF format, not crypto availability
        self.assertFalse(result.success)
    
    def test_signature_verification_validation(self):
        """Test signature verification input validation."""
        # Test with non-existent file
        info = self.security_manager.verify_digital_signature("nonexistent.pdf")
        self.assertIn("error", info)
        self.assertIn("does not exist", info["error"])
    
    def test_signature_verification_structure(self):
        """Test signature verification return structure."""
        # Create a dummy file
        dummy_pdf = os.path.join(self.temp_dir, "test.pdf")
        with open(dummy_pdf, 'w') as f:
            f.write("dummy content")
        
        info = self.security_manager.verify_digital_signature(dummy_pdf)
        
        # Should return error due to invalid PDF, but structure should be correct
        if "error" in info:
            self.assertIn("has_signature", info)
            self.assertIn("signature_valid", info)
        else:
            # If no error, should have proper structure
            required_keys = [
                'has_signature', 'signature_valid', 'signer_info', 
                'signature_date', 'verification_details'
            ]
            for key in required_keys:
                self.assertIn(key, info)
    
    def test_advanced_security_methods_exist(self):
        """Test that all advanced security methods exist."""
        advanced_methods = [
            'add_digital_signature',
            'verify_digital_signature',
            '_generate_self_signed_certificate'
        ]
        
        for method in advanced_methods:
            self.assertTrue(hasattr(self.security_manager, method))
            if not method.startswith('_'):  # Skip private methods for callable test
                self.assertTrue(callable(getattr(self.security_manager, method)))
    
    def test_watermark_advanced_positions(self):
        """Test watermark positioning options."""
        positions = ["center", "top-left", "top-right", "bottom-left", "bottom-right"]
        
        for position in positions:
            watermark_config = {
                "text": "TEST",
                "position": position,
                "opacity": 0.5,
                "rotation": 45,
                "font_size": 24,
                "color": "red"
            }
            
            # Test that configuration is accepted (validation will fail due to dummy file)
            dummy_pdf = os.path.join(self.temp_dir, f"test_{position}.pdf")
            with open(dummy_pdf, 'w') as f:
                f.write("dummy content")
            
            result = self.security_manager.add_watermark(dummy_pdf, watermark_config)
            # Should fail due to invalid PDF format, but not due to position validation
            self.assertFalse(result.success)
            self.assertNotIn("position", result.message.lower())
    
    def test_permission_combinations(self):
        """Test various permission combinations."""
        permission_sets = [
            {"print": False, "modify": False, "copy": False},
            {"print": True, "modify": False, "copy": True, "annotate": False},
            {"print": True, "modify": True, "copy": True, "annotate": True, "form": True},
        ]
        
        for permissions in permission_sets:
            dummy_pdf = os.path.join(self.temp_dir, "test_perms.pdf")
            with open(dummy_pdf, 'w') as f:
                f.write("dummy content")
            
            result = self.security_manager.set_permissions(dummy_pdf, permissions)
            # Should fail due to invalid PDF format, but not due to permission validation
            self.assertFalse(result.success)
            # The error should be about file format, not permission validation
            self.assertIn("failed to open", result.message.lower())


if __name__ == '__main__':
    unittest.main()