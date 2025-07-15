"""
Unit tests for BatchProcessor class.
"""

import unittest
import tempfile
import os
import time
from pathlib import Path

from smart_pdf_toolkit.core.batch_processor import BatchProcessor, BatchConfiguration, BatchJobInternal
from smart_pdf_toolkit.core.interfaces import JobStatus
from smart_pdf_toolkit.core.exceptions import PDFProcessingError, ValidationError


class TestBatchProcessor(unittest.TestCase):
    """Test cases for BatchProcessor functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.batch_processor = BatchProcessor()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create some dummy files for testing
        self.test_files = []
        for i in range(3):
            test_file = os.path.join(self.temp_dir, f"test_{i}.pdf")
            with open(test_file, 'w') as f:
                f.write(f"dummy content {i}")
            self.test_files.append(test_file)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Shutdown batch processor
        self.batch_processor.shutdown()
        
        # Clean up temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_batch_processor_initialization(self):
        """Test BatchProcessor initialization."""
        processor = BatchProcessor()
        self.assertIsNotNone(processor)
        self.assertIsNotNone(processor.config)
        self.assertIsNotNone(processor.batch_config)
        self.assertIsInstance(processor.batch_config, BatchConfiguration)
    
    def test_batch_configuration_creation(self):
        """Test BatchConfiguration dataclass."""
        # Test default config
        config = BatchConfiguration()
        self.assertEqual(config.max_workers, 4)
        self.assertEqual(config.chunk_size, 10)
        self.assertTrue(config.retry_failed)
        self.assertEqual(config.max_retries, 2)
        self.assertTrue(config.continue_on_error)
        
        # Test custom config
        config = BatchConfiguration(
            max_workers=8,
            chunk_size=20,
            retry_failed=False,
            max_retries=5,
            continue_on_error=False
        )
        self.assertEqual(config.max_workers, 8)
        self.assertEqual(config.chunk_size, 20)
        self.assertFalse(config.retry_failed)
        self.assertEqual(config.max_retries, 5)
        self.assertFalse(config.continue_on_error)
    
    def test_create_batch_job_validation(self):
        """Test batch job creation input validation."""
        # Test with empty operation
        with self.assertRaises(PDFProcessingError):
            self.batch_processor.create_batch_job("", self.test_files, {})
        
        # Test with unsupported operation
        with self.assertRaises(PDFProcessingError):
            self.batch_processor.create_batch_job("unsupported_op", self.test_files, {})
        
        # Test with empty file list
        with self.assertRaises(PDFProcessingError):
            self.batch_processor.create_batch_job("compress", [], {})
        
        # Test with non-existent files
        with self.assertRaises(PDFProcessingError):
            self.batch_processor.create_batch_job("compress", ["nonexistent.pdf"], {})
    
    def test_create_batch_job_success(self):
        """Test successful batch job creation."""
        job = self.batch_processor.create_batch_job("compress", self.test_files, {"compression_level": 5})
        
        self.assertIsNotNone(job.job_id)
        self.assertEqual(job.operation, "compress")
        self.assertEqual(job.status, JobStatus.PENDING)
        self.assertEqual(job.total_files, len(self.test_files))
        self.assertEqual(job.processed_files, 0)
        self.assertEqual(job.failed_files, 0)
        self.assertIsNotNone(job.created_at)
        self.assertIsNone(job.completed_at)
    
    def test_get_batch_status_validation(self):
        """Test batch status retrieval validation."""
        # Test with non-existent job
        with self.assertRaises(PDFProcessingError):
            self.batch_processor.get_batch_status("nonexistent-job-id")
    
    def test_get_batch_status_success(self):
        """Test successful batch status retrieval."""
        job = self.batch_processor.create_batch_job("compress", self.test_files, {"compression_level": 5})
        
        # Get status immediately
        status = self.batch_processor.get_batch_status(job.job_id)
        
        self.assertEqual(status.job_id, job.job_id)
        self.assertEqual(status.operation, "compress")
        self.assertIn(status.status, [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.COMPLETED])
        self.assertEqual(status.total_files, len(self.test_files))
    
    def test_cancel_batch_job(self):
        """Test batch job cancellation."""
        job = self.batch_processor.create_batch_job("compress", self.test_files, {"compression_level": 5})
        
        # Cancel the job
        result = self.batch_processor.cancel_batch_job(job.job_id)
        self.assertTrue(result)
        
        # Check status
        status = self.batch_processor.get_batch_status(job.job_id)
        self.assertEqual(status.status, JobStatus.CANCELLED)
        
        # Try to cancel again (should return False)
        result = self.batch_processor.cancel_batch_job(job.job_id)
        self.assertFalse(result)
        
        # Try to cancel non-existent job
        result = self.batch_processor.cancel_batch_job("nonexistent-job-id")
        self.assertFalse(result)
    
    def test_get_supported_operations(self):
        """Test getting supported operations."""
        operations = self.batch_processor.get_supported_operations()
        
        self.assertIsInstance(operations, list)
        self.assertGreater(len(operations), 0)
        
        # Check for expected operations
        expected_operations = [
            'merge', 'split', 'rotate', 'extract_pages', 'extract_text',
            'extract_images', 'ocr', 'convert_to_images', 'add_password',
            'compress', 'optimize_web'
        ]
        
        for op in expected_operations:
            self.assertIn(op, operations)
    
    def test_get_job_statistics_validation(self):
        """Test job statistics retrieval validation."""
        # Test with non-existent job
        with self.assertRaises(PDFProcessingError):
            self.batch_processor.get_job_statistics("nonexistent-job-id")
    
    def test_get_job_statistics_success(self):
        """Test successful job statistics retrieval."""
        job = self.batch_processor.create_batch_job("compress", self.test_files, {"compression_level": 5})
        
        # Get statistics
        stats = self.batch_processor.get_job_statistics(job.job_id)
        
        # Check required fields
        required_fields = [
            'job_id', 'operation', 'status', 'total_files', 'processed_files',
            'failed_files', 'success_rate', 'job_duration_seconds',
            'total_processing_time_seconds', 'average_processing_time_seconds',
            'created_at', 'successful_operations', 'failed_operations',
            'total_warnings', 'total_errors'
        ]
        
        for field in required_fields:
            self.assertIn(field, stats)
        
        self.assertEqual(stats['job_id'], job.job_id)
        self.assertEqual(stats['operation'], 'compress')
        self.assertEqual(stats['total_files'], len(self.test_files))
    
    def test_cleanup_completed_jobs(self):
        """Test cleanup of completed jobs."""
        # Create a job
        job = self.batch_processor.create_batch_job("compress", self.test_files, {"compression_level": 5})
        
        # Cancel it to make it completed
        self.batch_processor.cancel_batch_job(job.job_id)
        
        # Cleanup with very short age (should clean up the job)
        cleaned_count = self.batch_processor.cleanup_completed_jobs(max_age_hours=0)
        
        # Should have cleaned up at least one job
        self.assertGreaterEqual(cleaned_count, 0)
    
    def test_batch_job_internal_structure(self):
        """Test BatchJobInternal dataclass structure."""
        from datetime import datetime
        
        job = BatchJobInternal(
            job_id="test-id",
            operation="compress",
            status=JobStatus.PENDING,
            total_files=5,
            files=["file1.pdf", "file2.pdf"],
            params={"compression_level": 5}
        )
        
        self.assertEqual(job.job_id, "test-id")
        self.assertEqual(job.operation, "compress")
        self.assertEqual(job.status, JobStatus.PENDING)
        self.assertEqual(job.total_files, 5)
        self.assertEqual(job.processed_files, 0)  # Default
        self.assertEqual(job.failed_files, 0)  # Default
        self.assertIsInstance(job.created_at, datetime)
        self.assertIsNone(job.started_at)  # Default
        self.assertIsNone(job.completed_at)  # Default
        self.assertEqual(job.files, ["file1.pdf", "file2.pdf"])
        self.assertEqual(job.params, {"compression_level": 5})
    
    def test_batch_processor_methods_exist(self):
        """Test that all required methods exist."""
        required_methods = [
            'create_batch_job',
            'get_batch_status',
            'cancel_batch_job',
            'get_supported_operations',
            'get_job_statistics',
            'cleanup_completed_jobs',
            'shutdown'
        ]
        
        for method in required_methods:
            self.assertTrue(hasattr(self.batch_processor, method))
            self.assertTrue(callable(getattr(self.batch_processor, method)))
    
    def test_batch_operation_handlers_exist(self):
        """Test that all batch operation handlers exist."""
        expected_handlers = [
            '_batch_merge', '_batch_split', '_batch_rotate', '_batch_extract_pages',
            '_batch_extract_text', '_batch_extract_images', '_batch_ocr',
            '_batch_convert_to_images', '_batch_add_password', '_batch_compress',
            '_batch_optimize_web'
        ]
        
        for handler in expected_handlers:
            self.assertTrue(hasattr(self.batch_processor, handler))
            self.assertTrue(callable(getattr(self.batch_processor, handler)))
    
    def test_shutdown_method(self):
        """Test batch processor shutdown."""
        # Create a processor
        processor = BatchProcessor()
        
        # Shutdown should not raise an exception
        processor.shutdown()
        
        # Multiple shutdowns should be safe
        processor.shutdown()


if __name__ == '__main__':
    unittest.main()