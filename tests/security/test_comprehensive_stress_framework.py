"""Comprehensive Stress Testing Framework.

This module provides comprehensive stress testing capabilities for
Smart PDF Toolkit including load testing, performance testing,
and resource exhaustion testing.
"""

import pytest
import time
import threading
import psutil
import gc
import resource
import multiprocessing
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from smart_pdf_toolkit.core.interfaces import OperationResult
from .security_fixtures import (
    security_temp_dir, security_config, pdf_operations_secure,
    security_logger
)


class StressTestType(Enum):
    """Types of stress tests."""
    LOAD = "load"
    PERFORMANCE = "performance"
    MEMORY = "memory"
    CONCURRENCY = "concurrency"
    ENDURANCE = "endurance"
    RESOURCE_EXHAUSTION = "resource_exhaustion"


@dataclass
class StressTestMetrics:
    """Comprehensive metrics for stress testing."""
    test_type: StressTestType
    test_name: str
    duration: float
    operations_completed: int
    operations_failed: int
    operations_per_second: float
    
    # Memory metrics
    peak_memory_mb: float
    avg_memory_mb: float
    memory_growth_mb: float
    
    # CPU metrics
    peak_cpu_percent: float
    avg_cpu_percent: float
    
    # System metrics
    peak_file_descriptors: int
    peak_threads: int
    
    # Error metrics
    error_types: Dict[str, int] = field(default_factory=dict)
    timeout_count: int = 0
    
    # Performance percentiles
    response_times: List[float] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        total = self.operations_completed + self.operations_failed
        return (self.operations_completed / total * 100) if total > 0 else 0
    
    @property
    def p95_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[index] if index < len(sorted_times) else sorted_times[-1]
    
    @property
    def p99_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(0.99 * len(sorted_times))
        return sorted_times[index] if index < len(sorted_times) else sorted_times[-1]


