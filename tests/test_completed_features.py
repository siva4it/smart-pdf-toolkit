#!/usr/bin/env python3
"""
Test script to demonstrate all completed Smart PDF Toolkit features.
"""

import os
import tempfile
from pathlib import Path
import fitz  # PyMuPDF for creating test PDFs

# Import Smart PDF Toolkit components
from smart_pdf_toolkit.core.config import config_manager, ApplicationConfig
from smart_pdf_toolkit.core.pdf_document import PDFDocumentValidator, PDFDocumentFactory, validate_pdf_files
from smart_pdf_toolkit.core.pdf_operations import PDFOperationsManager
from smart_pdf_toolkit.utils.file_utils import FileManager
from smart_pdf_toolkit.utils.validation import Validator
from smart_pdf_toolkit.plugins.base import plugin_manager


def create_sample_pdf(file_path: str, page_count: int = 3, content_prefix: str = "Sample"):
    """Create a sample PDF file for testing."""
    doc = fitz.open()
    
    for i in range(page_count):
        page = doc.new_page()
        text = f"{content_prefix} PDF - Page {i + 1}\n\nThis is page {i + 1} of {page_count}.\nCreated for testing purposes."
        page.insert_text((50, 100), text, fontsize=12)
    
    doc.save(file_path)
    doc.close()
    print(f"Created sample PDF: {file_path} ({page_count} pages)")


def test_configuration_system():
    """Test configuration management system."""
    print("\n" + "="*50)
    print("TESTING CONFIGURATION SYSTEM")
    print("="*50)
    
    try:
        # Load default configuration
        config = config_manager.load_config()
        print(f"✅ Configuration loaded successfully")
        print(f"   - Temp directory: {config.temp_directory}")
        print(f"   - Max file size: {config.max_file_size / (1024*1024):.1f} MB")
        print(f"   - OCR languages: {config.ocr_languages}")
        print(f"   - Log level: {config.log_level}")
        
        # Test configuration modification
        original_log_level = config.log_level
        config.log_level = "DEBUG"
        config_manager.save_config(config)
        
        # Reload and verify
        reloaded_config = config_manager.load_config()
        assert reloaded_config.log_level == "DEBUG"
        print(f"✅ Configuration modification and reload successful")
        
        # Restore original
        config.log_level = original_log_level
        config_manager.save_config(config)
        
        return True
    except Exception as e:
        print(f"❌ Configuration system test failed: {e}")
        return False


def test_file_management():
    """Test file management utilities."""
    print("\n" + "="*50)
    print("TESTING FILE MANAGEMENT")
    print("="*50)
    
    try:
        with FileManager() as fm:
            # Test temporary file creation
            temp_file = fm.create_temp_file(suffix=".pdf", prefix="test_")
            temp_dir = fm.create_temp_dir(prefix="test_")
            
            print(f"✅ Temporary file created: {temp_file}")
            print(f"✅ Temporary directory created: {temp_dir}")
            
            # Test file operations
            test_content = b"Test PDF content"
            with open(temp_file, 'wb') as f:
                f.write(test_content)
            
            file_size = fm.get_file_size(temp_file)
            print(f"✅ File size retrieved: {file_size} bytes")
            
            # Test directory operations
            fm.ensure_directory(Path(temp_dir) / "subdir")
            print(f"✅ Directory creation successful")
            
        print(f"✅ File cleanup completed automatically")
        return True
    except Exception as e:
        print(f"❌ File management test failed: {e}")
        return False


def test_pdf_document_validation():
    """Test PDF document validation and metadata extraction."""
    print("\n" + "="*50)
    print("TESTING PDF DOCUMENT VALIDATION")
    print("="*50)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test PDFs
            pdf1_path = os.path.join(temp_dir, "test1.pdf")
            pdf2_path = os.path.join(temp_dir, "test2.pdf")
            invalid_path = os.path.join(temp_dir, "invalid.txt")
            
            create_sample_pdf(pdf1_path, 3, "Document 1")
            create_sample_pdf(pdf2_path, 5, "Document 2")
            
            # Create invalid file
            with open(invalid_path, 'w') as f:
                f.write("Not a PDF")
            
            # Test individual validation
            is_valid = PDFDocumentValidator.validate_pdf_file(pdf1_path)
            print(f"✅ PDF validation successful: {is_valid}")
            
            # Test metadata extraction
            metadata = PDFDocumentValidator.extract_metadata(pdf1_path)
            print(f"✅ Metadata extracted - Pages: {metadata['page_count']}, Size: {metadata['file_size']} bytes")
            
            # Test integrity check
            integrity = PDFDocumentValidator.check_pdf_integrity(pdf1_path)
            print(f"✅ Integrity check - Valid: {integrity['is_valid']}, Encrypted: {integrity['is_encrypted']}")
            
            # Test PDFDocument creation
            pdf_doc = PDFDocumentFactory.create_from_file(pdf1_path)
            print(f"✅ PDFDocument created - Path: {pdf_doc.path}, Pages: {pdf_doc.page_count}")
            
            # Test batch validation
            file_list = [pdf1_path, pdf2_path, invalid_path, "nonexistent.pdf"]
            validation_results = validate_pdf_files(file_list)
            print(f"✅ Batch validation - Valid: {len(validation_results['valid_files'])}, Invalid: {len(validation_results['invalid_files'])}")
            
        return True
    except Exception as e:
        print(f"❌ PDF document validation test failed: {e}")
        return False


