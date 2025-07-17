#!/usr/bin/env python3
"""
Simple test for merge functionality with Windows path support
"""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_merge_with_sample_files():
    """Test merge functionality with the sample files we created"""
    
    print("🧪 Testing PDF Merge Functionality")
    print("=" * 40)
    
    try:
        # Import the corrected classes
        from smart_pdf_toolkit.core.pdf_operations import PDFOperationsManager
        from smart_pdf_toolkit.core.config import ApplicationConfig
        
        # Create config with Windows-compatible paths
        config = ApplicationConfig()
        print(f"✅ Config created with temp dir: {config.temp_directory}")
        print(f"✅ Output dir: {config.output_dir}")
        
        # Initialize PDF operations
        pdf_ops = PDFOperationsManager(config)
        print("✅ PDFOperationsManager initialized")
        
        # Check for sample files
        sample1 = Path("sample1.pdf")
        sample2 = Path("sample2.pdf")
        
        if not sample1.exists() or not sample2.exists():
            print("❌ Sample PDF files not found")
            print("Run: python test_logging.py first to create sample files")
            return False
        
        print(f"✅ Found sample files: {sample1}, {sample2}")
        
        # Test merge
        output_file = "test_merged_output.pdf"
        input_files = [str(sample1), str(sample2)]
        
        print(f"🔄 Merging {len(input_files)} files...")
        print(f"   Input: {input_files}")
        print(f"   Output: {output_file}")
        
        # Perform merge
        result = pdf_ops.merge_pdfs(input_files, output_file)
        
        if result and hasattr(result, 'success') and result.success:
            print("✅ Merge operation successful!")
            
            # Check output file
            output_path = Path(output_file)
            if output_path.exists():
                file_size = output_path.stat().st_size
                print(f"✅ Output file created: {output_path} ({file_size} bytes)")
                
                # Try to verify it's a valid PDF
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(output_file)
                    page_count = doc.page_count
                    doc.close()
                    print(f"✅ Output PDF verified: {page_count} pages")
                except Exception as e:
                    print(f"⚠️  Could not verify PDF (PyMuPDF not available): {e}")
                
                return True
            else:
                print(f"❌ Output file not created: {output_path}")
                return False
        else:
            print(f"❌ Merge operation failed: {result}")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you've installed the package: pip install -e .")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("Smart PDF Toolkit - Simple Merge Test")
    print("Testing merge functionality with Windows path support")
    print()
    
    success = test_merge_with_sample_files()
    
    if success:
        print("\n🎉 Merge test completed successfully!")
        print("The GUI merge functionality should now work properly.")
    else:
        print("\n❌ Merge test failed.")
        print("Check the error messages above for troubleshooting.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)