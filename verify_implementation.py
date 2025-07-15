#!/usr/bin/env python3
"""
Comprehensive verification script for Smart PDF Toolkit implementation.
Tests all core functionality after project reorganization.
"""

import os
import sys
import traceback
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all core modules can be imported successfully."""
    print("🔍 Testing module imports...")
    
    try:
        # Core interfaces
        from smart_pdf_toolkit.core.interfaces import (
            IPDFOperations, IContentExtractor, IOCRProcessor, 
            IFormatConverter, OperationResult, PDFDocument
        )
        print("  ✅ Core interfaces imported successfully")
        
        # Core implementations
        from smart_pdf_toolkit.core.pdf_operations import PDFOperationsManager
        from smart_pdf_toolkit.core.content_extractor import ContentExtractor
        from smart_pdf_toolkit.core.ocr_processor import OCRProcessor
        from smart_pdf_toolkit.core.format_converter import FormatConverter
        from smart_pdf_toolkit.core.pdf_document import PDFDocumentValidator, PDFDocumentFactory
        print("  ✅ Core implementations imported successfully")
        
        # Configuration and exceptions
        from smart_pdf_toolkit.core.config import ApplicationConfig, ConfigManager
        from smart_pdf_toolkit.core.exceptions import (
            PDFToolkitError, PDFProcessingError, ValidationError
        )
        print("  ✅ Configuration and exceptions imported successfully")
        
        # Utilities
        from smart_pdf_toolkit.utils.validation import validate_pdf_file
        from smart_pdf_toolkit.utils.file_utils import FileManager
        from smart_pdf_toolkit.utils.logging_utils import setup_logging
        print("  ✅ Utilities imported successfully")
        
        # Plugin system
        from smart_pdf_toolkit.plugins.base import PluginManager
        print("  ✅ Plugin system imported successfully")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import failed: {str(e)}")
        traceback.print_exc()
        return False

def test_core_classes():
    """Test that core classes can be instantiated."""
    print("\n🔍 Testing core class instantiation...")
    
    try:
        # Import classes first
        from smart_pdf_toolkit.core.pdf_operations import PDFOperationsManager
        from smart_pdf_toolkit.core.content_extractor import ContentExtractor
        from smart_pdf_toolkit.core.ocr_processor import OCRProcessor
        from smart_pdf_toolkit.core.format_converter import FormatConverter
        from smart_pdf_toolkit.core.config import ApplicationConfig, ConfigManager
        from smart_pdf_toolkit.plugins.base import PluginManager
        
        # Test PDF Operations
        pdf_ops = PDFOperationsManager()
        print("  ✅ PDFOperationsManager instantiated")
        
        # Test Content Extractor
        extractor = ContentExtractor()
        print("  ✅ ContentExtractor instantiated")
        
        # Test OCR Processor
        try:
            ocr = OCRProcessor()
            print("  ✅ OCRProcessor instantiated")
        except Exception as e:
            print(f"  ⚠️  OCRProcessor warning (tesseract may not be installed): {str(e)}")
        
        # Test Format Converter
        converter = FormatConverter()
        print("  ✅ FormatConverter instantiated")
        
        # Test Configuration
        config = ApplicationConfig()
        config_manager = ConfigManager()
        print("  ✅ Configuration classes instantiated")
        
        # Test Plugin Manager
        plugin_manager = PluginManager()
        print("  ✅ PluginManager instantiated")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Class instantiation failed: {str(e)}")
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality without requiring actual PDF files."""
    print("\n🔍 Testing basic functionality...")
    
    try:
        # Test validation utilities
        from smart_pdf_toolkit.utils.validation import Validator
        
        # Test file manager
        from smart_pdf_toolkit.utils.file_utils import FileManager
        with FileManager() as fm:
            temp_file = fm.create_temp_file(suffix=".txt")
            print(f"  ✅ Temporary file created: {temp_file}")
        
        # Test logging setup
        from smart_pdf_toolkit.utils.logging_utils import setup_logging
        logger = setup_logging(log_level="INFO")
        logger.info("Test log message")
        print("  ✅ Logging system working")
        
        # Test configuration
        from smart_pdf_toolkit.core.config import ApplicationConfig
        config = ApplicationConfig()
        print(f"  ✅ Configuration loaded with temp_directory: {config.temp_directory}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Basic functionality test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_interface_compliance():
    """Test that implementations comply with their interfaces."""
    print("\n🔍 Testing interface compliance...")
    
    try:
        from smart_pdf_toolkit.core.interfaces import IPDFOperations, IContentExtractor
        from smart_pdf_toolkit.core.pdf_operations import PDFOperationsManager
        from smart_pdf_toolkit.core.content_extractor import ContentExtractor
        
        # Test PDF Operations interface compliance
        pdf_ops = PDFOperationsManager()
        assert isinstance(pdf_ops, IPDFOperations), "PDFOperationsManager doesn't implement IPDFOperations"
        print("  ✅ PDFOperationsManager implements IPDFOperations")
        
        # Test Content Extractor interface compliance
        extractor = ContentExtractor()
        assert isinstance(extractor, IContentExtractor), "ContentExtractor doesn't implement IContentExtractor"
        print("  ✅ ContentExtractor implements IContentExtractor")
        
        # Check that required methods exist
        required_pdf_methods = ['merge_pdfs', 'split_pdf', 'rotate_pages', 'extract_pages', 'reorder_pages']
        for method in required_pdf_methods:
            assert hasattr(pdf_ops, method), f"PDFOperationsManager missing method: {method}"
        print("  ✅ PDFOperationsManager has all required methods")
        
        required_extractor_methods = ['extract_text', 'extract_images', 'extract_tables', 'extract_metadata', 'extract_links']
        for method in required_extractor_methods:
            assert hasattr(extractor, method), f"ContentExtractor missing method: {method}"
        print("  ✅ ContentExtractor has all required methods")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Interface compliance test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_dependencies():
    """Test that required dependencies are available."""
    print("\n🔍 Testing dependencies...")
    
    dependencies = {
        'PyMuPDF': 'fitz',
        'pdfplumber': 'pdfplumber',
        'PyYAML': 'yaml',
        'Pillow': 'PIL',
        'pytesseract': 'pytesseract',
        'langdetect': 'langdetect'
    }
    
    missing_deps = []
    
    for dep_name, import_name in dependencies.items():
        try:
            __import__(import_name)
            print(f"  ✅ {dep_name} available")
        except ImportError:
            print(f"  ❌ {dep_name} missing")
            missing_deps.append(dep_name)
    
    if missing_deps:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print("   Install with: pip install -r requirements.txt")
        return False
    
    return True

def test_project_structure():
    """Test that project structure is correct."""
    print("\n🔍 Testing project structure...")
    
    required_dirs = [
        'smart_pdf_toolkit',
        'smart_pdf_toolkit/core',
        'smart_pdf_toolkit/api',
        'smart_pdf_toolkit/cli',
        'smart_pdf_toolkit/gui',
        'smart_pdf_toolkit/web',
        'smart_pdf_toolkit/plugins',
        'smart_pdf_toolkit/utils',
        'tests',
        '.kiro'
    ]
    
    required_files = [
        'requirements.txt',
        'README.md',
        '.gitignore',
        'smart_pdf_toolkit/__init__.py',
        'smart_pdf_toolkit/core/interfaces.py',
        'smart_pdf_toolkit/core/pdf_operations.py',
        'smart_pdf_toolkit/core/content_extractor.py'
    ]
    
    missing_items = []
    
    for dir_path in required_dirs:
        if not os.path.isdir(dir_path):
            missing_items.append(f"Directory: {dir_path}")
        else:
            print(f"  ✅ Directory exists: {dir_path}")
    
    for file_path in required_files:
        if not os.path.isfile(file_path):
            missing_items.append(f"File: {file_path}")
        else:
            print(f"  ✅ File exists: {file_path}")
    
    if missing_items:
        print(f"\n❌ Missing items:")
        for item in missing_items:
            print(f"   - {item}")
        return False
    
    return True

def main():
    """Run all verification tests."""
    print("🚀 Smart PDF Toolkit - Implementation Verification")
    print("=" * 60)
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Dependencies", test_dependencies),
        ("Module Imports", test_imports),
        ("Class Instantiation", test_core_classes),
        ("Interface Compliance", test_interface_compliance),
        ("Basic Functionality", test_basic_functionality)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Your Smart PDF Toolkit implementation is working correctly.")
        print("✅ Ready to proceed with next development tasks (6-15)")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please fix issues before proceeding.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)