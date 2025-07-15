"""
Minimal test of class definition
"""

import sys
sys.path.insert(0, '.')

from smart_pdf_toolkit.core.interfaces import IFormatConverter, OperationResult
from smart_pdf_toolkit.core.exceptions import ConversionError
from smart_pdf_toolkit.core.config import ApplicationConfig

print("All imports successful")

class TestConverter(IFormatConverter):
    """Test converter class"""
    
    def __init__(self):
        print("TestConverter initialized")
    
    def pdf_to_office(self, pdf_path: str, target_format: str) -> OperationResult:
        return OperationResult(
            success=False,
            message="Test implementation",
            output_files=[],
            execution_time=0.0,
            warnings=[],
            errors=[]
        )

print("TestConverter defined")
converter = TestConverter()
print("TestConverter instantiated successfully")