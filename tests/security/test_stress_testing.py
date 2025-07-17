"""Stress testing for Smart PDF Toolkit.

This module contains stress tests for performance, memory usage,
concurrent operations, and resource limits.
"""

import pytest
import time
import threading
import psutil
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

from smart_pdf_toolkit.core.interfaces import OperationResult
from .security_fixtures import (
    security_temp_dir, security_config, pdf_operations_secure,
    large_file_generator, security_logger
)


class TestMemoryStress:
    """Test memory usage and limits under stress conditions."""
    
    def test_large_file_processing(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test processing of large PDF files."""
        # Create a large PDF file (50MB)
        large_pdf = large_file_generator(50, "large_test.pdf")
        output_path = security_temp_dir / "large_output.pdf"
        
        # Monitor memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Process the large file
        start_time = time.time()
        result = pdf_operations_secure.rotate_pdf(
            str(large_pdf), [90], str(output_path)
        )
        processing_time = time.time() - start_time
        
        # Check memory usage after processing
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Should complete within reasonable time and memory limits
        assert processing_time < 300  # 5 minutes max
        assert memory_increase < 500 * 1024 * 1024  # 500MB max increase
        
        # Operation should succeed or fail gracefully
        assert isinstance(result.success, bool)
    
    def test_memory_leak_detection(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test for memory leaks during repeated operations."""
        # Create a medium-sized PDF
        test_pdf = large_file_generator(10, "memory_test.pdf")
        
        process = psutil.Process()
        memory_readings = []
        
        # Perform multiple operations
        for i in range(10):
            output_path = security_temp_dir / f"output_{i}.pdf"
            
            # Record memory before operation
            memory_before = process.memory_info().rss
            
            # Perform operation
            result = pdf_operations_secure.rotate_pdf(
                str(test_pdf), [90], str(output_path)
            )
            
            # Record memory after operation
            memory_after = process.memory_info().rss
            memory_readings.append(memory_after - memory_before)
            
            # Clean up output file
            if output_path.exists():
                output_path.unlink()
        
        # Check for consistent memory usage (no significant leaks)
        avg_memory_increase = sum(memory_readings) / len(memory_readings)
        max_memory_increase = max(memory_readings)
        
        # Memory increase should be reasonable and consistent
        assert avg_memory_increase < 50 * 1024 * 1024  # 50MB average
        assert max_memory_increase < 100 * 1024 * 1024  # 100MB max
    
    def test_out_of_memory_handling(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test handling of out-of-memory conditions."""
        # Create a very large PDF file (if possible)
        try:
            very_large_pdf = large_file_generator(200, "very_large.pdf")  # 200MB
            output_path = security_temp_dir / "oom_output.pdf"
            
            # Try to process it - should handle OOM gracefully
            result = pdf_operations_secure.split_pdf(str(very_large_pdf), str(security_temp_dir))
            
            # Should either succeed or fail gracefully
            assert isinstance(result.success, bool)
            if not result.success:
                assert "memory" in result.message.lower() or "size" in result.message.lower()
        
        except OSError:
            # If we can't create the large file due to disk space, skip
            pytest.skip("Insufficient disk space for OOM test")


class TestConcurrencyStress:
    """Test concurrent operations and thread safety."""
    
    def test_concurrent_pdf_operations(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test concurrent PDF operations."""
        # Create multiple test PDFs
        test_pdfs = []
        for i in range(5):
            pdf_path = large_file_generator(5, f"concurrent_test_{i}.pdf")  # 5MB each
            test_pdfs.append(pdf_path)
        
        def process_pdf(pdf_path, operation_id):
            """Process a single PDF."""
            output_path = security_temp_dir / f"concurrent_output_{operation_id}.pdf"
            result = pdf_operations_secure.rotate_pdf(
                str(pdf_path), [90], str(output_path)
            )
            return result, operation_id
        
        # Run operations concurrently
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(process_pdf, pdf_path, i)
                for i, pdf_path in enumerate(test_pdfs)
            ]
            
            results = []
            for future in as_completed(futures):
                try:
                    result, operation_id = future.result(timeout=60)
                    results.append((result, operation_id))
                except Exception as e:
                    results.append((OperationResult(False, f"Exception: {e}"), -1))
        
        processing_time = time.time() - start_time
        
        # All operations should complete within reasonable time
        assert processing_time < 180  # 3 minutes max
        assert len(results) == 5
        
        # Most operations should succeed (some may fail due to resource constraints)
        successful_operations = sum(1 for result, _ in results if result.success)
        assert successful_operations >= 3  # At least 60% success rate
    
    def test_thread_safety(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test thread safety of PDF operations."""
        test_pdf = large_file_generator(10, "thread_safety_test.pdf")
        
        results = []
        errors = []
        
        def worker_thread(thread_id):
            """Worker thread function."""
            try:
                for i in range(3):  # 3 operations per thread
                    output_path = security_temp_dir / f"thread_{thread_id}_output_{i}.pdf"
                    result = pdf_operations_secure.rotate_pdf(
                        str(test_pdf), [90 * (i + 1)], str(output_path)
                    )
                    results.append((thread_id, i, result))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Create and start multiple threads
        threads = []
        for thread_id in range(3):
            thread = threading.Thread(target=worker_thread, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=120)  # 2 minutes timeout per thread
        
        # Check results
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 9  # 3 threads × 3 operations each
    
    def test_resource_contention(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test behavior under resource contention."""
        # Create multiple PDFs
        test_pdfs = [
            large_file_generator(15, f"contention_test_{i}.pdf")
            for i in range(3)
        ]
        
        def resource_intensive_operation(pdf_path, operation_id):
            """Perform resource-intensive operation."""
            # Multiple operations on the same file
            operations = [
                lambda: pdf_operations_secure.rotate_pdf(
                    str(pdf_path), [90], 
                    str(security_temp_dir / f"rotate_{operation_id}.pdf")
                ),
                lambda: pdf_operations_secure.split_pdf(
                    str(pdf_path), 
                    str(security_temp_dir / f"split_{operation_id}")
                )
            ]
            
            results = []
            for op in operations:
                try:
                    result = op()
                    results.append(result)
                except Exception as e:
                    results.append(OperationResult(False, f"Exception: {e}"))
            
            return results
        
        # Run resource-intensive operations concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(resource_intensive_operation, pdf_path, i)
                for i, pdf_path in enumerate(test_pdfs)
            ]
            
            all_results = []
            for future in as_completed(futures):
                try:
                    results = future.result(timeout=180)  # 3 minutes timeout
                    all_results.extend(results)
                except Exception as e:
                    all_results.append(OperationResult(False, f"Timeout or error: {e}"))
        
        # Should handle resource contention gracefully
        assert len(all_results) > 0
        # At least some operations should succeed
        successful_ops = sum(1 for result in all_results if result.success)
        assert successful_ops >= len(all_results) // 2  # At least 50% success


class TestPerformanceStress:
    """Test performance under various stress conditions."""
    
    def test_batch_processing_performance(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test performance of batch processing operations."""
        # Create multiple PDFs for batch processing
        batch_pdfs = []
        for i in range(10):
            pdf_path = large_file_generator(5, f"batch_test_{i}.pdf")
            batch_pdfs.append(str(pdf_path))
        
        # Test batch merge performance
        merged_output = security_temp_dir / "batch_merged.pdf"
        
        start_time = time.time()
        result = pdf_operations_secure.merge_pdfs(batch_pdfs, str(merged_output))
        merge_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert merge_time < 120  # 2 minutes max
        assert isinstance(result.success, bool)
    
    def test_repeated_operations_performance(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test performance degradation over repeated operations."""
        test_pdf = large_file_generator(10, "repeated_ops_test.pdf")
        
        operation_times = []
        
        # Perform the same operation multiple times
        for i in range(20):
            output_path = security_temp_dir / f"repeated_output_{i}.pdf"
            
            start_time = time.time()
            result = pdf_operations_secure.rotate_pdf(
                str(test_pdf), [90], str(output_path)
            )
            operation_time = time.time() - start_time
            
            operation_times.append(operation_time)
            
            # Clean up to avoid disk space issues
            if output_path.exists():
                output_path.unlink()
        
        # Check for performance degradation
        first_half_avg = sum(operation_times[:10]) / 10
        second_half_avg = sum(operation_times[10:]) / 10
        
        # Performance shouldn't degrade significantly
        assert second_half_avg < first_half_avg * 2  # No more than 2x slower
    
    def test_cpu_intensive_operations(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test CPU-intensive operations under stress."""
        # Create a complex PDF for processing
        complex_pdf = large_file_generator(20, "cpu_intensive_test.pdf")
        
        # Monitor CPU usage
        process = psutil.Process()
        
        # Perform CPU-intensive operation
        start_time = time.time()
        cpu_before = process.cpu_percent()
        
        result = pdf_operations_secure.split_pdf(
            str(complex_pdf), str(security_temp_dir / "cpu_test_split")
        )
        
        processing_time = time.time() - start_time
        cpu_after = process.cpu_percent()
        
        # Should complete within reasonable time
        assert processing_time < 300  # 5 minutes max
        assert isinstance(result.success, bool)


class TestResourceLimits:
    """Test behavior at resource limits."""
    
    def test_file_descriptor_limits(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test behavior when approaching file descriptor limits."""
        # Create many small PDFs
        many_pdfs = []
        try:
            for i in range(100):  # Create many files
                pdf_path = large_file_generator(1, f"fd_test_{i}.pdf")  # 1MB each
                many_pdfs.append(str(pdf_path))
        except OSError:
            # If we hit limits creating files, use what we have
            pass
        
        if len(many_pdfs) > 10:  # Only test if we have enough files
            # Try to merge many files
            merged_output = security_temp_dir / "many_files_merged.pdf"
            
            result = pdf_operations_secure.merge_pdfs(many_pdfs, str(merged_output))
            
            # Should handle many files gracefully
            assert isinstance(result.success, bool)
    
    def test_disk_space_handling(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test handling of low disk space conditions."""
        # Check available disk space
        disk_usage = psutil.disk_usage(str(security_temp_dir))
        available_gb = disk_usage.free / (1024**3)
        
        if available_gb > 1:  # Only test if we have more than 1GB free
            # Try to create a file that might fill available space
            try:
                # Create a large PDF (but not too large to actually fill disk)
                large_pdf = large_file_generator(
                    min(100, int(available_gb * 0.1 * 1024)),  # 10% of available space or 100MB
                    "disk_space_test.pdf"
                )
                
                # Try to process it
                output_path = security_temp_dir / "disk_space_output.pdf"
                result = pdf_operations_secure.rotate_pdf(
                    str(large_pdf), [90], str(output_path)
                )
                
                # Should handle gracefully
                assert isinstance(result.success, bool)
                
            except OSError as e:
                # Expected if we actually run out of space
                assert "space" in str(e).lower() or "disk" in str(e).lower()
    
    def test_timeout_handling(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test handling of operation timeouts."""
        # Create a large PDF that might take a long time to process
        large_pdf = large_file_generator(50, "timeout_test.pdf")
        
        # Mock a timeout scenario
        with patch('time.time', side_effect=[0, 0, 0, 1000]):  # Simulate long processing time
            result = pdf_operations_secure.rotate_pdf(
                str(large_pdf), [90], str(security_temp_dir / "timeout_output.pdf")
            )
            
            # Should handle timeout gracefully
            assert isinstance(result.success, bool)
            if not result.success:
                assert "timeout" in result.message.lower() or "time" in result.message.lower()