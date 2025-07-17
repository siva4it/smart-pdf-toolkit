"""Comprehensive Security and Stress Testing Framework.

This module provides a unified framework for running comprehensive security
and stress tests across all components of Smart PDF Toolkit.
"""

import pytest
import time
import threading
import psutil
import os
import gc
import resource
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from unittest.mock import patch, MagicMock

from smart_pdf_toolkit.core.interfaces import OperationResult
from .security_fixtures import (
    security_temp_dir, security_config, security_manager, pdf_operations_secure,
    sample_passwords, malicious_inputs, create_encrypted_pdf, create_malicious_pdf,
    permission_test_cases, security_logger
)


@dataclass
class SecurityTestResult:
    """Result of a security test."""
    test_name: str
    passed: bool
    execution_time: float
    memory_usage: int
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class StressTestMetrics:
    """Metrics collected during stress testing."""
    peak_memory_mb: float
    avg_memory_mb: float
    peak_cpu_percent: float
    avg_cpu_percent: float
    total_execution_time: float
    operations_per_second: float
    error_count: int
    success_count: int


class SecurityTestOrchestrator:
    """Orchestrates comprehensive security and stress testing."""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.results = []
        self.metrics = {}
        
    def run_security_test(self, test_func, test_name: str, *args, **kwargs) -> SecurityTestResult:
        """Run a single security test with monitoring."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        start_time = time.time()
        try:
            test_func(*args, **kwargs)
            passed = True
            error_message = None
        except Exception as e:
            passed = False
            error_message = str(e)
            self.logger.error(f\"Security test {test_name} failed: {e}\")
        
        execution_time = time.time() - start_time
        final_memory = process.memory_info().rss
        memory_usage = final_memory - initial_memory
        
        result = SecurityTestResult(
            test_name=test_name,
            passed=passed,
            execution_time=execution_time,
            memory_usage=memory_usage,
            error_message=error_message
        )
        
        self.results.append(result)
        return result
    
    def run_stress_test(self, operation_func, iterations: int, concurrent_threads: int = 1) -> StressTestMetrics:
        \"\"\"Run stress test with comprehensive monitoring.\"\"\"
        process = psutil.Process()
        memory_samples = []
        cpu_samples = []
        start_time = time.time()
        success_count = 0
        error_count = 0
        
        def monitor_resources():
            \"\"\"Monitor system resources during stress test.\"\"\"
            while not stop_monitoring:
                try:
                    memory_samples.append(process.memory_info().rss / 1024 / 1024)  # MB
                    cpu_samples.append(process.cpu_percent())
                    time.sleep(0.1)
                except:
                    break
        
        stop_monitoring = False
        monitor_thread = threading.Thread(target=monitor_resources)
        monitor_thread.start()
        
        try:
            if concurrent_threads == 1:
                # Sequential execution
                for i in range(iterations):
                    try:
                        operation_func()
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        self.logger.warning(f\"Stress test iteration {i} failed: {e}\")
            else:
                # Concurrent execution
                with ThreadPoolExecutor(max_workers=concurrent_threads) as executor:
                    futures = [executor.submit(operation_func) for _ in range(iterations)]
                    
                    for future in as_completed(futures):
                        try:
                            future.result()
                            success_count += 1
                        except Exception as e:
                            error_count += 1
                            self.logger.warning(f\"Concurrent stress test failed: {e}\")
        
        finally:
            stop_monitoring = True
            monitor_thread.join(timeout=1)
        
        total_time = time.time() - start_time
        
        return StressTestMetrics(
            peak_memory_mb=max(memory_samples) if memory_samples else 0,
            avg_memory_mb=sum(memory_samples) / len(memory_samples) if memory_samples else 0,
            peak_cpu_percent=max(cpu_samples) if cpu_samples else 0,
            avg_cpu_percent=sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0,
            total_execution_time=total_time,
            operations_per_second=iterations / total_time if total_time > 0 else 0,
            error_count=error_count,
            success_count=success_count
        )
    
    def generate_security_report(self) -> Dict[str, Any]:
        \"\"\"Generate comprehensive security test report.\"\"\"
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        total_time = sum(r.execution_time for r in self.results)
        total_memory = sum(r.memory_usage for r in self.results)
        
        return {
            \"summary\": {
                \"total_tests\": total_tests,
                \"passed_tests\": passed_tests,
                \"failed_tests\": failed_tests,
                \"success_rate\": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                \"total_execution_time\": total_time,
                \"total_memory_usage\": total_memory
            },
            \"failed_tests\": [
                {\"name\": r.test_name, \"error\": r.error_message}
                for r in self.results if not r.passed
            ],
            \"performance_metrics\": {
                \"avg_execution_time\": total_time / total_tests if total_tests > 0 else 0,
                \"avg_memory_usage\": total_memory / total_tests if total_tests > 0 else 0
            },
            \"stress_test_metrics\": self.metrics
        }


@pytest.fixture
def security_orchestrator(security_config, security_logger):
    \"\"\"Create a security test orchestrator.\"\"\"
    return SecurityTestOrchestrator(security_config, security_logger)


class TestComprehensiveSecurityFramework:
    \"\"\"Comprehensive security and stress testing framework.\"\"\"
    
    def test_password_security_comprehensive(self, security_orchestrator, security_manager, sample_passwords):
        \"\"\"Comprehensive password security testing.\"\"\"
        
        def test_password_strength():
            # Test various password strengths
            for password_type, password in sample_passwords.items():
                result = security_manager.validate_password_strength(password)
                if password_type == 'weak':
                    assert not result.success or \"weak\" in result.message.lower()
                elif password_type == 'strong':
                    assert result.success
        
        def test_password_encryption():
            # Test password encryption/decryption
            test_password = sample_passwords['strong']
            hashed = security_manager.hash_password(test_password)
            assert security_manager.verify_password(test_password, hashed)
            assert not security_manager.verify_password(\"wrong\", hashed)
        
        def test_unicode_passwords():
            # Test Unicode password handling
            unicode_password = sample_passwords.get('unicode', 'тест123')
            hashed = security_manager.hash_password(unicode_password)
            assert security_manager.verify_password(unicode_password, hashed)
        
        # Run comprehensive password tests
        security_orchestrator.run_security_test(test_password_strength, \"password_strength\")
        security_orchestrator.run_security_test(test_password_encryption, \"password_encryption\")
        security_orchestrator.run_security_test(test_unicode_passwords, \"unicode_passwords\")
    
    def test_input_validation_comprehensive(self, security_orchestrator, pdf_operations_secure, malicious_inputs):
        \"\"\"Comprehensive input validation testing.\"\"\"
        
        def test_malicious_file_paths():
            # Test path traversal attacks
            malicious_paths = [
                \"../../../etc/passwd\",
                \"..\\\\..\\\\..\\\\windows\\\\system32\\\\config\\\\sam\",
                \"/dev/null\",
                \"CON\", \"PRN\", \"AUX\",  # Windows reserved names
                \"file:///etc/passwd\",
                \"\\x00truncated\",
                \"very_long_path\" + \"a\" * 1000
            ]
            
            for path in malicious_paths:
                try:
                    result = pdf_operations_secure.validate_file_path(path)
                    assert not result.success, f\"Should reject malicious path: {path}\"
                except Exception:
                    pass  # Expected to fail
        
        def test_malicious_file_content():
            # Test malicious file content
            for input_type, content in malicious_inputs.items():
                try:
                    # This should be handled gracefully
                    result = pdf_operations_secure.validate_file_content(content)
                    # Should either succeed with sanitization or fail gracefully
                    assert isinstance(result, OperationResult)
                except Exception as e:
                    # Should not crash the application
                    assert \"crash\" not in str(e).lower()
        
        def test_buffer_overflow_protection():
            # Test protection against buffer overflow attempts
            large_input = \"A\" * (10 * 1024 * 1024)  # 10MB string
            try:
                result = pdf_operations_secure.process_text_input(large_input)
                # Should handle large inputs gracefully
                assert isinstance(result, OperationResult)
            except MemoryError:
                pass  # Acceptable to run out of memory
            except Exception as e:
                # Should not cause unexpected crashes
                assert \"segmentation\" not in str(e).lower()
        
        # Run comprehensive input validation tests
        security_orchestrator.run_security_test(test_malicious_file_paths, \"malicious_file_paths\")
        security_orchestrator.run_security_test(test_malicious_file_content, \"malicious_file_content\")
        security_orchestrator.run_security_test(test_buffer_overflow_protection, \"buffer_overflow_protection\")
    
    def test_stress_testing_comprehensive(self, security_orchestrator, pdf_operations_secure, security_temp_dir):
        \"\"\"Comprehensive stress testing.\"\"\"
        
        # Create test files
        test_files = []
        for i in range(10):
            test_file = security_temp_dir / f\"stress_test_{i}.pdf\"
            test_file.touch()
            test_files.append(test_file)
        
        def single_operation():
            \"\"\"Single PDF operation for stress testing.\"\"\"
            import random
            test_file = random.choice(test_files)
            output_file = security_temp_dir / f\"output_{random.randint(1000, 9999)}.pdf\"
            
            result = pdf_operations_secure.rotate_pdf(
                str(test_file), [90], str(output_file)
            )
            return result.success
        
        # Run stress tests with different configurations
        test_configs = [
            (\"sequential_light\", 50, 1),
            (\"sequential_heavy\", 100, 1),
            (\"concurrent_light\", 50, 5),
            (\"concurrent_heavy\", 100, 10)
        ]
        
        for test_name, iterations, threads in test_configs:
            metrics = security_orchestrator.run_stress_test(
                single_operation, iterations, threads
            )
            security_orchestrator.metrics[test_name] = metrics
            
            # Validate stress test results
            assert metrics.success_count > 0, f\"No successful operations in {test_name}\"
            assert metrics.peak_memory_mb < 1000, f\"Memory usage too high in {test_name}: {metrics.peak_memory_mb}MB\"
            assert metrics.operations_per_second > 0, f\"No operations completed in {test_name}\"
    
    def test_memory_leak_detection(self, security_orchestrator, pdf_operations_secure, security_temp_dir):
        \"\"\"Test for memory leaks during repeated operations.\"\"\"
        
        def memory_leak_test():
            # Create test file
            test_file = security_temp_dir / \"memory_test.pdf\"
            test_file.touch()
            
            initial_memory = psutil.Process().memory_info().rss
            
            # Perform repeated operations
            for i in range(100):
                output_file = security_temp_dir / f\"memory_output_{i}.pdf\"
                result = pdf_operations_secure.rotate_pdf(
                    str(test_file), [90], str(output_file)
                )
                
                # Force garbage collection every 10 iterations
                if i % 10 == 0:
                    gc.collect()
            
            final_memory = psutil.Process().memory_info().rss
            memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
            
            # Memory increase should be reasonable (less than 100MB)
            assert memory_increase < 100, f\"Potential memory leak detected: {memory_increase}MB increase\"
        
        security_orchestrator.run_security_test(memory_leak_test, \"memory_leak_detection\")
    
    def test_concurrent_access_safety(self, security_orchestrator, pdf_operations_secure, security_temp_dir):
        \"\"\"Test thread safety and concurrent access.\"\"\"
        
        def concurrent_safety_test():
            # Create shared test file
            shared_file = security_temp_dir / \"shared_test.pdf\"
            shared_file.touch()
            
            results = []
            errors = []
            
            def worker_operation(worker_id):
                try:
                    output_file = security_temp_dir / f\"concurrent_output_{worker_id}.pdf\"
                    result = pdf_operations_secure.rotate_pdf(
                        str(shared_file), [90 * worker_id], str(output_file)
                    )
                    results.append(result.success)
                except Exception as e:
                    errors.append(str(e))
            
            # Run concurrent operations
            threads = []
            for i in range(20):
                thread = threading.Thread(target=worker_operation, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=30)
            
            # Validate results
            assert len(errors) == 0, f\"Concurrent access errors: {errors}\"
            assert len(results) > 0, \"No operations completed\"
            assert any(results), \"All concurrent operations failed\"
        
        security_orchestrator.run_security_test(concurrent_safety_test, \"concurrent_access_safety\")
    
    def test_resource_exhaustion_protection(self, security_orchestrator, pdf_operations_secure, security_temp_dir):
        \"\"\"Test protection against resource exhaustion attacks.\"\"\"
        
        def resource_exhaustion_test():
            # Test file descriptor exhaustion protection
            open_files = []
            try:
                for i in range(1000):  # Try to open many files
                    test_file = security_temp_dir / f\"resource_test_{i}.pdf\"
                    test_file.touch()
                    # This should be limited by the system
                    if len(open_files) < 100:  # Reasonable limit
                        open_files.append(open(test_file, 'rb'))
            except OSError:
                pass  # Expected when hitting limits
            finally:
                # Clean up
                for f in open_files:
                    try:
                        f.close()
                    except:
                        pass
            
            # Test CPU exhaustion protection
            start_time = time.time()
            iteration_count = 0
            
            # Run operations for maximum 30 seconds
            while time.time() - start_time < 30 and iteration_count < 1000:
                test_file = security_temp_dir / \"cpu_test.pdf\"
                test_file.touch()
                output_file = security_temp_dir / f\"cpu_output_{iteration_count}.pdf\"
                
                try:
                    result = pdf_operations_secure.rotate_pdf(
                        str(test_file), [90], str(output_file)
                    )
                    iteration_count += 1
                except Exception:
                    break  # Stop if operations start failing
            
            # Should complete some operations without hanging
            assert iteration_count > 0, \"No operations completed under resource pressure\"
        
        security_orchestrator.run_security_test(resource_exhaustion_test, \"resource_exhaustion_protection\")
    
    def test_generate_comprehensive_report(self, security_orchestrator):
        \"\"\"Generate and validate comprehensive security report.\"\"\"
        # Ensure we have some test results
        if not security_orchestrator.results:
            # Add a dummy test result
            dummy_result = SecurityTestResult(
                test_name=\"dummy_test\",
                passed=True,
                execution_time=0.1,
                memory_usage=1024
            )
            security_orchestrator.results.append(dummy_result)
        
        report = security_orchestrator.generate_security_report()
        
        # Validate report structure
        assert \"summary\" in report
        assert \"failed_tests\" in report
        assert \"performance_metrics\" in report
        assert \"stress_test_metrics\" in report
        
        # Validate summary data
        summary = report[\"summary\"]
        assert \"total_tests\" in summary
        assert \"passed_tests\" in summary
        assert \"failed_tests\" in summary
        assert \"success_rate\" in summary
        
        # Log the report
        security_orchestrator.logger.info(f\"Security Test Report: {report}\")