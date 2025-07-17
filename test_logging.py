#!/usr/bin/env python3
"""
Test logging setup and create log files
"""

import sys
import logging
from pathlib import Path
import os

def setup_logging():
    """Setup logging with multiple handlers"""
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Setup logging
    log_file = logs_dir / "smart_pdf_toolkit.log"
    
    # Create logger
    logger = logging.getLogger('smart_pdf_toolkit')
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger, log_file

def test_gui_merge():
    """Test GUI merge functionality with logging"""
    
    logger, log_file = setup_logging()
    
    print("="*60)
    print("SMART PDF TOOLKIT - MERGE DEBUG TEST")
    print("="*60)
    print(f"Log file: {log_file.absolute()}")
    print()
    
    logger.info("Starting GUI merge debug test")
    
    try:
        # Add src to path
        sys.path.insert(0, 'src')
        logger.info("Added src to Python path")
        
        # Test imports
        logger.info("Testing imports...")
        
        try:
            from smart_pdf_toolkit.core.pdf_operations import PDFOperationsManager
            logger.info("✅ Successfully imported PDFOperationsManager")
            print("✅ Core PDF operations import successful")
        except Exception as e:
            logger.error(f"❌ Failed to import PDFOperationsManager: {e}")
            print(f"❌ Failed to import PDFOperationsManager: {e}")
            return
        
        try:
            from smart_pdf_toolkit.gui.main_window import MainWindow
            logger.info("✅ Successfully imported MainWindow")
            print("✅ GUI components import successful")
        except Exception as e:
            logger.error(f"❌ Failed to import MainWindow: {e}")
            print(f"❌ Failed to import MainWindow: {e}")
            print("Note: This might be due to missing PyQt6")
        
        # Test PDF operations directly
        logger.info("Testing PDF operations...")
        ops = PDFOperationsManager()
        logger.info("✅ PDFOperationsManager instance created")
        print("✅ PDF operations instance created")
        
        # Get current directory files
        current_dir = Path(".")
        pdf_files = list(current_dir.glob("*.pdf"))
        
        if pdf_files:
            logger.info(f"Found {len(pdf_files)} PDF files in current directory")
            print(f"📄 Found {len(pdf_files)} PDF files in current directory:")
            for pdf in pdf_files:
                print(f"   - {pdf}")
                logger.info(f"   Found PDF: {pdf}")
        else:
            logger.info("No PDF files found in current directory")
            print("📄 No PDF files found in current directory")
            
            # Create sample PDF files for testing
            print("\n🔧 Creating sample PDF files for testing...")
            logger.info("Creating sample PDF files for testing")
            
            try:
                create_sample_pdfs()
                logger.info("✅ Sample PDF files created")
                print("✅ Sample PDF files created")
            except Exception as e:
                logger.error(f"❌ Failed to create sample PDFs: {e}")
                print(f"❌ Failed to create sample PDFs: {e}")
        
        print(f"\n📝 Log file created at: {log_file.absolute()}")
        print("You can now:")
        print("1. Run the GUI: python src/smart_pdf_toolkit/gui/app.py")
        print("2. Try merge operation and check the log file")
        print("3. Run: python debug_merge.py for interactive debugging")
        
    except Exception as e:
        logger.exception("Unexpected error in test")
        print(f"❌ Unexpected error: {e}")

def create_sample_pdfs():
    """Create sample PDF files for testing"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create sample PDF 1
        pdf1_path = Path("sample1.pdf")
        c = canvas.Canvas(str(pdf1_path), pagesize=letter)
        c.drawString(100, 750, "Sample PDF 1")
        c.drawString(100, 700, "This is the first test PDF file.")
        c.drawString(100, 650, "Created for merge testing.")
        c.save()
        
        # Create sample PDF 2
        pdf2_path = Path("sample2.pdf")
        c = canvas.Canvas(str(pdf2_path), pagesize=letter)
        c.drawString(100, 750, "Sample PDF 2")
        c.drawString(100, 700, "This is the second test PDF file.")
        c.drawString(100, 650, "Also created for merge testing.")
        c.save()
        
        print(f"✅ Created {pdf1_path}")
        print(f"✅ Created {pdf2_path}")
        
    except ImportError:
        print("⚠️  reportlab not available, cannot create sample PDFs")
        print("Install with: pip install reportlab")

def main():
    """Main function"""
    test_gui_merge()

if __name__ == "__main__":
    main()