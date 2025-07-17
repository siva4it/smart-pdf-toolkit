"""Comprehensive Stress Testing Framework.

This module provides stress testing capabilities for Smart PDF Toolkit,
including load testing, performance benchmarking, and resource monitoring.
"""

import time
import threading
import psutil
import os
import gc
import statistics
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
import logging
import json
import random

from smart_pdf_toolkit.core.interfaces import OperationResult
from smart_pdf_toolkit.core.config import Config
from smart_pdf_toolkit.core.pdf_operations import PDFOperationsManager
from smart_pdf_toolkit.core.format_converter import FormatConverter
from smart_pdf_toolkit.core.content_extractor import ContentExtractor
from smart_pdf_toolkit.core.security_manager import SecurityManager

logger = logging.getLogger(__name__)


@dataclass
class StressTestConfig:
    """Configuration for stress tests."""
    duration_seconds: int = 60
    concurrent_operations: int = 10
    max_memory_mb: int = 2048
    max_cpu_percent: float = 90.0
    operations_per_second_target: float = 1.0
    ramp_up_seconds: int = 10
    cool_down_seconds: int = 5


@dataclass
class PerformanceMetrics:
    """Performance metrics collected during stress testing."""
    operation_name: str
    start_time: float
    end_time: float
    execution_time: float
    memory_before_mb: float
    memory_after_mb: float
    memory_peak_mb: float
    cpu_percent: float
    success: bool
    error_message: Optional[str] = None
    thread_id: Optional[int] = None
    process_id: Optional[int] = None


