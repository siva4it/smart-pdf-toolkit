"""
Tests for core interfaces and data structures.
"""

import unittest
from datetime import datetime
from smart_pdf_toolkit.core.interfaces import (
    OperationResult, PDFDocument, BatchJob, JobStatus
)


class TestDataStructures(unittest.TestCase):
    """Test cases for core data structures."""
    
    def test_operation_result_creation(self):
        """Test OperationResult creation."""
        result = OperationResult(
            success=True,
            message="Operation completed successfully",
            output_files=["output.pdf"],
            execution_time=1.5,
            warnings=["Minor warning"],
            errors=[]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Operation completed successfully")
        self.assertEqual(len(result.output_files), 1)
        self.assertEqual(result.execution_time, 1.5)
        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(len(result.errors), 0)
    
    def test_pdf_document_creation(self):
        """Test PDFDocument creation."""
        doc = PDFDocument(
            path="/path/to/document.pdf",
            page_count=10,
            file_size=1024000,
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            author="Test Author",
            title="Test Document",
            is_encrypted=False,
            permissions={"print": True, "copy": True}
        )
        
        self.assertEqual(doc.path, "/path/to/document.pdf")
        self.assertEqual(doc.page_count, 10)
        self.assertEqual(doc.file_size, 1024000)
        self.assertFalse(doc.is_encrypted)
        self.assertTrue(doc.permissions["print"])
    
    def test_batch_job_creation(self):
        """Test BatchJob creation."""
        job = BatchJob(
            job_id="job_123",
            operation="merge",
            status=JobStatus.PENDING,
            total_files=5,
            processed_files=0,
            failed_files=0,
            created_at=datetime.now(),
            completed_at=None,
            results=[]
        )
        
        self.assertEqual(job.job_id, "job_123")
        self.assertEqual(job.operation, "merge")
        self.assertEqual(job.status, JobStatus.PENDING)
        self.assertEqual(job.total_files, 5)
        self.assertIsNone(job.completed_at)


if __name__ == '__main__':
    unittest.main()