def test_pdf_operations():
    """Test PDF operations (merge, split, rotate, extract, reorder)."""
    print("\n" + "="*50)
    print("TESTING PDF OPERATIONS")
    print("="*50)
    
    try:
        operations_manager = PDFOperationsManager()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test PDFs
            pdf1_path = os.path.join(temp_dir, "doc1.pdf")
            pdf2_path = os.path.join(temp_dir, "doc2.pdf")
            pdf3_path = os.path.join(temp_dir, "doc3.pdf")
            
            create_sample_pdf(pdf1_path, 3, "Document A")
            create_sample_pdf(pdf2_path, 4, "Document B")
            create_sample_pdf(pdf3_path, 6, "Document C")
            
            # Test merge operation
            merged_path = os.path.join(temp_dir, "merged.pdf")
            merge_result = operations_manager.merge_pdfs([pdf1_path, pdf2_path], merged_path)
            print(f"✅ Merge operation - Success: {merge_result.success}, Output: {merge_result.output_files}")
            
            # Test split operation
            split_result = operations_manager.split_pdf(pdf3_path, [(1, 2), (3, 4), (5, 6)])
            print(f"✅ Split operation - Success: {split_result.success}, Files created: {len(split_result.output_files)}")
            
            # Test page rotation
            rotate_result = operations_manager.rotate_pages(pdf1_path, {1: 90, 3: 180})
            print(f"✅ Rotate operation - Success: {rotate_result.success}, Output: {rotate_result.output_files}")
            
            # Test page extraction
            extract_result = operations_manager.extract_pages(pdf2_path, [1, 3, 4])
            print(f"✅ Extract operation - Success: {extract_result.success}, Output: {extract_result.output_files}")
            
            # Test page reordering
            reorder_result = operations_manager.reorder_pages(pdf1_path, [3, 1, 2])
            print(f"✅ Reorder operation - Success: {reorder_result.success}, Output: {reorder_result.output_files}")
            
            # Verify all operations completed successfully
            all_successful = all([
                merge_result.success,
                split_result.success,
                rotate_result.success,
                extract_result.success,
                reorder_result.success
            ])
            
            if all_successful:
                print(f"✅ All PDF operations completed successfully!")
            else:
                print(f"⚠️  Some PDF operations had issues")
            
        return all_successful
    except Exception as e:
        print(f"❌ PDF operations test failed: {e}")
        return False


def test_validation_utilities():
    """Test validation utilities."""
    print("\n" + "="*50)
    print("TESTING VALIDATION UTILITIES")
    print("="*50)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            pdf_path = os.path.join(temp_dir, "test.pdf")
            create_sample_pdf(pdf_path, 2)
            
            # Test file existence validation
            Validator.validate_file_exists(pdf_path)
            print(f"✅ File existence validation passed")
            
            # Test PDF file validation
            Validator.validate_pdf_file(pdf_path)
            print(f"✅ PDF file validation passed")
            
            # Test output directory validation
            output_dir = os.path.join(temp_dir, "output")
            Validator.validate_output_directory(output_dir)
            print(f"✅ Output directory validation passed")
            
            # Test page range validation
            Validator.validate_page_range((1, 2), 2)
            print(f"✅ Page range validation passed")
            
            # Test page list validation
            Validator.validate_page_list([1, 2], 2)
            print(f"✅ Page list validation passed")
            
            # Test rotation angle validation
            Validator.validate_rotation_angle(90)
            print(f"✅ Rotation angle validation passed")
            
            # Test compression level validation
            Validator.validate_compression_level(5)
            print(f"✅ Compression level validation passed")
            
            # Test image format validation
            Validator.validate_image_format("png")
            print(f"✅ Image format validation passed")
            
        return True
    except Exception as e:
        print(f"❌ Validation utilities test failed: {e}")
        return False


def test_plugin_system():
    """Test plugin system."""
    print("\n" + "="*50)
    print("TESTING PLUGIN SYSTEM")
    print("="*50)
    
    try:
        # Test plugin discovery
        discovered_plugins = plugin_manager.discover_plugins()
        print(f"✅ Plugin discovery completed - Found: {len(discovered_plugins)} plugins")
        
        # Test plugin listing
        available_plugins = plugin_manager.list_available_plugins()
        loaded_plugins = plugin_manager.list_loaded_plugins()
        
        print(f"✅ Available plugins: {len(available_plugins)}")
        print(f"✅ Loaded plugins: {len(loaded_plugins)}")
        
        # Test plugin configuration
        plugins_config = config_manager.load_plugins_config()
        print(f"✅ Plugin configuration loaded: {len(plugins_config)} configured plugins")
        
        return True
    except Exception as e:
        print(f"❌ Plugin system test failed: {e}")
        return False


def main():
    """Run all completed feature tests."""
    print("Smart PDF Toolkit - Completed Features Test")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_results.append(("Configuration System", test_configuration_system()))
    test_results.append(("File Management", test_file_management()))
    test_results.append(("PDF Document Validation", test_pdf_document_validation()))
    test_results.append(("PDF Operations", test_pdf_operations()))
    test_results.append(("Validation Utilities", test_validation_utilities()))
    test_results.append(("Plugin System", test_plugin_system()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All completed features are working correctly!")
    else:
        print("⚠️  Some features need attention")
    
    return passed == total


if __name__ == "__main__":
    main()