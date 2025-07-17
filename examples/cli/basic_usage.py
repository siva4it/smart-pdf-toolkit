#!/usr/bin/env python3
"""
Basic CLI usage examples for Smart PDF Toolkit
"""

import subprocess
import sys
from pathlib import Path

def run_command(command):
    """Run a command and print the result"""
    print(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

def main():
    """Demonstrate basic CLI usage"""
    print("Smart PDF Toolkit - CLI Examples")
    print("=" * 40)
    
    # Example PDF file (you should have this in your test data)
    sample_pdf = Path("tests/fixtures/sample.pdf")
    
    if not sample_pdf.exists():
        print(f"Sample PDF not found at {sample_pdf}")
        print("Please ensure you have test fixtures available")
        return
    
    # Example 1: Get PDF information
    print("\n1. Getting PDF information:")
    run_command(["smart-pdf", "info", str(sample_pdf)])
    
    # Example 2: Extract text from PDF
    print("\n2. Extracting text from PDF:")
    run_command(["smart-pdf", "extract-text", str(sample_pdf), "-o", "extracted_text.txt"])
    
    # Example 3: Convert PDF to images
    print("\n3. Converting PDF to images:")
    run_command(["smart-pdf", "to-images", str(sample_pdf), "-o", "output_images/"])
    
    # Example 4: Optimize PDF
    print("\n4. Optimizing PDF:")
    run_command(["smart-pdf", "optimize", str(sample_pdf), "-o", "optimized.pdf"])
    
    # Example 5: Merge multiple PDFs (if you have multiple files)
    print("\n5. Merging PDFs:")
    run_command(["smart-pdf", "merge", str(sample_pdf), str(sample_pdf), "-o", "merged.pdf"])
    
    # Example 6: Split PDF
    print("\n6. Splitting PDF:")
    run_command(["smart-pdf", "split", str(sample_pdf), "-p", "1-2", "-o", "split_pages.pdf"])
    
    # Example 7: Add password protection
    print("\n7. Adding password protection:")
    run_command(["smart-pdf", "protect", str(sample_pdf), "--password", "secret123", "-o", "protected.pdf"])
    
    print("\nCLI examples completed!")

if __name__ == "__main__":
    main()