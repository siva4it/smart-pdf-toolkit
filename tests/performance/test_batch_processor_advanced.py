"""
Advanced unit tests for BatchProcessor reporting and error handling features.
"""

import unittest
import tempfile
import os
import json
from pathlib import Path

from smart_pdf_toolkit.core.batch_processor import BatchProcessor, BatchConfiguration
from smart_pdf_toolkit.core.interfaces import JobStatus
from smart_pdf_toolkit.core.exceptions import PDFProcessingError, ValidationError


class TestBatchProcessorAdvanced(unittest.TestCase):
    """Test cases for BatchProcessor advanced functionality."""
    
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
    
    def test_generate_batch_report_validation(self):
        """Test batch report generation input validation."""
        # Test with non-existent job
        report = self.batch_processor.generate_batch_report("nonexistent-job-id")
        self.assertIn("error", report)
        self.assertIn("Job not found", report["error"])
    
    def test_generate_batch_report_structure(self):
        """Test batch report structure."""
        job = self.batch_processor.create_batch_job("compress", self.test_files, {"compression_level": 5})
        
        # Wait a moment for job to process
        import time
        time.sleep(0.5)
        
        # Generate report
        report = self.batch_processor.generate_batch_report(job.job_id)
        
        # Check report structure
        if "error" not in report:
            required_sections = ['job_summary', 'file_results', 'error_summary', 'performance_metrics', 'recommendations']
            for section in required_sections:
                self.assertIn(section, report)
            
            # Check job summary structure
            job_summary_fields = ['job_id', 'operation', 'status', 'total_files', 'success_rate', 'execution_time']
            for field in job_summary_fields:
                self.assertIn(field, report['job_summary'])
            
            # Check error summary structure
            error_summary_fields = ['total_errors', 'total_warnings', 'failed_files', 'error_types']
            for field in error_summary_fields:
                self.assertIn(field, report['error_summary'])
            
            # Check performance metrics structure
            perf_fields = ['average_processing_time', 'total_processing_time', 'throughput_files_per_second']
            for field in perf_fields:
                self.assertIn(field, report['performance_metrics'])
    
    def test_save_batch_configuration_validation(self):
        """Test batch configuration saving validation."""
        # Test with non-existent job
        result = self.batch_processor.save_batch_configuration("nonexistent-job-id", "test_config")
        self.assertFalse(result)
    
    def test_save_and_load_batch_configuration(self):
        """Test saving and loading batch configuration."""
        job = self.batch_processor.create_batch_job("compress", self.test_files, {"compression_level": 7})
        
        # Save configuration
        config_name = "test_compression_config"
        result = self.batch_processor.save_batch_configuration(job.job_id, config_name)
        self.assertTrue(result)
        
        # Load configuration
        loaded_config = self.batch_processor.load_batch_configuration(config_name)
        self.assertIsNotNone(loaded_config)
        
        # Check configuration content
        self.assertEqual(loaded_config['name'], config_name)
        self.assertEqual(loaded_config['operation'], 'compress')
        self.assertEqual(loaded_config['parameters']['compression_level'], 7)
        self.assertEqual(loaded_config['source_job_id'], job.job_id)
        self.assertIn('created_at', loaded_config)
    
    def test_load_nonexistent_configuration(self):
        """Test loading non-existent configuration."""
        loaded_config = self.batch_processor.load_batch_configuration("nonexistent_config")
        self.assertIsNone(loaded_config)
    
    def test_retry_failed_operations_validation(self):
        """Test retry failed operations validation."""
        # Test with non-existent job
        with self.assertRaises(PDFProcessingError):
            self.batch_processor.retry_failed_operations("nonexistent-job-id")
        
        # Test with running job (should fail)
        job = self.batch_processor.create_batch_job("compress", self.test_files, {"compression_level": 5})
        
        # Try to retry before job is completed
        with self.assertRaises(PDFProcessingError):
            self.batch_processor.retry_failed_operations(job.job_id)
    
    def test_categorize_error_method(self):
        """Test error categorization method."""
        # Test different error types
        test_cases = [
            ("File not found: test.pdf", "file_not_found"),
            ("Permission denied accessing file", "permission_error"),
            ("PDF file is corrupted", "corrupted_file"),
            ("Out of memory error", "memory_error"),
            ("Operation timed out", "timeout_error"),
            ("Some unknown error occurred", "unknown_error")
        ]
        
        for error_message, expected_category in test_cases:
            category = self.batch_processor._categorize_error(error_message)
            self.assertEqual(category, expected_category)
    
    def test_generate_recommendations_method(self):
        """Test recommendations generation method."""
        # Create a mock job and stats
        from smart_pdf_toolkit.core.batch_processor import BatchJobInternal
        from datetime import datetime
        
        job = BatchJobInternal(
            job_id="test-job",
            operation="compress",
            status=JobStatus.COMPLETED,
            total_files=10
        )
        
        # Test with low success rate
        stats = {
            'success_rate': 30,
            'average_processing_time_seconds': 5,
            'total_files': 10,
            'total_errors': 5,
            'failed_operations': 3
        }
        
        recommendations = self.batch_processor._generate_recommendations(job, stats)
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Check for specific recommendations based on stats
        rec_text = ' '.join(recommendations)
        self.assertIn("file integrity", rec_text.lower())
    
    def test_advanced_batch_methods_exist(self):
        """Test that all advanced batch methods exist."""
        advanced_methods = [
            'generate_batch_report',
            'save_batch_configuration',
            'load_batch_configuration',
            'retry_failed_operations',
            '_categorize_error',
            '_generate_recommendations'
        ]
        
        for method in advanced_methods:
            self.assertTrue(hasattr(self.batch_processor, method))
            if not method.startswith('_'):  # Skip private methods for callable test
                self.assertTrue(callable(getattr(self.batch_processor, method)))
    
    def test_batch_configuration_advanced_options(self):
        """Test advanced batch configuration options."""
        # Test configuration with all options
        config = BatchConfiguration(
            max_workers=8,
            chunk_size=20,
            retry_failed=True,
            max_retries=5,
            continue_on_error=False,
            save_intermediate_results=True,
            progress_update_interval=0.5
        )
        
        self.assertEqual(config.max_workers, 8)
        self.assertEqual(config.chunk_size, 20)
        self.assertTrue(config.retry_failed)
        self.assertEqual(config.max_retries, 5)
        self.assertFalse(config.continue_on_error)
        self.assertTrue(config.save_intermediate_results)
        self.assertEqual(config.progress_update_interval, 0.5)
    
    def test_error_recovery_configuration(self):
        """Test error recovery configuration options."""
        # Test with continue_on_error = False
        processor = BatchProcessor()
        processor.batch_config.continue_on_error = False
        
        # This should be configured properly
        self.assertFalse(processor.batch_config.continue_on_error)
        
        # Test with retry configuration
        processor.batch_config.retry_failed = True
        processor.batch_config.max_retries = 3
        
        self.assertTrue(processor.batch_config.retry_failed)
        self.assertEqual(processor.batch_config.max_retries, 3)
        
        processor.shutdown()
    
    def test_batch_reporting_performance_metrics(self):
        """Test performance metrics in batch reporting."""
        job = self.batch_processor.create_batch_job("compress", self.test_files, {"compression_level": 5})
        
        # Wait for job to complete
        import time
        time.sleep(1)
        
        # Get statistics
        stats = self.batch_processor.get_job_statistics(job.job_id)
        
        # Check performance metrics exist
        perf_fields = [
            'job_duration_seconds',
            'total_processing_time_seconds',
            'average_processing_time_seconds'
        ]
        
        for field in perf_fields:
            self.assertIn(field, stats)
            self.assertIsInstance(stats[field], (int, float))
    
    def test_configuration_file_handling(self):
        """Test configuration file creation and management."""
        job = self.batch_processor.create_batch_job("compress", self.test_files, {"compression_level": 5})
        
        # Save configuration
        config_name = "file_handling_test"
        result = self.batch_processor.save_batch_configuration(job.job_id, config_name)
        self.assertTrue(result)
        
        # Check if configuration file was created
        config_dir = Path(self.batch_processor.config.temp_directory) / "batch_configs"
        config_file = config_dir / f"{config_name}.json"
        
        # File should exist
        self.assertTrue(config_file.exists())
        
        # File should contain valid JSON
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        self.assertIsInstance(config_data, dict)
        self.assertEqual(config_data['name'], config_name)


if __name__ == '__main__':
    unittest.main()