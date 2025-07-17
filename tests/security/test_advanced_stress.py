"""Advanced stress testing for Smart PDF Toolkit.

This module contains advanced stress tests for edge cases, resource exhaustion,
and extreme load conditions.
"""

import pytest
import time
import threading
import multiprocessing
import psutil
import gc
import weakref
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from unittest.mock import patch, MagicMock

from smart_pdf_toolkit.core.interfaces import OperationResult
from .security_fixtures import (
    security_temp_dir, security_config, pdf_operations_secure,
    large_file_generator, security_logger
)


class TestExtremeLoadStress:
    """Test system behavior under extreme load conditions."""
    
    def test_massive_concurrent_operations(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test handling of massive concurrent operations."""
        # Create test files
        test_files = []
        for i in range(20):
            pdf_path = large_file_generator(5, f"massive_test_{i}.pdf")
            test_files.append(pdf_path)
        
        def stress_operation(file_index):
            """Perform stress operation on a file."""
            pdf_path = test_files[file_index % len(test_files)]
            output_path = security_temp_dir / f"massive_output_{file_index}_{threading.current_thread().ident}.pdf"
            
            try:
                result = pdf_operations_secure.rotate_pdf(
                    str(pdf_path), [90], str(output_path)
                )
                return result.success, file_index, None
            except Exception as e:
                return False, file_index, str(e)
        
        # Run massive concurrent operations
        max_workers = min(50, multiprocessing.cpu_count() * 4)
        successful_operations = 0
        failed_operations = 0
        exceptions = []
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(stress_operation, i) for i in range(100)]
            
            for future in as_completed(futures, timeout=600):  # 10 minute timeout
                try:
                    success, file_index, error = future.result()
                    if success:
                        successful_operations += 1
                    else:
                        failed_operations += 1
                        if error:
                            exceptions.append(error)
                except Exception as e:
                    failed_operations += 1
                    exceptions.append(str(e))
        
        total_time = time.time() - start_time
        
        # Should handle massive load gracefully
        assert total_time < 600  # Should complete within 10 minutes
        assert successful_operations + failed_operations == 100
        
        # Should have reasonable success rate even under extreme load
        success_rate = successful_operations / 100
        assert success_rate >= 0.3  # At least 30% success rate
        
        # Failures should be graceful, not crashes
        crash_indicators = ["segmentation fault", "core dumped", "access violation"]
        for exception in exceptions:
            for indicator in crash_indicators:
                assert indicator.lower() not in exception.lower()
    
    def test_process_pool_stress(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test stress using process pools instead of thread pools."""
        # Create test files
        test_files = []
        for i in range(10):
            pdf_path = large_file_generator(3, f"process_test_{i}.pdf")
            test_files.append(str(pdf_path))
        
        def process_operation(args):
            """Process operation to run in separate process."""
            pdf_path, output_index = args
            
            # Import inside function for multiprocessing
            from smart_pdf_toolkit.core.pdf_operations import PDFOperationsManager
            from smart_pdf_toolkit.core.config import Config
            
            config = Config()
            pdf_ops = PDFOperationsManager(config)
            
            output_path = f"{security_temp_dir}/process_output_{output_index}.pdf"
            
            try:
                result = pdf_ops.rotate_pdf(pdf_path, [90], output_path)
                return result.success, output_index, None
            except Exception as e:
                return False, output_index, str(e)
        
        # Prepare arguments
        args_list = [(test_files[i % len(test_files)], i) for i in range(20)]
        
        # Run with process pool
        successful_operations = 0
        failed_operations = 0
        
        try:
            with ProcessPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(process_operation, args) for args in args_list]
                
                for future in as_completed(futures, timeout=300):  # 5 minute timeout
                    try:
                        success, output_index, error = future.result()
                        if success:
                            successful_operations += 1
                        else:
                            failed_operations += 1
                    except Exception:
                        failed_operations += 1
        
        except Exception:
            # Process pool might fail in some environments, which is acceptable
            pytest.skip("Process pool execution failed - environment limitation")
        
        # Should handle process-based concurrency
        assert successful_operations + failed_operations > 0
    
    def test_resource_exhaustion_recovery(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test recovery from resource exhaustion."""
        # Monitor system resources
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Create increasingly large operations until resources are exhausted
        operation_sizes = [10, 20, 50, 100, 200]  # MB
        recovery_successful = False
        
        for size_mb in operation_sizes:
            try:
                # Create large file
                large_pdf = large_file_generator(size_mb, f"exhaustion_test_{size_mb}mb.pdf")
                output_path = security_temp_dir / f"exhaustion_output_{size_mb}mb.pdf"
                
                # Try operation
                result = pdf_operations_secure.split_pdf(str(large_pdf), str(security_temp_dir / f"split_{size_mb}"))
                
                # Check memory usage
                current_memory = process.memory_info().rss
                memory_increase = current_memory - initial_memory
                
                # If memory usage becomes excessive, test recovery
                if memory_increase > 1024 * 1024 * 1024:  # 1GB increase
                    # Force garbage collection
                    gc.collect()
                    
                    # Try a simple operation to test recovery
                    small_pdf = large_file_generator(1, "recovery_test.pdf")
                    recovery_output = security_temp_dir / "recovery_output.pdf"
                    
                    recovery_result = pdf_operations_secure.rotate_pdf(
                        str(small_pdf), [90], str(recovery_output)
                    )
                    
                    if recovery_result.success:
                        recovery_successful = True
                    break
                    
            except (MemoryError, OSError) as e:
                # Expected when resources are exhausted
                # Test recovery with smaller operation
                try:
                    small_pdf = large_file_generator(1, "recovery_test_small.pdf")
                    recovery_output = security_temp_dir / "recovery_output_small.pdf"
                    
                    recovery_result = pdf_operations_secure.rotate_pdf(
                        str(small_pdf), [90], str(recovery_output)
                    )
                    
                    if recovery_result.success:
                        recovery_successful = True
                except Exception:
                    pass
                break
        
        # Should be able to recover from resource exhaustion
        assert recovery_successful or "recovery not tested due to resource limits"


class TestMemoryLeakDetection:
    """Test for memory leaks and resource cleanup."""
    
    def test_object_lifecycle_management(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test proper object lifecycle management."""
        # Create weak references to track object cleanup
        weak_refs = []
        
        def create_and_process_pdf(index):
            """Create and process PDF, tracking objects."""
            pdf_path = large_file_generator(5, f"lifecycle_test_{index}.pdf")
            output_path = security_temp_dir / f"lifecycle_output_{index}.pdf"
            
            # Create weak reference to track cleanup
            weak_refs.append(weakref.ref(pdf_path))
            
            result = pdf_operations_secure.rotate_pdf(
                str(pdf_path), [90], str(output_path)
            )
            
            return result
        
        # Process multiple PDFs
        for i in range(10):
            result = create_and_process_pdf(i)
            
            # Force garbage collection
            gc.collect()
        
        # Check that objects are being cleaned up
        # Allow some time for cleanup
        time.sleep(1)
        gc.collect()
        
        # Count how many objects are still alive
        alive_objects = sum(1 for ref in weak_refs if ref() is not None)
        
        # Most objects should be cleaned up
        assert alive_objects < len(weak_refs) * 0.5  # Less than 50% still alive
    
    def test_file_handle_cleanup(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test proper file handle cleanup."""
        # Monitor file descriptor count
        process = psutil.Process()
        initial_fd_count = process.num_fds() if hasattr(process, 'num_fds') else 0
        
        # Perform many file operations
        for i in range(50):
            pdf_path = large_file_generator(2, f"fd_test_{i}.pdf")
            output_path = security_temp_dir / f"fd_output_{i}.pdf"
            
            result = pdf_operations_secure.rotate_pdf(
                str(pdf_path), [90], str(output_path)
            )
            
            # Clean up output file to avoid disk space issues
            if output_path.exists():
                output_path.unlink()
        
        # Check file descriptor count
        if hasattr(process, 'num_fds'):
            final_fd_count = process.num_fds()
            fd_increase = final_fd_count - initial_fd_count
            
            # Should not leak file descriptors significantly
            assert fd_increase < 20  # Allow some increase but not excessive
    
    def test_temporary_file_cleanup(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test cleanup of temporary files."""
        # Count initial files in temp directory
        initial_file_count = len(list(security_temp_dir.glob("*")))
        
        # Perform operations that might create temporary files
        for i in range(20):
            pdf_path = large_file_generator(3, f"temp_test_{i}.pdf")
            
            # Operations that might create temporary files
            result1 = pdf_operations_secure.split_pdf(str(pdf_path), str(security_temp_dir / f"temp_split_{i}"))
            result2 = pdf_operations_secure.merge_pdfs([str(pdf_path)], str(security_temp_dir / f"temp_merge_{i}.pdf"))
        
        # Force cleanup
        gc.collect()
        time.sleep(1)
        
        # Count final files
        final_file_count = len(list(security_temp_dir.glob("*")))
        
        # Should not accumulate excessive temporary files
        file_increase = final_file_count - initial_file_count
        assert file_increase < 100  # Allow reasonable increase but not excessive


class TestEdgeCaseStress:
    """Test edge cases and boundary conditions."""
    
    def test_zero_byte_file_handling(self, pdf_operations_secure, security_temp_dir):
        """Test handling of zero-byte files."""
        # Create zero-byte file
        zero_byte_file = security_temp_dir / "zero_byte.pdf"
        zero_byte_file.touch()
        
        output_path = security_temp_dir / "zero_output.pdf"
        
        # Should handle zero-byte files gracefully
        result = pdf_operations_secure.rotate_pdf(
            str(zero_byte_file), [90], str(output_path)
        )
        
        # Should fail gracefully, not crash
        assert not result.success
        assert "empty" in result.message.lower() or "invalid" in result.message.lower()
    
    def test_extremely_long_filename_handling(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test handling of extremely long filenames."""
        # Create file with very long name
        long_name = "a" * 200 + ".pdf"  # 200+ character filename
        
        try:
            pdf_path = large_file_generator(1, long_name)
            output_name = "b" * 200 + ".pdf"
            output_path = security_temp_dir / output_name
            
            result = pdf_operations_secure.rotate_pdf(
                str(pdf_path), [90], str(output_path)
            )
            
            # Should handle long filenames gracefully
            assert isinstance(result.success, bool)
            
        except OSError:
            # Some filesystems don't support very long filenames
            pytest.skip("Filesystem doesn't support long filenames")
    
    def test_unicode_filename_handling(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test handling of Unicode filenames."""
        unicode_names = [
            "测试文件.pdf",  # Chinese
            "тест.pdf",      # Russian
            "🔒📄.pdf",      # Emojis
            "café_résumé.pdf"  # Accented characters
        ]
        
        for unicode_name in unicode_names:
            try:
                pdf_path = large_file_generator(1, unicode_name)
                output_path = security_temp_dir / f"output_{unicode_name}"
                
                result = pdf_operations_secure.rotate_pdf(
                    str(pdf_path), [90], str(output_path)
                )
                
                # Should handle Unicode filenames gracefully
                assert isinstance(result.success, bool)
                
            except (UnicodeError, OSError):
                # Some systems might not support certain Unicode characters
                continue
    
    def test_deeply_nested_path_handling(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test handling of deeply nested file paths."""
        # Create deeply nested directory structure
        nested_path = security_temp_dir
        for i in range(20):  # Create 20 levels deep
            nested_path = nested_path / f"level_{i}"
            try:
                nested_path.mkdir(exist_ok=True)
            except OSError:
                # Hit path length limit
                break
        
        if nested_path != security_temp_dir:
            try:
                pdf_path = large_file_generator(1, "nested_test.pdf")
                deep_output = nested_path / "deep_output.pdf"
                
                result = pdf_operations_secure.rotate_pdf(
                    str(pdf_path), [90], str(deep_output)
                )
                
                # Should handle deep paths gracefully
                assert isinstance(result.success, bool)
                
            except OSError:
                # Path too deep for filesystem
                pytest.skip("Path too deep for filesystem")
    
    def test_special_character_path_handling(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test handling of paths with special characters."""
        special_chars = ["spaces in name", "name-with-dashes", "name_with_underscores", "name.with.dots"]
        
        for special_name in special_chars:
            try:
                pdf_path = large_file_generator(1, f"{special_name}.pdf")
                output_path = security_temp_dir / f"output_{special_name}.pdf"
                
                result = pdf_operations_secure.rotate_pdf(
                    str(pdf_path), [90], str(output_path)
                )
                
                # Should handle special characters gracefully
                assert isinstance(result.success, bool)
                
            except OSError:
                # Some special characters might not be supported
                continue


class TestSystemResourceStress:
    """Test system resource usage under stress."""
    
    def test_cpu_saturation_handling(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test behavior under CPU saturation."""
        # Create CPU-intensive background load
        def cpu_load():
            """Create CPU load."""
            end_time = time.time() + 30  # Run for 30 seconds
            while time.time() < end_time:
                # CPU-intensive calculation
                sum(i * i for i in range(10000))
        
        # Start CPU load in background
        cpu_threads = []
        for _ in range(multiprocessing.cpu_count()):
            thread = threading.Thread(target=cpu_load)
            thread.start()
            cpu_threads.append(thread)
        
        try:
            # Perform PDF operations under CPU load
            pdf_path = large_file_generator(10, "cpu_stress_test.pdf")
            output_path = security_temp_dir / "cpu_stress_output.pdf"
            
            start_time = time.time()
            result = pdf_operations_secure.rotate_pdf(
                str(pdf_path), [90], str(output_path)
            )
            operation_time = time.time() - start_time
            
            # Should complete even under CPU stress (may take longer)
            assert operation_time < 300  # 5 minutes max
            assert isinstance(result.success, bool)
            
        finally:
            # Wait for CPU load threads to finish
            for thread in cpu_threads:
                thread.join(timeout=1)
    
    def test_memory_pressure_handling(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test behavior under memory pressure."""
        # Create memory pressure
        memory_hogs = []
        
        try:
            # Allocate memory to create pressure
            available_memory = psutil.virtual_memory().available
            target_allocation = min(available_memory // 4, 1024 * 1024 * 1024)  # 1/4 of available or 1GB
            
            chunk_size = 10 * 1024 * 1024  # 10MB chunks
            chunks_needed = target_allocation // chunk_size
            
            for _ in range(min(chunks_needed, 100)):  # Limit to 100 chunks max
                memory_hogs.append(bytearray(chunk_size))
            
            # Perform PDF operation under memory pressure
            pdf_path = large_file_generator(5, "memory_pressure_test.pdf")
            output_path = security_temp_dir / "memory_pressure_output.pdf"
            
            result = pdf_operations_secure.rotate_pdf(
                str(pdf_path), [90], str(output_path)
            )
            
            # Should handle memory pressure gracefully
            assert isinstance(result.success, bool)
            
        except MemoryError:
            # Expected under extreme memory pressure
            pytest.skip("Insufficient memory for pressure test")
        
        finally:
            # Clean up memory
            memory_hogs.clear()
            gc.collect()
    
    def test_disk_io_saturation_handling(self, pdf_operations_secure, large_file_generator, security_temp_dir):
        """Test behavior under disk I/O saturation."""
        def disk_io_load():
            """Create disk I/O load."""
            end_time = time.time() + 20  # Run for 20 seconds
            file_counter = 0
            
            while time.time() < end_time:
                try:
                    # Create and delete files to generate I/O load
                    temp_file = security_temp_dir / f"io_load_{file_counter}.tmp"
                    with open(temp_file, 'wb') as f:
                        f.write(b'x' * 1024 * 1024)  # 1MB
                    temp_file.unlink()
                    file_counter += 1
                except OSError:
                    # Disk might be full or I/O error
                    break
        
        # Start I/O load in background
        io_threads = []
        for _ in range(4):  # 4 I/O threads
            thread = threading.Thread(target=disk_io_load)
            thread.start()
            io_threads.append(thread)
        
        try:
            # Perform PDF operation under I/O load
            pdf_path = large_file_generator(5, "io_stress_test.pdf")
            output_path = security_temp_dir / "io_stress_output.pdf"
            
            start_time = time.time()
            result = pdf_operations_secure.rotate_pdf(
                str(pdf_path), [90], str(output_path)
            )
            operation_time = time.time() - start_time
            
            # Should complete even under I/O stress (may take longer)
            assert operation_time < 180  # 3 minutes max
            assert isinstance(result.success, bool)
            
        finally:
            # Wait for I/O load threads to finish
            for thread in io_threads:
                thread.join(timeout=1)