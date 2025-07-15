"""
Simple test of FormatConverter implementation
"""

import sys
import os
sys.path.insert(0, '.')

try:
    print("Testing FormatConverter import...")
    from smart_pdf_toolkit.core.format_converter import FormatConverter
    print("SUCCESS: FormatConverter imported")
    
    converter = FormatConverter()
    print("SUCCESS: FormatConverter instantiated")
    
    # Test a simple method
    result = converter.pdf_to_office("test.pdf", "docx")
    print(f"Method call result: {result.success}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()