@dataclass
class StressTestResults:
    """Results of a stress test."""
    test_name: str
    config: StressTestConfig
    start_time: float
    end_time: float
    total_operations: int
    successful_operations: int
    failed_operations: int
    operations_per_second: float
    peak_memory_mb: float
    avg_memory_mb: float
    peak_cpu_percent: float
    avg_cpu_percent: float
    error_rate: float
    metrics: List[PerformanceMetrics] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class ResourceMonitor:
    """Monitor system resources during stress testing."""
    
    def __init__(self, interval: float = 0.5):
        self.interval = interval
        self.monitoring = False
        self.metrics = []
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start resource monitoring."""
        self.monitoring = True
        self.metrics = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return collected metrics."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        if not self.metrics:
            return {}
        
        memory_values = [m['memory_mb'] for m in self.metrics]
        cpu_values = [m['cpu_percent'] for m in self.metrics]
        
        return {
            'peak_memory_mb': max(memory_values),
            'avg_memory_mb': statistics.mean(memory_values),
            'min_memory_mb': min(memory_values),
            'peak_cpu_percent': max(cpu_values),
            'avg_cpu_percent': statistics.mean(cpu_values),
            'min_cpu_percent': min(cpu_values),
            'sample_count': len(self.metrics),
            'duration_seconds': self.metrics[-1]['timestamp'] - self.metrics[0]['timestamp'] if len(self.metrics) > 1 else 0
        }
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        process = psutil.Process()
        start_time = time.time()
        
        while self.monitoring:
            try:
                memory_info = process.memory_info()
                cpu_percent = process.cpu_percent()
                
                self.metrics.append({
                    'timestamp': time.time() - start_time,
                    'memory_mb': memory_info.rss / 1024 / 1024,
                    'cpu_percent': cpu_percent,
                    'memory_vms_mb': memory_info.vms / 1024 / 1024
                })
                
                time.sleep(self.interval)
            except Exception as e:
                logger.warning(f"Error in resource monitoring: {e}")
                break


class StressTestFramework:
    """Framework for conducting comprehensive stress tests."""
    
    def __init__(self, config: Config):
        self.config = config
        self.pdf_operations = PDFOperationsManager(config)
        self.format_converter = FormatConverter(config)
        self.content_extractor = ContentExtractor(config)
        self.security_manager = SecurityManager(config)
        
        self.resource_monitor = ResourceMonitor()
        self.test_results: List[StressTestResults] = []
    
    def run_load_test(self, operation_func: Callable, test_config: StressTestConfig, 
                     test_name: str = "Load Test") -> StressTestResults:
        """Run a load test with specified configuration.
        
        Args:
            operation_func: Function to execute repeatedly
            test_config: Configuration for the stress test
            test_name: Name of the test
            
        Returns:
            StressTestResults containing test metrics
        """
        logger.info(f"Starting load test: {test_name}")
        
        # Initialize test results
        results = StressTestResults(
            test_name=test_name,
            config=test_config,
            start_time=time.time(),
            end_time=0,
            total_operations=0,
            successful_operations=0,
            failed_operations=0,
            operations_per_second=0,
            peak_memory_mb=0,
            avg_memory_mb=0,
            peak_cpu_percent=0,
            avg_cpu_percent=0,
            error_rate=0
        )
        
        # Start resource monitoring
        self.resource_monitor.start_monitoring()
        
        try:
            # Ramp-up phase
            if test_config.ramp_up_seconds > 0:
                logger.info(f"Ramp-up phase: {test_config.ramp_up_seconds} seconds")
                self._ramp_up_operations(operation_func, test_config)
            
            # Main load test phase
            logger.info(f"Main load test phase: {test_config.duration_seconds} seconds")
            self._execute_load_test(operation_func, test_config, results)
            
            # Cool-down phase
            if test_config.cool_down_seconds > 0:
                logger.info(f"Cool-down phase: {test_config.cool_down_seconds} seconds")
                time.sleep(test_config.cool_down_seconds)
            
        finally:
            # Stop monitoring and collect metrics
            resource_metrics = self.resource_monitor.stop_monitoring()
            results.end_time = time.time()
            
            # Update results with resource metrics
            if resource_metrics:
                results.peak_memory_mb = resource_metrics['peak_memory_mb']
                results.avg_memory_mb = resource_metrics['avg_memory_mb']
                results.peak_cpu_percent = resource_metrics['peak_cpu_percent']
                results.avg_cpu_percent = resource_metrics['avg_cpu_percent']
            
            # Calculate final metrics
            total_time = results.end_time - results.start_time
            results.operations_per_second = results.total_operations / total_time if total_time > 0 else 0
            results.error_rate = (results.failed_operations / results.total_operations * 100) if results.total_operations > 0 else 0
        
        self.test_results.append(results)
        logger.info(f"Load test completed: {test_name}")
        return results
    
    def _ramp_up_operations(self, operation_func: Callable, test_config: StressTestConfig):
        """Gradually increase load during ramp-up phase."""
        ramp_up_steps = 5
        step_duration = test_config.ramp_up_seconds / ramp_up_steps
        
        for step in range(1, ramp_up_steps + 1):
            concurrent_ops = int(test_config.concurrent_operations * step / ramp_up_steps)
            logger.debug(f"Ramp-up step {step}: {concurrent_ops} concurrent operations")
            
            with ThreadPoolExecutor(max_workers=concurrent_ops) as executor:
                futures = []
                for _ in range(concurrent_ops):
                    future = executor.submit(operation_func)
                    futures.append(future)
                
                # Wait for completion or step timeout
                start_time = time.time()
                for future in as_completed(futures, timeout=step_duration):
                    try:
                        future.result()
                    except Exception as e:
                        logger.debug(f"Ramp-up operation error: {e}")
                    
                    if time.time() - start_time >= step_duration:
                        break
    
    def _execute_load_test(self, operation_func: Callable, test_config: StressTestConfig, 
                          results: StressTestResults):
        """Execute the main load test phase."""
        end_time = time.time() + test_config.duration_seconds
        operation_counter = 0
        
        with ThreadPoolExecutor(max_workers=test_config.concurrent_operations) as executor:
            active_futures = set()
            
            while time.time() < end_time:
                # Submit new operations to maintain concurrency level
                while len(active_futures) < test_config.concurrent_operations and time.time() < end_time:
                    future = executor.submit(self._execute_monitored_operation, 
                                           operation_func, operation_counter)
                    active_futures.add(future)
                    operation_counter += 1
                
                # Process completed operations
                completed_futures = set()
                for future in active_futures:
                    if future.done():
                        completed_futures.add(future)
                        try:
                            metrics = future.result()
                            results.metrics.append(metrics)
                            results.total_operations += 1
                            
                            if metrics.success:
                                results.successful_operations += 1
                            else:
                                results.failed_operations += 1
                                if metrics.error_message:
                                    results.errors.append(metrics.error_message)
                                    
                        except Exception as e:
                            results.failed_operations += 1
                            results.errors.append(str(e))
                            logger.error(f"Error processing operation result: {e}")
                
                # Remove completed futures
                active_futures -= completed_futures
                
                # Check resource limits
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                current_cpu = psutil.Process().cpu_percent()
                
                if current_memory > test_config.max_memory_mb:
                    logger.warning(f"Memory limit exceeded: {current_memory:.2f}MB > {test_config.max_memory_mb}MB")
                    break
                
                if current_cpu > test_config.max_cpu_percent:
                    logger.warning(f"CPU limit exceeded: {current_cpu:.2f}% > {test_config.max_cpu_percent}%")
                
                # Brief pause to prevent overwhelming the system
                time.sleep(0.01)
            
            # Wait for remaining operations to complete
            for future in active_futures:
                try:
                    metrics = future.result(timeout=30)
                    results.metrics.append(metrics)
                    results.total_operations += 1
                    
                    if metrics.success:
                        results.successful_operations += 1
                    else:
                        results.failed_operations += 1
                        if metrics.error_message:
                            results.errors.append(metrics.error_message)
                            
                except Exception as e:
                    results.failed_operations += 1
                    results.errors.append(str(e))
    
    def _execute_monitored_operation(self, operation_func: Callable, operation_id: int) -> PerformanceMetrics:
        """Execute an operation with performance monitoring."""
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024
        
        success = False
        error_message = None
        memory_peak = memory_before
        
        try:
            # Execute the operation
            result = operation_func()
            success = True
            
            # Monitor peak memory during operation
            memory_peak = max(memory_peak, psutil.Process().memory_info().rss / 1024 / 1024)
            
        except Exception as e:
            error_message = str(e)
            logger.debug(f"Operation {operation_id} failed: {e}")
        
        end_time = time.time()
        memory_after = psutil.Process().memory_info().rss / 1024 / 1024
        cpu_percent = psutil.Process().cpu_percent()
        
        return PerformanceMetrics(
            operation_name=operation_func.__name__ if hasattr(operation_func, '__name__') else 'unknown',
            start_time=start_time,
            end_time=end_time,
            execution_time=end_time - start_time,
            memory_before_mb=memory_before,
            memory_after_mb=memory_after,
            memory_peak_mb=memory_peak,
            cpu_percent=cpu_percent,
            success=success,
            error_message=error_message,
            thread_id=threading.get_ident(),
            process_id=os.getpid()
        )
    
    def run_benchmark_suite(self) -> Dict[str, StressTestResults]:
        """Run a comprehensive benchmark suite."""
        logger.info("Starting comprehensive benchmark suite")
        
        benchmark_results = {}
        
        # PDF Operations Benchmarks
        benchmark_results['pdf_split'] = self.benchmark_pdf_split()
        benchmark_results['pdf_merge'] = self.benchmark_pdf_merge()
        benchmark_results['pdf_rotate'] = self.benchmark_pdf_rotate()
        
        # Content Extraction Benchmarks
        benchmark_results['text_extraction'] = self.benchmark_text_extraction()
        benchmark_results['image_extraction'] = self.benchmark_image_extraction()
        
        # Format Conversion Benchmarks
        benchmark_results['pdf_to_images'] = self.benchmark_pdf_to_images()
        benchmark_results['images_to_pdf'] = self.benchmark_images_to_pdf()
        
        # Security Operations Benchmarks
        benchmark_results['password_operations'] = self.benchmark_password_operations()
        
        # Concurrent Operations Benchmark
        benchmark_results['concurrent_mixed'] = self.benchmark_concurrent_mixed_operations()
        
        logger.info("Benchmark suite completed")
        return benchmark_results
    
    def benchmark_pdf_split(self) -> StressTestResults:
        """Benchmark PDF split operations."""
        def split_operation():
            test_pdf = self._create_test_pdf()
            output_dir = self.config.temp_dir / f"split_bench_{random.randint(1000, 9999)}"
            output_dir.mkdir(exist_ok=True)
            
            result = self.pdf_operations.split_pdf(
                pdf_path=str(test_pdf),
                output_dir=str(output_dir)
            )
            return result
        
        config = StressTestConfig(
            duration_seconds=30,
            concurrent_operations=5,
            max_memory_mb=1024
        )
        
        return self.run_load_test(split_operation, config, "PDF Split Benchmark")
    
    def benchmark_pdf_merge(self) -> StressTestResults:
        """Benchmark PDF merge operations."""
        def merge_operation():
            test_pdfs = [self._create_test_pdf() for _ in range(3)]
            output_pdf = self.config.temp_dir / f"merged_bench_{random.randint(1000, 9999)}.pdf"
            
            result = self.pdf_operations.merge_pdfs(
                pdf_paths=[str(pdf) for pdf in test_pdfs],
                output_path=str(output_pdf)
            )
            return result
        
        config = StressTestConfig(
            duration_seconds=30,
            concurrent_operations=3,
            max_memory_mb=1024
        )
        
        return self.run_load_test(merge_operation, config, "PDF Merge Benchmark")
    
    def benchmark_pdf_rotate(self) -> StressTestResults:
        """Benchmark PDF rotate operations."""
        def rotate_operation():
            test_pdf = self._create_test_pdf()
            output_pdf = self.config.temp_dir / f"rotated_bench_{random.randint(1000, 9999)}.pdf"
            
            result = self.pdf_operations.rotate_pdf(
                pdf_path=str(test_pdf),
                angles=[90, 180, 270][random.randint(0, 2)],
                output_path=str(output_pdf)
            )
            return result
        
        config = StressTestConfig(
            duration_seconds=30,
            concurrent_operations=5,
            max_memory_mb=1024
        )
        
        return self.run_load_test(rotate_operation, config, "PDF Rotate Benchmark")
    
    def benchmark_text_extraction(self) -> StressTestResults:
        """Benchmark text extraction operations."""
        def extract_text_operation():
            test_pdf = self._create_test_pdf()
            output_txt = self.config.temp_dir / f"text_bench_{random.randint(1000, 9999)}.txt"
            
            result = self.content_extractor.extract_text(
                pdf_path=str(test_pdf),
                output_path=str(output_txt)
            )
            return result
        
        config = StressTestConfig(
            duration_seconds=30,
            concurrent_operations=5,
            max_memory_mb=1024
        )
        
        return self.run_load_test(extract_text_operation, config, "Text Extraction Benchmark")
    
    def benchmark_image_extraction(self) -> StressTestResults:
        """Benchmark image extraction operations."""
        def extract_images_operation():
            test_pdf = self._create_test_pdf()
            output_dir = self.config.temp_dir / f"images_bench_{random.randint(1000, 9999)}"
            output_dir.mkdir(exist_ok=True)
            
            result = self.content_extractor.extract_images(
                pdf_path=str(test_pdf),
                output_dir=str(output_dir)
            )
            return result
        
        config = StressTestConfig(
            duration_seconds=30,
            concurrent_operations=3,
            max_memory_mb=1024
        )
        
        return self.run_load_test(extract_images_operation, config, "Image Extraction Benchmark")
    
    def benchmark_pdf_to_images(self) -> StressTestResults:
        """Benchmark PDF to images conversion."""
        def pdf_to_images_operation():
            test_pdf = self._create_test_pdf()
            output_dir = self.config.temp_dir / f"pdf2img_bench_{random.randint(1000, 9999)}"
            output_dir.mkdir(exist_ok=True)
            
            result = self.format_converter.pdf_to_images(
                pdf_path=str(test_pdf),
                format="PNG",
                quality=90,
                output_dir=str(output_dir)
            )
            return result
        
        config = StressTestConfig(
            duration_seconds=30,
            concurrent_operations=3,
            max_memory_mb=1536
        )
        
        return self.run_load_test(pdf_to_images_operation, config, "PDF to Images Benchmark")
    
    def benchmark_images_to_pdf(self) -> StressTestResults:
        """Benchmark images to PDF conversion."""
        def images_to_pdf_operation():
            test_images = [self._create_test_image() for _ in range(3)]
            output_pdf = self.config.temp_dir / f"img2pdf_bench_{random.randint(1000, 9999)}.pdf"
            
            result = self.format_converter.images_to_pdf(
                image_paths=[str(img) for img in test_images],
                output_path=str(output_pdf)
            )
            return result
        
        config = StressTestConfig(
            duration_seconds=30,
            concurrent_operations=3,
            max_memory_mb=1536
        )
        
        return self.run_load_test(images_to_pdf_operation, config, "Images to PDF Benchmark")
    
    def benchmark_password_operations(self) -> StressTestResults:
        """Benchmark password operations."""
        def password_operation():
            test_pdf = self._create_test_pdf()
            protected_pdf = self.config.temp_dir / f"protected_bench_{random.randint(1000, 9999)}.pdf"
            
            # Add password
            result = self.security_manager.add_password(
                pdf_path=str(test_pdf),
                password="BenchmarkPassword123!",
                output_path=str(protected_pdf)
            )
            
            if result.success:
                # Remove password
                unprotected_pdf = self.config.temp_dir / f"unprotected_bench_{random.randint(1000, 9999)}.pdf"
                result = self.security_manager.remove_password(
                    pdf_path=str(protected_pdf),
                    password="BenchmarkPassword123!",
                    output_path=str(unprotected_pdf)
                )
            
            return result
        
        config = StressTestConfig(
            duration_seconds=30,
            concurrent_operations=3,
            max_memory_mb=1024
        )
        
        return self.run_load_test(password_operation, config, "Password Operations Benchmark")
    
    def benchmark_concurrent_mixed_operations(self) -> StressTestResults:
        """Benchmark mixed concurrent operations."""
        operations = [
            self._create_split_operation,
            self._create_merge_operation,
            self._create_rotate_operation,
            self._create_extract_text_operation,
            self._create_password_operation
        ]
        
        def mixed_operation():
            operation_func = random.choice(operations)
            return operation_func()
        
        config = StressTestConfig(
            duration_seconds=60,
            concurrent_operations=8,
            max_memory_mb=2048
        )
        
        return self.run_load_test(mixed_operation, config, "Mixed Concurrent Operations Benchmark")
    
    def generate_stress_test_report(self, results: List[StressTestResults]) -> Dict[str, Any]:
        """Generate a comprehensive stress test report."""
        if not results:
            return {"error": "No test results provided"}
        
        total_operations = sum(r.total_operations for r in results)
        total_successful = sum(r.successful_operations for r in results)
        total_failed = sum(r.failed_operations for r in results)
        
        # Calculate aggregate metrics
        avg_ops_per_second = statistics.mean([r.operations_per_second for r in results if r.operations_per_second > 0])
        peak_memory = max([r.peak_memory_mb for r in results])
        avg_memory = statistics.mean([r.avg_memory_mb for r in results if r.avg_memory_mb > 0])
        peak_cpu = max([r.peak_cpu_percent for r in results])
        avg_cpu = statistics.mean([r.avg_cpu_percent for r in results if r.avg_cpu_percent > 0])
        
        # Identify performance bottlenecks
        bottlenecks = []
        for result in results:
            if result.error_rate > 10:  # More than 10% error rate
                bottlenecks.append(f"{result.test_name}: High error rate ({result.error_rate:.1f}%)")
            
            if result.operations_per_second < 0.5:  # Less than 0.5 ops/sec
                bottlenecks.append(f"{result.test_name}: Low throughput ({result.operations_per_second:.2f} ops/sec)")
            
            if result.peak_memory_mb > 1500:  # More than 1.5GB
                bottlenecks.append(f"{result.test_name}: High memory usage ({result.peak_memory_mb:.1f}MB)")
        
        return {
            "summary": {
                "total_tests": len(results),
                "total_operations": total_operations,
                "successful_operations": total_successful,
                "failed_operations": total_failed,
                "overall_success_rate": (total_successful / total_operations * 100) if total_operations > 0 else 0,
                "avg_operations_per_second": avg_ops_per_second,
                "peak_memory_mb": peak_memory,
                "avg_memory_mb": avg_memory,
                "peak_cpu_percent": peak_cpu,
                "avg_cpu_percent": avg_cpu
            },
            "test_results": [self._result_to_dict(r) for r in results],
            "performance_bottlenecks": bottlenecks,
            "recommendations": self._generate_performance_recommendations(results),
            "timestamp": time.time()
        }
    
    def _result_to_dict(self, result: StressTestResults) -> Dict[str, Any]:
        """Convert StressTestResults to dictionary."""
        return {
            "test_name": result.test_name,
            "total_operations": result.total_operations,
            "successful_operations": result.successful_operations,
            "failed_operations": result.failed_operations,
            "operations_per_second": result.operations_per_second,
            "peak_memory_mb": result.peak_memory_mb,
            "avg_memory_mb": result.avg_memory_mb,
            "peak_cpu_percent": result.peak_cpu_percent,
            "avg_cpu_percent": result.avg_cpu_percent,
            "error_rate": result.error_rate,
            "duration_seconds": result.end_time - result.start_time,
            "errors": result.errors[:10]  # Limit to first 10 errors
        }
    
    def _generate_performance_recommendations(self, results: List[StressTestResults]) -> List[str]:
        """Generate performance recommendations based on test results."""
        recommendations = []
        
        # Memory usage recommendations
        high_memory_tests = [r for r in results if r.peak_memory_mb > 1000]
        if high_memory_tests:
            recommendations.append(f"Consider memory optimization for {len(high_memory_tests)} tests with high memory usage (>1GB)")
        
        # CPU usage recommendations
        high_cpu_tests = [r for r in results if r.peak_cpu_percent > 80]
        if high_cpu_tests:
            recommendations.append(f"Consider CPU optimization for {len(high_cpu_tests)} tests with high CPU usage (>80%)")
        
        # Error rate recommendations
        high_error_tests = [r for r in results if r.error_rate > 5]
        if high_error_tests:
            recommendations.append(f"Investigate error causes for {len(high_error_tests)} tests with high error rates (>5%)")
        
        # Throughput recommendations
        low_throughput_tests = [r for r in results if r.operations_per_second < 1.0]
        if low_throughput_tests:
            recommendations.append(f"Consider performance optimization for {len(low_throughput_tests)} tests with low throughput (<1 ops/sec)")
        
        return recommendations
    
    # Helper methods for creating test files
    
    def _create_test_pdf(self) -> Path:
        """Create a test PDF file."""
        test_pdf = self.config.temp_dir / f"test_{random.randint(1000, 9999)}.pdf"
        test_pdf.touch()
        return test_pdf
    
    def _create_test_image(self) -> Path:
        """Create a test image file."""
        test_image = self.config.temp_dir / f"test_{random.randint(1000, 9999)}.png"
        test_image.touch()
        return test_image
    
    def _create_split_operation(self):
        """Create a split operation for mixed testing."""
        test_pdf = self._create_test_pdf()
        output_dir = self.config.temp_dir / f"split_mixed_{random.randint(1000, 9999)}"
        output_dir.mkdir(exist_ok=True)
        return self.pdf_operations.split_pdf(str(test_pdf), str(output_dir))
    
    def _create_merge_operation(self):
        """Create a merge operation for mixed testing."""
        test_pdfs = [self._create_test_pdf() for _ in range(2)]
        output_pdf = self.config.temp_dir / f"merged_mixed_{random.randint(1000, 9999)}.pdf"
        return self.pdf_operations.merge_pdfs([str(pdf) for pdf in test_pdfs], str(output_pdf))
    
    def _create_rotate_operation(self):
        """Create a rotate operation for mixed testing."""
        test_pdf = self._create_test_pdf()
        output_pdf = self.config.temp_dir / f"rotated_mixed_{random.randint(1000, 9999)}.pdf"
        return self.pdf_operations.rotate_pdf(str(test_pdf), [90], str(output_pdf))
    
    def _create_extract_text_operation(self):
        """Create a text extraction operation for mixed testing."""
        test_pdf = self._create_test_pdf()
        output_txt = self.config.temp_dir / f"text_mixed_{random.randint(1000, 9999)}.txt"
        return self.content_extractor.extract_text(str(test_pdf), str(output_txt))
    
    def _create_password_operation(self):
        """Create a password operation for mixed testing."""
        test_pdf = self._create_test_pdf()
        output_pdf = self.config.temp_dir / f"protected_mixed_{random.randint(1000, 9999)}.pdf"
        return self.security_manager.add_password(str(test_pdf), "TestPassword123!", str(output_pdf))