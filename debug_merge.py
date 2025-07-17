#!/usr/bin/env python3
"""
Debug script for testing PDF merge functionality
"""

import sys
import logging
from pathlib import Path

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('merge_debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, 'src')

def test_merge_functionality():
    """Test the merge functionality with debug output."""
    try:
        logger.info("Starting merge functionality test...")
        
        # Import after path setup
        from smart_pdf_toolkit.core.pdf_operations import PDFOperations
        
        # Initialize PDF operations
        ops = PDFOperations()
        logger.info("PDFOperations initialized successfully")
        
        # Get test files from user
        print("\n" + "="*50)
        print("PDF MERGE DEBUG TOOL")
        print("="*50)
        
        files = []
        while len(files) < 2:
            file_path = input(f"Enter path to PDF file {len(files) + 1} (or 'quit' to exit): ").strip()
            
            if file_path.lower() == 'quit':
                return
                
            path = Path(file_path)
            
            if not path.exists():
                print(f"❌ File not found: {path}")
                continue
                
            if not path.suffix.lower() == '.pdf':
                print(f"❌ Not a PDF file: {path}")
                continue
                
            # Test if file is readable
            try:
                with open(path, 'rb') as f:
                    f.read(1024)
                logger.info(f"File is readable: {path}")
            except Exception as e:
                print(f"❌ Cannot read file {path}: {e}")
                continue
            
            # Test if it's a valid PDF
            try:
                import PyMuPDF as fitz
                doc = fitz.open(path)
                page_count = doc.page_count
                doc.close()
                print(f"✅ Valid PDF: {path} ({page_count} pages)")
                logger.info(f"Valid PDF with {page_count} pages: {path}")
            except Exception as e:
                print(f"❌ Invalid PDF {path}: {e}")
                continue
                
            files.append(path)
            
            if len(files) >= 2:
                add_more = input("Add another file? (y/n): ").strip().lower()
                if add_more == 'y':
                    continue
                else:
                    break
        
        # Get output filename
        output_file = input("Enter output filename (default: debug_merged.pdf): ").strip()
        if not output_file:
            output_file = "debug_merged.pdf"
            
        output_path = Path(output_file)
        
        print(f"\n📋 Merge Summary:")
        print(f"   Input files: {len(files)}")
        for i, file in enumerate(files, 1):
            print(f"   {i}. {file}")
        print(f"   Output: {output_path}")
        
        # Confirm merge
        confirm = input("\nProceed with merge? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Merge cancelled.")
            return
            
        print("\n🔄 Starting merge operation...")
        logger.info(f"Starting merge of {len(files)} files to {output_path}")
        
        # Perform merge
        result = ops.merge_pdfs(files, str(output_path))
        
        if result and hasattr(result, 'success') and result.success:
            print(f"✅ Merge successful! Output: {output_path}")
            logger.info(f"Merge completed successfully: {output_path}")
            
            # Verify output file
            if output_path.exists():
                try:
                    import PyMuPDF as fitz
                    doc = fitz.open(output_path)
                    page_count = doc.page_count
                    doc.close()
                    print(f"📄 Output PDF has {page_count} pages")
                    logger.info(f"Output PDF verified: {page_count} pages")
                except Exception as e:
                    print(f"⚠️  Warning: Could not verify output PDF: {e}")
                    logger.warning(f"Could not verify output PDF: {e}")
            else:
                print(f"❌ Output file was not created: {output_path}")
                logger.error(f"Output file not found: {output_path}")
        else:
            print(f"❌ Merge failed!")
            logger.error(f"Merge operation failed: {result}")
            
    except ImportError as e:
        logger.error(f"Import error: {e}")
        print(f"❌ Import error: {e}")
        print("Make sure you've installed the package: pip install -e .")
    except Exception as e:
        logger.exception("Unexpected error during merge test")
        print(f"❌ Unexpected error: {e}")
        print("Check merge_debug.log for detailed error information")

def main():
    """Main function."""
    print("Smart PDF Toolkit - Merge Debug Tool")
    print("This tool will help debug merge functionality issues")
    print("Logs are written to: merge_debug.log")
    print()
    
    test_merge_functionality()
    
    print(f"\n📝 Debug log saved to: merge_debug.log")
    print("You can share this log file for further debugging help.")

if __name__ == "__main__":
    main()