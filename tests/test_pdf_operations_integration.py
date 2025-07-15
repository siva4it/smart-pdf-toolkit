"""
Integration tests for PDF operations with real PDF files.
"""

import os
import tempfile
import pytest
from pathlib import Path

from smart_pdf_toolkit.core.pdf_operations import PDFOperationsManager
from smart_pdf_toolkit.core.interfaces import OperationResult


def create_minimal_pdf(file_path: str, page_count: int = 3):
    """Create a minimal valid PDF file for testing."""
    # This creates a very basic PDF structure with multiple pages
    pdf_content = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [{' '.join([f'{i+3} 0 R' for i in range(page_count)])}]
/Count {page_count}
>>
endobj

"""
    
    # Add page objects
    for i in range(page_count):
        pdf_content += f"""
{i+3} 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
"""
    
    # Add xref and trailer
    pdf_content += f"""
xref
0 {page_count + 3}
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
"""
    
    for i in range(page_count):
        pdf_content += f"0000000{100 + i*50:03d} 00000 n \n"
    
    pdf_content += f"""trailer
<<
/Size {page_count + 3}
/Root 1 0 R
>>
startxref
{200 + page_count * 50}
%%EOF"""
    
    with open(file_path, 'w') as f:
        f.write(pdf_content)


class TestPDFOperationsIntegration:
    """Integration tests with real PDF files."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.operations_manager = PDFOperationsManager()
    
    def test_merge_real_pdfs(self):
        """Test merging real PDF files."""
        temp_files = []
        
        try:
            # Create test PDF files
            for i in range(3):
                temp_file = tempfile.NamedTemporaryFile(suffix=f'_test_{i}.pdf', delete=False)
                create_minimal_pdf(temp_file.name, page_count=2)
                temp_files.append(temp_file.name)
                temp_file.close()
            
            # Create output file path
            output_file = tempfile.NamedTemporaryFile(suffix='_merged.pdf', delete=False)
            output_file.close()
            temp_files.append(output_file.name)
            
            # Test merge operation
            result = self.operations_manager.merge_pdfs(temp_files[:-1], output_file.name)
            
            assert isinstance(result, OperationResult)
            assert result.success is True
            assert "Successfully merged 3 PDF files" in result.message
            assert os.path.exists(output_file.name)
            assert os.path.getsize(output_file.name) > 0
            
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except (OSError, PermissionError):
                    pass
    
    def test_split_real_pdf(self):
        """Test splitting a real PDF file."""
        temp_files = []
        
        try:
            # Create test PDF file with 5 pages
            input_file = tempfile.NamedTemporaryFile(suffix='_input.pdf', delete=False)
            create_minimal_pdf(input_file.name, page_count=5)
            temp_files.append(input_file.name)
            input_file.close()
            
            # Test split operation
            result = self.operations_manager.split_pdf(
                input_file.name, 
                [(1, 2), (3, 5)]
            )
            
            assert isinstance(result, OperationResult)
            assert result.success is True
            assert "Successfully split PDF into 2 files" in result.message
            assert len(result.output_files) == 2
            
            # Verify output files exist
            for output_file in result.output_files:
                assert os.path.exists(output_file)
                assert os.path.getsize(output_file) > 0
                temp_files.append(output_file)
            
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except (OSError, PermissionError):
                    pass
    
    def test_rotate_real_pdf_pages(self):
        """Test rotating pages in a real PDF file."""
        temp_files = []
        
        try:
            # Create test PDF file
            input_file = tempfile.NamedTemporaryFile(suffix='_input.pdf', delete=False)
            create_minimal_pdf(input_file.name, page_count=3)
            temp_files.append(input_file.name)
            input_file.close()
            
            # Test rotation operation
            result = self.operations_manager.rotate_pages(
                input_file.name, 
                {1: 90, 3: 180}
            )
            
            assert isinstance(result, OperationResult)
            assert result.success is True
            assert "Successfully rotated 2 pages" in result.message
            assert len(result.output_files) == 1
            
            # Verify output file exists
            output_file = result.output_files[0]
            assert os.path.exists(output_file)
            assert os.path.getsize(output_file) > 0
            temp_files.append(output_file)
            
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except (OSError, PermissionError):
                    pass
    
    def test_extract_real_pdf_pages(self):
        """Test extracting pages from a real PDF file."""
        temp_files = []
        
        try:
            # Create test PDF file
            input_file = tempfile.NamedTemporaryFile(suffix='_input.pdf', delete=False)
            create_minimal_pdf(input_file.name, page_count=5)
            temp_files.append(input_file.name)
            input_file.close()
            
            # Test extraction operation
            result = self.operations_manager.extract_pages(
                input_file.name, 
                [1, 3, 5]
            )
            
            assert isinstance(result, OperationResult)
            assert result.success is True
            assert "Successfully extracted 3 pages" in result.message
            assert len(result.output_files) == 1
            
            # Verify output file exists
            output_file = result.output_files[0]
            assert os.path.exists(output_file)
            assert os.path.getsize(output_file) > 0
            temp_files.append(output_file)
            
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except (OSError, PermissionError):
                    pass
    
    def test_reorder_real_pdf_pages(self):
        """Test reordering pages in a real PDF file."""
        temp_files = []
        
        try:
            # Create test PDF file
            input_file = tempfile.NamedTemporaryFile(suffix='_input.pdf', delete=False)
            create_minimal_pdf(input_file.name, page_count=4)
            temp_files.append(input_file.name)
            input_file.close()
            
            # Test reorder operation
            result = self.operations_manager.reorder_pages(
                input_file.name, 
                [4, 3, 2, 1]  # Reverse order
            )
            
            assert isinstance(result, OperationResult)
            assert result.success is True
            assert "Successfully reordered 4 pages" in result.message
            assert len(result.output_files) == 1
            
            # Verify output file exists
            output_file = result.output_files[0]
            assert os.path.exists(output_file)
            assert os.path.getsize(output_file) > 0
            temp_files.append(output_file)
            
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except (OSError, PermissionError):
                    pass


if __name__ == "__main__":
    pytest.main([__file__])