class SystemMonitor:
    """Monitor system resources during stress testing."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.monitoring = False
        self.samples = []
        self.monitor_thread = None
    
    def start_monitoring(self, interval: float = 0.1):
        """Start monitoring system resources."""
        self.monitoring = True
        self.samples = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return collected metrics."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        
        if not self.samples:
            return {}
        
        memory_samples = [s['memory_mb'] for s in self.samples]
        cpu_samples = [s['cpu_percent'] for s in self.samples]
        fd_samples = [s['file_descriptors'] for s in self.samples]
        thread_samples = [s['threads'] for s in self.samples]
        
        return {
            'peak_memory_mb': max(memory_samples),
            'avg_memory_mb': sum(memory_samples) / len(memory_samples),
            'memory_growth_mb': memory_samples[-1] - memory_samples[0] if len(memory_samples) > 1 else 0,
            'peak_cpu_percent': max(cpu_samples),
            'avg_cpu_percent': sum(cpu_samples) / len(cpu_samples),
            'peak_file_descriptors': max(fd_samples),
            'peak_threads': max(thread_samples),
            'sample_count': len(self.samples)
        }
    
    def _monitor_loop(self, interval: float):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                memory_info = self.process.memory_info()
                cpu_percent = self.process.cpu_percent()
                
                # Get file descriptor count (Unix-like systems)
                try:
                    fd_count = self.process.num_fds()
                except (AttributeError, psutil.AccessDenied):
                    fd_count = 0
                
                # Get thread count
                try:
                    thread_count = self.process.num_threads()
                except psutil.AccessDenied:
                    thread_count = 0
                
                sample = {
                    'timestamp': time.time(),
                    'memory_mb': memory_info.rss / 1024 / 1024,
                    'cpu_percent': cpu_percent,
                    'file_descriptors': fd_count,
                    'threads': thread_count
                }
                
                self.samples.append(sample)
                time.sleep(interval)
                
            except Exception:
                # Continue monitoring even if some metrics fail
                time.sleep(interval)


class StressTestRunner:
    """Comprehensive stress test runner."""
    
    def __init__(self, logger):
        self.logger = logger
        self.monitor = SystemMonitor()
    
    def run_load_test(self, operation_func: Callable, 
                     concurrent_users: int = 10,
                     duration_seconds: int = 60,
                     ramp_up_seconds: int = 10) -> StressTestMetrics:
        """Run load test with gradual ramp-up."""
        self.logger.info(f"Starting load test: {concurrent_users} users, {duration_seconds}s duration")
        
        start_time = time.time()
        self.monitor.start_monitoring()
        
        operations_completed = 0
        operations_failed = 0
        response_times = []
        error_types = {}
        timeout_count = 0
        
        # Gradual ramp-up
        users_per_second = concurrent_users / ramp_up_seconds if ramp_up_seconds > 0 else concurrent_users
        active_threads = []
        
        def worker():
            nonlocal operations_completed, operations_failed, timeout_count
            
            while time.time() - start_time < duration_seconds:
                op_start = time.time()
                try:
                    result = operation_func()
                    op_time = time.time() - op_start
                    response_times.append(op_time)
                    
                    if hasattr(result, 'success') and result.success:
                        operations_completed += 1
                    else:
                        operations_failed += 1
                        
                except Exception as e:
                    operations_failed += 1
                    error_type = type(e).__name__
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                    
                    if "timeout" in str(e).lower():
                        timeout_count += 1
                
                # Small delay to prevent overwhelming
                time.sleep(0.01)
        
        # Ramp up users gradually
        for i in range(concurrent_users):
            if ramp_up_seconds > 0:
                time.sleep(1 / users_per_second)
            
            thread = threading.Thread(target=worker)
            thread.start()
            active_threads.append(thread)
        
        # Wait for test duration
        time.sleep(max(0, duration_seconds - (time.time() - start_time)))
        
        # Wait for threads to complete
        for thread in active_threads:
            thread.join(timeout=5)
        
        total_duration = time.time() - start_time
        system_metrics = self.monitor.stop_monitoring()
        
        return StressTestMetrics(
            test_type=StressTestType.LOAD,
            test_name=f"load_test_{concurrent_users}_users",
            duration=total_duration,
            operations_completed=operations_completed,
            operations_failed=operations_failed,
            operations_per_second=operations_completed / total_duration if total_duration > 0 else 0,
            response_times=response_times,
            error_types=error_types,
            timeout_count=timeout_count,
            **system_metrics
        )
    
    def run_memory_stress_test(self, operation_func: Callable,
                              iterations: int = 1000,
                              memory_limit_mb: int = 500) -> StressTestMetrics:
        """Run memory stress test to detect leaks and excessive usage."""
        self.logger.info(f"Starting memory stress test: {iterations} iterations")
        
        start_time = time.time()
        self.monitor.start_monitoring()
        
        operations_completed = 0
        operations_failed = 0
        response_times = []
        error_types = {}
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        for i in range(iterations):
            op_start = time.time()
            try:
                result = operation_func()
                op_time = time.time() - op_start
                response_times.append(op_time)
                
                if hasattr(result, 'success') and result.success:
                    operations_completed += 1
                else:
                    operations_failed += 1
                    
            except Exception as e:
                operations_failed += 1
                error_type = type(e).__name__
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Check memory usage periodically
            if i % 100 == 0:
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                if current_memory > memory_limit_mb:
                    self.logger.warning(f"Memory limit exceeded: {current_memory:.1f}MB > {memory_limit_mb}MB")
                    break
                
                # Force garbage collection
                gc.collect()
        
        total_duration = time.time() - start_time
        system_metrics = self.monitor.stop_monitoring()
        
        return StressTestMetrics(
            test_type=StressTestType.MEMORY,
            test_name=f"memory_stress_{iterations}_iterations",
            duration=total_duration,
            operations_completed=operations_completed,
            operations_failed=operations_failed,
            operations_per_second=operations_completed / total_duration if total_duration > 0 else 0,
            response_times=response_times,
            error_types=error_types,
            **system_metrics
        )
    
    def run_concurrency_test(self, operation_func: Callable,
                           max_workers: int = 50,
                           operations_per_worker: int = 10) -> StressTestMetrics:
        """Run concurrency test with thread pool."""
        self.logger.info(f"Starting concurrency test: {max_workers} workers, {operations_per_worker} ops each")
        
        start_time = time.time()
        self.monitor.start_monitoring()
        
        operations_completed = 0
        operations_failed = 0
        response_times = []
        error_types = {}
        timeout_count = 0
        
        def worker_task():
            results = []
            for _ in range(operations_per_worker):
                op_start = time.time()
                try:
                    result = operation_func()
                    op_time = time.time() - op_start
                    results.append((True, op_time, None))
                except Exception as e:
                    op_time = time.time() - op_start
                    results.append((False, op_time, e))
            return results
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker_task) for _ in range(max_workers)]
            
            for future in as_completed(futures, timeout=300):  # 5 minute timeout
                try:
                    results = future.result(timeout=10)
                    for success, op_time, error in results:
                        response_times.append(op_time)
                        if success:
                            operations_completed += 1
                        else:
                            operations_failed += 1
                            if error:
                                error_type = type(error).__name__
                                error_types[error_type] = error_types.get(error_type, 0) + 1
                                if "timeout" in str(error).lower():
                                    timeout_count += 1
                                    
                except Exception as e:
                    operations_failed += operations_per_worker
                    error_type = type(e).__name__
                    error_types[error_type] = error_types.get(error_type, 0) + operations_per_worker
        
        total_duration = time.time() - start_time
        system_metrics = self.monitor.stop_monitoring()
        
        return StressTestMetrics(
            test_type=StressTestType.CONCURRENCY,
            test_name=f"concurrency_test_{max_workers}_workers",
            duration=total_duration,
            operations_completed=operations_completed,
            operations_failed=operations_failed,
            operations_per_second=operations_completed / total_duration if total_duration > 0 else 0,
            response_times=response_times,
            error_types=error_types,
            timeout_count=timeout_count,
            **system_metrics
        )
    
    def run_endurance_test(self, operation_func: Callable,
                          duration_hours: float = 1.0,
                          operations_per_minute: int = 60) -> StressTestMetrics:
        """Run endurance test over extended period."""
        duration_seconds = duration_hours * 3600
        self.logger.info(f"Starting endurance test: {duration_hours}h duration, {operations_per_minute} ops/min")
        
        start_time = time.time()
        self.monitor.start_monitoring()
        
        operations_completed = 0
        operations_failed = 0
        response_times = []
        error_types = {}
        
        interval = 60.0 / operations_per_minute  # seconds between operations
        
        while time.time() - start_time < duration_seconds:
            op_start = time.time()
            try:
                result = operation_func()
                op_time = time.time() - op_start
                response_times.append(op_time)
                
                if hasattr(result, 'success') and result.success:
                    operations_completed += 1
                else:
                    operations_failed += 1
                    
            except Exception as e:
                operations_failed += 1
                error_type = type(e).__name__
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Wait for next operation
            elapsed = time.time() - op_start
            if elapsed < interval:
                time.sleep(interval - elapsed)
            
            # Periodic cleanup
            if operations_completed % 100 == 0:
                gc.collect()
        
        total_duration = time.time() - start_time
        system_metrics = self.monitor.stop_monitoring()
        
        return StressTestMetrics(
            test_type=StressTestType.ENDURANCE,
            test_name=f"endurance_test_{duration_hours}h",
            duration=total_duration,
            operations_completed=operations_completed,
            operations_failed=operations_failed,
            operations_per_second=operations_completed / total_duration if total_duration > 0 else 0,
            response_times=response_times,
            error_types=error_types,
            **system_metrics
        )


@pytest.fixture
def stress_test_runner(security_logger):
    """Create a stress test runner."""
    return StressTestRunner(security_logger)


@pytest.fixture
def test_pdf_files(security_temp_dir):
    """Create test PDF files for stress testing."""
    files = []
    for i in range(10):
        pdf_file = security_temp_dir / f"stress_test_{i}.pdf"
        # Create minimal PDF content
        with open(pdf_file, 'wb') as f:
            f.write(b'%PDF-1.4\\n')
            f.write(b'1 0 obj\\n<< /Type /Catalog /Pages 2 0 R >>\\nendobj\\n')
            f.write(b'2 0 obj\\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\\nendobj\\n')
            f.write(b'3 0 obj\\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\\nendobj\\n')
            f.write(b'xref\\n0 4\\n')
            f.write(b'0000000000 65535 f \\n')
            f.write(b'0000000009 00000 n \\n')
            f.write(b'0000000074 00000 n \\n')
            f.write(b'0000000131 00000 n \\n')
            f.write(b'trailer\\n<< /Size 4 /Root 1 0 R >>\\n')
            f.write(b'startxref\\n177\\n%%EOF\\n')
        files.append(pdf_file)
    return files


class TestComprehensiveStressFramework:
    """Comprehensive stress testing framework tests."""
    
    def test_load_stress_test(self, stress_test_runner, pdf_operations_secure, test_pdf_files, security_temp_dir, security_logger):
        """Test load stress with multiple concurrent users."""
        
        def pdf_operation():
            import random
            input_file = random.choice(test_pdf_files)
            output_file = security_temp_dir / f"load_output_{random.randint(1000, 9999)}.pdf"
            
            return pdf_operations_secure.rotate_pdf(
                str(input_file), [90], str(output_file)
            )
        
        # Run load test with moderate settings for CI
        metrics = stress_test_runner.run_load_test(
            operation_func=pdf_operation,
            concurrent_users=5,  # Reduced for CI
            duration_seconds=30,  # Reduced for CI
            ramp_up_seconds=5
        )
        
        # Validate results
        assert metrics.test_type == StressTestType.LOAD
        assert metrics.duration > 0
        assert metrics.operations_completed > 0
        assert metrics.success_rate > 50  # At least 50% success rate
        assert metrics.peak_memory_mb > 0
        
        # Log results
        security_logger.info(f"Load test results:")
        security_logger.info(f"  Operations completed: {metrics.operations_completed}")
        security_logger.info(f"  Operations failed: {metrics.operations_failed}")
        security_logger.info(f"  Success rate: {metrics.success_rate:.1f}%")
        security_logger.info(f"  Operations/sec: {metrics.operations_per_second:.2f}")
        security_logger.info(f"  Peak memory: {metrics.peak_memory_mb:.1f}MB")
        security_logger.info(f"  P95 response time: {metrics.p95_response_time:.3f}s")
    
    def test_memory_stress_test(self, stress_test_runner, pdf_operations_secure, test_pdf_files, security_temp_dir, security_logger):
        """Test memory usage and leak detection."""
        
        def pdf_operation():
            import random
            input_file = random.choice(test_pdf_files)
            output_file = security_temp_dir / f"memory_output_{random.randint(1000, 9999)}.pdf"
            
            return pdf_operations_secure.rotate_pdf(
                str(input_file), [90], str(output_file)
            )
        
        # Run memory stress test
        metrics = stress_test_runner.run_memory_stress_test(
            operation_func=pdf_operation,
            iterations=200,  # Reduced for CI
            memory_limit_mb=300  # 300MB limit
        )
        
        # Validate results
        assert metrics.test_type == StressTestType.MEMORY
        assert metrics.duration > 0
        assert metrics.operations_completed > 0
        assert metrics.peak_memory_mb < 300  # Should stay under limit
        
        # Check for memory leaks (growth should be reasonable)
        if metrics.memory_growth_mb > 100:
            security_logger.warning(f"Potential memory leak detected: {metrics.memory_growth_mb:.1f}MB growth")
        
        # Log results
        security_logger.info(f"Memory stress test results:")
        security_logger.info(f"  Operations completed: {metrics.operations_completed}")
        security_logger.info(f"  Peak memory: {metrics.peak_memory_mb:.1f}MB")
        security_logger.info(f"  Memory growth: {metrics.memory_growth_mb:.1f}MB")
        security_logger.info(f"  Average memory: {metrics.avg_memory_mb:.1f}MB")
    
    def test_concurrency_stress_test(self, stress_test_runner, pdf_operations_secure, test_pdf_files, security_temp_dir, security_logger):
        """Test concurrent access and thread safety."""
        
        def pdf_operation():
            import random
            input_file = random.choice(test_pdf_files)
            output_file = security_temp_dir / f"concurrent_output_{random.randint(1000, 9999)}.pdf"
            
            return pdf_operations_secure.rotate_pdf(
                str(input_file), [90], str(output_file)
            )
        
        # Run concurrency test
        metrics = stress_test_runner.run_concurrency_test(
            operation_func=pdf_operation,
            max_workers=10,  # Reduced for CI
            operations_per_worker=5  # Reduced for CI
        )
        
        # Validate results
        assert metrics.test_type == StressTestType.CONCURRENCY
        assert metrics.duration > 0
        assert metrics.operations_completed > 0
        assert metrics.success_rate > 70  # Higher success rate expected for concurrency
        
        # Check for thread safety issues
        if metrics.error_types:
            security_logger.warning(f"Concurrency errors detected: {metrics.error_types}")
        
        # Log results
        security_logger.info(f"Concurrency stress test results:")
        security_logger.info(f"  Operations completed: {metrics.operations_completed}")
        security_logger.info(f"  Success rate: {metrics.success_rate:.1f}%")
        security_logger.info(f"  Peak threads: {metrics.peak_threads}")
        security_logger.info(f"  Error types: {metrics.error_types}")
    
    def test_endurance_stress_test(self, stress_test_runner, pdf_operations_secure, test_pdf_files, security_temp_dir, security_logger):
        """Test endurance over extended period."""
        
        def pdf_operation():
            import random
            input_file = random.choice(test_pdf_files)
            output_file = security_temp_dir / f"endurance_output_{random.randint(1000, 9999)}.pdf"
            
            return pdf_operations_secure.rotate_pdf(
                str(input_file), [90], str(output_file)
            )
        
        # Run short endurance test for CI (2 minutes)
        metrics = stress_test_runner.run_endurance_test(
            operation_func=pdf_operation,
            duration_hours=0.033,  # 2 minutes
            operations_per_minute=30  # Reduced rate
        )
        
        # Validate results
        assert metrics.test_type == StressTestType.ENDURANCE
        assert metrics.duration > 0
        assert metrics.operations_completed > 0
        assert metrics.success_rate > 80  # High success rate expected for endurance
        
        # Log results
        security_logger.info(f"Endurance stress test results:")
        security_logger.info(f"  Duration: {metrics.duration:.1f}s")
        security_logger.info(f"  Operations completed: {metrics.operations_completed}")
        security_logger.info(f"  Success rate: {metrics.success_rate:.1f}%")
        security_logger.info(f"  Operations/sec: {metrics.operations_per_second:.2f}")
        security_logger.info(f"  Memory growth: {metrics.memory_growth_mb:.1f}MB")
    
    def test_resource_exhaustion_protection(self, pdf_operations_secure, test_pdf_files, security_temp_dir, security_logger):
        """Test protection against resource exhaustion."""
        
        # Test file descriptor exhaustion protection
        open_files = []
        try:
            # Try to open many files simultaneously
            for i in range(100):  # Reasonable limit for testing
                test_file = security_temp_dir / f"resource_test_{i}.pdf"
                test_file.touch()
                try:
                    f = open(test_file, 'rb')
                    open_files.append(f)
                except OSError:
                    # Expected when hitting system limits
                    break
            
            # Should handle resource pressure gracefully
            input_file = test_pdf_files[0]
            output_file = security_temp_dir / "resource_output.pdf"
            
            result = pdf_operations_secure.rotate_pdf(
                str(input_file), [90], str(output_file)
            )
            
            # Should either succeed or fail gracefully
            assert isinstance(result, OperationResult)
            
        finally:
            # Clean up
            for f in open_files:
                try:
                    f.close()
                except:
                    pass
        
        security_logger.info(f"Resource exhaustion test completed: opened {len(open_files)} files")
    
    def test_stress_test_reporting(self, stress_test_runner, security_logger):
        """Test stress test metrics and reporting."""
        
        # Create sample metrics
        metrics = StressTestMetrics(
            test_type=StressTestType.LOAD,
            test_name="sample_test",
            duration=60.0,
            operations_completed=1000,
            operations_failed=50,
            operations_per_second=17.5,
            peak_memory_mb=150.0,
            avg_memory_mb=120.0,
            memory_growth_mb=30.0,
            peak_cpu_percent=85.0,
            avg_cpu_percent=65.0,
            peak_file_descriptors=50,
            peak_threads=10,
            response_times=[0.1, 0.2, 0.15, 0.3, 0.25] * 200,  # Sample response times
            error_types={"TimeoutError": 20, "ValueError": 30},
            timeout_count=20
        )
        
        # Validate metrics calculations
        assert metrics.success_rate == pytest.approx(95.24, rel=0.01)  # 1000/(1000+50)*100
        assert metrics.p95_response_time > 0
        assert metrics.p99_response_time > 0
        assert metrics.p99_response_time >= metrics.p95_response_time
        
        # Log comprehensive metrics
        security_logger.info(f"Stress test metrics validation:")
        security_logger.info(f"  Success rate: {metrics.success_rate:.2f}%")
        security_logger.info(f"  P95 response time: {metrics.p95_response_time:.3f}s")
        security_logger.info(f"  P99 response time: {metrics.p99_response_time:.3f}s")
        security_logger.info(f"  Error breakdown: {metrics.error_types}")