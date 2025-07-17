"""Advanced Stress Testing Framework for Smart PDF Toolkit.

This module provides comprehensive stress testing capabilities including
load testing, performance benchmarking, resource exhaustion testing,
and concurrent operation stress testing.
"""

import pytest
import time
import threading
import multiprocessing
import psutil
import gc
import os
import random
import string
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
import statistics

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
    SPIKE = "spike"
    VOLUME = "volume"


class ResourceType(Enum):
    """Types of resources to monitor."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    FILE_HANDLES = "file_handles"
    THREADS = "threads"


@dataclass
class StressTestConfig:
    """Configuration for stress tests."""
    test_type: StressTestType
    duration_seconds: int
    concurrent_operations: int
    target_operations_per_second: Optional[int]
    max_memory_mb: int
    max_cpu_percent: float
    timeout_seconds: int
    ramp_up_seconds: int
    ramp_down_seconds: int


@dataclass
class ResourceMetrics:
    """Resource usage metrics."""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    disk_read_mb: float
    disk_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    file_handles: int
    thread_count: int


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""
    operation_name: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    percentile_95_response_time: float
    percentile_99_response_time: float
    operations_per_second: float
    error_rate: float


@dataclass
class StressTestResult:
    """Result of a stress test."""
    test_name: str
    test_type: StressTestType
    config: StressTestConfig
    start_time: float
    end_time: float
    duration: float
    performance_metrics: PerformanceMetrics
    resource_metrics: List[ResourceMetrics]
    passed: bool
    failure_reason: Optional[str]
    recommendations: List[str]


class ResourceMonitor:
    """Monitors system resource usage during stress tests."""
    
    def __init__(self, interval_seconds: float = 1.0):
        self.interval = interval_seconds
        self.metrics: List[ResourceMetrics] = []
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.process = psutil.Process()
    
    def start_monitoring(self):
        """Start resource monitoring."""
        self.monitoring = True
        self.metrics.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                # Get current metrics
                cpu_percent = self.process.cpu_percent()
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)
                
                # Get I/O stats
                try:
                    io_counters = self.process.io_counters()
                    disk_read_mb = io_counters.read_bytes / (1024 * 1024)
                    disk_write_mb = io_counters.write_bytes / (1024 * 1024)
                except (AttributeError, psutil.AccessDenied):
                    disk_read_mb = disk_write_mb = 0
                
                # Get network stats (system-wide)
                try:
                    net_io = psutil.net_io_counters()
                    network_sent_mb = net_io.bytes_sent / (1024 * 1024)
                    network_recv_mb = net_io.bytes_recv / (1024 * 1024)
                except (AttributeError, psutil.AccessDenied):
                    network_sent_mb = network_recv_mb = 0
                
                # Get file handles and threads
                try:
                    file_handles = self.process.num_fds() if hasattr(self.process, 'num_fds') else len(self.process.open_files())
                except (AttributeError, psutil.AccessDenied):
                    file_handles = 0
                
                try:
                    thread_count = self.process.num_threads()
                except (AttributeError, psutil.AccessDenied):
                    thread_count = 0
                
                # Record metrics
                metrics = ResourceMetrics(
                    timestamp=time.time(),
                    cpu_percent=cpu_percent,
                    memory_mb=memory_mb,
                    disk_read_mb=disk_read_mb,
                    disk_write_mb=disk_write_mb,
                    network_sent_mb=network_sent_mb,
                    network_recv_mb=network_recv_mb,
                    file_handles=file_handles,
                    thread_count=thread_count
                )
                
                self.metrics.append(metrics)
                
            except Exception as e:
                # Continue monitoring even if some metrics fail
                pass
            
            time.sleep(self.interval)
    
    def get_peak_usage(self) -> Dict[str, float]:
        """Get peak resource usage."""
        if not self.metrics:
            return {}
        
        return {
            "peak_cpu_percent": max(m.cpu_percent for m in self.metrics),
            "peak_memory_mb": max(m.memory_mb for m in self.metrics),
            "peak_disk_read_mb": max(m.disk_read_mb for m in self.metrics),
            "peak_disk_write_mb": max(m.disk_write_mb for m in self.metrics),
            "peak_file_handles": max(m.file_handles for m in self.metrics),
            "peak_thread_count": max(m.thread_count for m in self.metrics)
        }
    
    def get_average_usage(self) -> Dict[str, float]:
        """Get average resource usage."""
        if not self.metrics:
            return {}
        
        return {
            "avg_cpu_percent": statistics.mean(m.cpu_percent for m in self.metrics),
            "avg_memory_mb": statistics.mean(m.memory_mb for m in self.metrics),
            "avg_disk_read_mb": statistics.mean(m.disk_read_mb for m in self.metrics),
            "avg_disk_write_mb": statistics.mean(m.disk_write_mb for m in self.metrics),
            "avg_file_handles": statistics.mean(m.file_handles for m in self.metrics),
            "avg_thread_count": statistics.mean(m.thread_count for m in self.metrics)
        }


class StressTestFramework:
    """Advanced stress testing framework."""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.resource_monitor = ResourceMonitor()
        self.test_results: List[StressTestResult] = []
    
    def run_load_test(self, operation_func: Callable, config: StressTestConfig, *args, **kwargs) -> StressTestResult:
        """Run a load test with specified configuration."""
        self.logger.info(f"Starting load test: {config.concurrent_operations} concurrent operations for {config.duration_seconds}s")
        
        start_time = time.time()
        self.resource_monitor.start_monitoring()
        
        # Track operation results
        operation_times = []
        operation_results = []
        
        try:
            # Ramp up phase
            if config.ramp_up_seconds > 0:
                self._ramp_up(operation_func, config, operation_times, operation_results, *args, **kwargs)
            
            # Main load phase
            with ThreadPoolExecutor(max_workers=config.concurrent_operations) as executor:
                end_time = start_time + config.duration_seconds
                futures = []
                
                while time.time() < end_time:
                    if len(futures) < config.concurrent_operations:
                        future = executor.submit(self._timed_operation, operation_func, *args, **kwargs)
                        futures.append(future)
                    
                    # Collect completed operations
                    completed_futures = [f for f in futures if f.done()]
                    for future in completed_futures:
                        try:
                            result, duration = future.result()
                            operation_times.append(duration)
                            operation_results.append(result)
                        except Exception as e:
                            operation_results.append(OperationResult(False, f"Exception: {e}\"))
                        futures.remove(future)
                    
                    # Control operation rate if specified
                    if config.target_operations_per_second:
                        time.sleep(1.0 / config.target_operations_per_second)
                
                # Wait for remaining operations
                for future in as_completed(futures, timeout=config.timeout_seconds):
                    try:
                        result, duration = future.result()
                        operation_times.append(duration)
                        operation_results.append(result)
                    except Exception as e:
                        operation_results.append(OperationResult(False, f\"Exception: {e}\"))
            
            # Ramp down phase
            if config.ramp_down_seconds > 0:
                time.sleep(config.ramp_down_seconds)
            
        except Exception as e:
            self.logger.error(f"Load test failed: {e}")
            return self._create_failed_result("load_test", config, start_time, f"Test execution failed: {e}")
        
        finally:
            self.resource_monitor.stop_monitoring()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics("load_test", operation_times, operation_results)
        
        # Check if test passed
        passed, failure_reason = self._evaluate_test_results(config, performance_metrics, self.resource_monitor.get_peak_usage())
        
        result = StressTestResult(
            test_name="load_test",
            test_type=config.test_type,
            config=config,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            performance_metrics=performance_metrics,
            resource_metrics=self.resource_monitor.metrics,
            passed=passed,
            failure_reason=failure_reason,
            recommendations=self._generate_recommendations(config, performance_metrics, self.resource_monitor.get_peak_usage())
        )
        
        self.test_results.append(result)
        return result
    
    def run_spike_test(self, operation_func: Callable, config: StressTestConfig, *args, **kwargs) -> StressTestResult:
        """Run a spike test with sudden load increases."""
        self.logger.info(f"Starting spike test with {config.concurrent_operations} operations")
        
        start_time = time.time()
        self.resource_monitor.start_monitoring()
        
        operation_times = []
        operation_results = []
        
        try:
            # Normal load phase
            normal_load = max(1, config.concurrent_operations // 4)
            self._run_constant_load(operation_func, normal_load, config.duration_seconds // 3, 
                                  operation_times, operation_results, *args, **kwargs)
            
            # Spike phase - sudden increase
            spike_load = config.concurrent_operations
            self._run_constant_load(operation_func, spike_load, config.duration_seconds // 3,
                                  operation_times, operation_results, *args, **kwargs)
            
            # Recovery phase - back to normal
            self._run_constant_load(operation_func, normal_load, config.duration_seconds // 3,
                                  operation_times, operation_results, *args, **kwargs)
            
        except Exception as e:
            self.logger.error(f"Spike test failed: {e}")
            return self._create_failed_result("spike_test", config, start_time, f"Test execution failed: {e}")
        
        finally:
            self.resource_monitor.stop_monitoring()
        
        end_time = time.time()
        duration = end_time - start_time
        
        performance_metrics = self._calculate_performance_metrics("spike_test", operation_times, operation_results)
        passed, failure_reason = self._evaluate_test_results(config, performance_metrics, self.resource_monitor.get_peak_usage())
        
        result = StressTestResult(
            test_name="spike_test",
            test_type=config.test_type,
            config=config,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            performance_metrics=performance_metrics,
            resource_metrics=self.resource_monitor.metrics,
            passed=passed,
            failure_reason=failure_reason,
            recommendations=self._generate_recommendations(config, performance_metrics, self.resource_monitor.get_peak_usage())
        )
        
        self.test_results.append(result)
        return result
    
    def run_endurance_test(self, operation_func: Callable, config: StressTestConfig, *args, **kwargs) -> StressTestResult:
        """Run an endurance test for extended periods."""
        self.logger.info(f"Starting endurance test for {config.duration_seconds}s")
        
        start_time = time.time()
        self.resource_monitor.start_monitoring()
        
        operation_times = []
        operation_results = []
        
        try:
            # Run constant moderate load for extended period
            moderate_load = max(1, config.concurrent_operations // 2)
            self._run_constant_load(operation_func, moderate_load, config.duration_seconds,
                                  operation_times, operation_results, *args, **kwargs)
            
        except Exception as e:
            self.logger.error(f"Endurance test failed: {e}")
            return self._create_failed_result("endurance_test", config, start_time, f"Test execution failed: {e}")
        
        finally:
            self.resource_monitor.stop_monitoring()
        
        end_time = time.time()
        duration = end_time - start_time
        
        performance_metrics = self._calculate_performance_metrics("endurance_test", operation_times, operation_results)
        passed, failure_reason = self._evaluate_test_results(config, performance_metrics, self.resource_monitor.get_peak_usage())
        
        # Additional checks for endurance tests
        if passed:
            # Check for memory leaks
            memory_metrics = [m.memory_mb for m in self.resource_monitor.metrics]
            if len(memory_metrics) > 10:
                # Check if memory usage is consistently increasing
                first_half_avg = statistics.mean(memory_metrics[:len(memory_metrics)//2])
                second_half_avg = statistics.mean(memory_metrics[len(memory_metrics)//2:])
                memory_increase_percent = ((second_half_avg - first_half_avg) / first_half_avg) * 100
                
                if memory_increase_percent > 20:  # More than 20% increase
                    passed = False
                    failure_reason = f"Potential memory leak detected: {memory_increase_percent:.2f}% memory increase"
        
        result = StressTestResult(
            test_name="endurance_test",
            test_type=config.test_type,
            config=config,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            performance_metrics=performance_metrics,
            resource_metrics=self.resource_monitor.metrics,
            passed=passed,
            failure_reason=failure_reason,
            recommendations=self._generate_recommendations(config, performance_metrics, self.resource_monitor.get_peak_usage())
        )
        
        self.test_results.append(result)
        return result
    
    def run_volume_test(self, operation_func: Callable, config: StressTestConfig, large_data_generator: Callable, *args, **kwargs) -> StressTestResult:
        """Run a volume test with large amounts of data."""
        self.logger.info(f"Starting volume test with large data sets")
        
        start_time = time.time()
        self.resource_monitor.start_monitoring()
        
        operation_times = []
        operation_results = []
        
        try:
            # Generate large test data
            large_data = large_data_generator()
            
            # Process large data with limited concurrency to avoid overwhelming system
            limited_concurrency = min(config.concurrent_operations, 4)
            
            with ThreadPoolExecutor(max_workers=limited_concurrency) as executor:
                futures = []
                
                for data_item in large_data:
                    future = executor.submit(self._timed_operation, operation_func, data_item, *args, **kwargs)
                    futures.append(future)
                
                for future in as_completed(futures, timeout=config.timeout_seconds):
                    try:
                        result, duration = future.result()
                        operation_times.append(duration)
                        operation_results.append(result)
                    except Exception as e:
                        operation_results.append(OperationResult(False, f"Exception: {e}"))
            
        except Exception as e:
            self.logger.error(f"Volume test failed: {e}")
            return self._create_failed_result("volume_test", config, start_time, f"Test execution failed: {e}")
        
        finally:
            self.resource_monitor.stop_monitoring()
        
        end_time = time.time()
        duration = end_time - start_time
        
        performance_metrics = self._calculate_performance_metrics("volume_test", operation_times, operation_results)
        passed, failure_reason = self._evaluate_test_results(config, performance_metrics, self.resource_monitor.get_peak_usage())
        
        result = StressTestResult(
            test_name="volume_test",
            test_type=config.test_type,
            config=config,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            performance_metrics=performance_metrics,
            resource_metrics=self.resource_monitor.metrics,
            passed=passed,
            failure_reason=failure_reason,
            recommendations=self._generate_recommendations(config, performance_metrics, self.resource_monitor.get_peak_usage())
        )
        
        self.test_results.append(result)
        return result
    
    def _ramp_up(self, operation_func: Callable, config: StressTestConfig, operation_times: List, operation_results: List, *args, **kwargs):
        """Gradually increase load during ramp-up phase."""
        ramp_steps = 10
        step_duration = config.ramp_up_seconds / ramp_steps
        
        for step in range(ramp_steps):
            concurrent_ops = int((step + 1) * config.concurrent_operations / ramp_steps)
            self._run_constant_load(operation_func, concurrent_ops, step_duration, 
                                  operation_times, operation_results, *args, **kwargs)
    
    def _run_constant_load(self, operation_func: Callable, concurrent_ops: int, duration: float, 
                          operation_times: List, operation_results: List, *args, **kwargs):
        """Run constant load for specified duration."""
        with ThreadPoolExecutor(max_workers=concurrent_ops) as executor:
            end_time = time.time() + duration
            futures = []
            
            while time.time() < end_time:
                if len(futures) < concurrent_ops:
                    future = executor.submit(self._timed_operation, operation_func, *args, **kwargs)
                    futures.append(future)
                
                # Collect completed operations
                completed_futures = [f for f in futures if f.done()]
                for future in completed_futures:
                    try:
                        result, op_duration = future.result()
                        operation_times.append(op_duration)
                        operation_results.append(result)
                    except Exception as e:
                        operation_results.append(OperationResult(False, f"Exception: {e}"))
                    futures.remove(future)
                
                time.sleep(0.1)  # Small delay to prevent tight loop
            
            # Wait for remaining operations
            for future in as_completed(futures, timeout=30):
                try:
                    result, op_duration = future.result()
                    operation_times.append(op_duration)
                    operation_results.append(result)
                except Exception as e:
                    operation_results.append(OperationResult(False, f"Exception: {e}"))
    
    def _timed_operation(self, operation_func: Callable, *args, **kwargs) -> Tuple[OperationResult, float]:
        """Execute operation and measure execution time."""
        start_time = time.time()
        try:
            result = operation_func(*args, **kwargs)
            duration = time.time() - start_time
            return result, duration
        except Exception as e:
            duration = time.time() - start_time
            return OperationResult(False, f"Operation failed: {e}"), duration
    
    def _calculate_performance_metrics(self, operation_name: str, operation_times: List[float], 
                                     operation_results: List[OperationResult]) -> PerformanceMetrics:
        """Calculate performance metrics from operation results."""
        if not operation_times:
            return PerformanceMetrics(
                operation_name=operation_name,
                total_operations=0,
                successful_operations=0,
                failed_operations=0,
                average_response_time=0,
                min_response_time=0,
                max_response_time=0,
                percentile_95_response_time=0,
                percentile_99_response_time=0,
                operations_per_second=0,
                error_rate=0
            )
        
        total_operations = len(operation_results)
        successful_operations = sum(1 for r in operation_results if r.success)
        failed_operations = total_operations - successful_operations
        
        average_response_time = statistics.mean(operation_times)
        min_response_time = min(operation_times)
        max_response_time = max(operation_times)
        
        # Calculate percentiles
        sorted_times = sorted(operation_times)
        percentile_95_response_time = sorted_times[int(0.95 * len(sorted_times))]
        percentile_99_response_time = sorted_times[int(0.99 * len(sorted_times))]
        
        # Calculate operations per second
        total_time = sum(operation_times)
        operations_per_second = total_operations / total_time if total_time > 0 else 0
        
        error_rate = (failed_operations / total_operations) * 100 if total_operations > 0 else 0
        
        return PerformanceMetrics(
            operation_name=operation_name,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            average_response_time=average_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            percentile_95_response_time=percentile_95_response_time,
            percentile_99_response_time=percentile_99_response_time,
            operations_per_second=operations_per_second,
            error_rate=error_rate
        )
    
    def _evaluate_test_results(self, config: StressTestConfig, performance_metrics: PerformanceMetrics, 
                             peak_usage: Dict[str, float]) -> Tuple[bool, Optional[str]]:
        """Evaluate if test results meet acceptance criteria."""
        # Check error rate
        if performance_metrics.error_rate > 5.0:  # More than 5% error rate
            return False, f"High error rate: {performance_metrics.error_rate:.2f}%"
        
        # Check resource usage
        if peak_usage.get("peak_memory_mb", 0) > config.max_memory_mb:
            return False, f"Memory usage exceeded limit: {peak_usage['peak_memory_mb']:.2f}MB > {config.max_memory_mb}MB"
        
        if peak_usage.get("peak_cpu_percent", 0) > config.max_cpu_percent:
            return False, f"CPU usage exceeded limit: {peak_usage['peak_cpu_percent']:.2f}% > {config.max_cpu_percent}%"
        
        # Check response time
        if performance_metrics.percentile_95_response_time > 30.0:  # More than 30 seconds for 95th percentile
            return False, f"Response time too high: 95th percentile = {performance_metrics.percentile_95_response_time:.2f}s"
        
        # Check operations per second if target is specified
        if config.target_operations_per_second:
            if performance_metrics.operations_per_second < config.target_operations_per_second * 0.8:  # 80% of target
                return False, f"Operations per second below target: {performance_metrics.operations_per_second:.2f} < {config.target_operations_per_second * 0.8:.2f}"
        
        return True, None
    
    def _generate_recommendations(self, config: StressTestConfig, performance_metrics: PerformanceMetrics, 
                                peak_usage: Dict[str, float]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if performance_metrics.error_rate > 1.0:
            recommendations.append("Investigate and fix errors causing operation failures")
        
        if performance_metrics.average_response_time > 10.0:
            recommendations.append("Optimize operation performance to reduce response time")
        
        if peak_usage.get("peak_memory_mb", 0) > config.max_memory_mb * 0.8:
            recommendations.append("Monitor memory usage and consider optimization")
        
        if peak_usage.get("peak_cpu_percent", 0) > config.max_cpu_percent * 0.8:
            recommendations.append("Consider CPU optimization or scaling")
        
        if performance_metrics.operations_per_second < 1.0:
            recommendations.append("Improve operation throughput")
        
        return recommendations
    
    def _create_failed_result(self, test_name: str, config: StressTestConfig, start_time: float, 
                            failure_reason: str) -> StressTestResult:
        """Create a failed test result."""
        return StressTestResult(
            test_name=test_name,
            test_type=config.test_type,
            config=config,
            start_time=start_time,
            end_time=time.time(),
            duration=time.time() - start_time,
            performance_metrics=PerformanceMetrics(
                operation_name=test_name,
                total_operations=0,
                successful_operations=0,
                failed_operations=0,
                average_response_time=0,
                min_response_time=0,
                max_response_time=0,
                percentile_95_response_time=0,
                percentile_99_response_time=0,
                operations_per_second=0,
                error_rate=100
            ),
            resource_metrics=[],
            passed=False,
            failure_reason=failure_reason,
            recommendations=["Fix test execution issues"]
        )
    
    def generate_stress_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive stress test report."""
        if not self.test_results:
            return {"error": "No test results available"}
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.passed)
        failed_tests = total_tests - passed_tests
        
        # Aggregate performance metrics
        all_operations = sum(r.performance_metrics.total_operations for r in self.test_results)
        all_successful = sum(r.performance_metrics.successful_operations for r in self.test_results)
        all_failed = sum(r.performance_metrics.failed_operations for r in self.test_results)
        
        avg_response_times = [r.performance_metrics.average_response_time for r in self.test_results if r.performance_metrics.total_operations > 0]
        overall_avg_response_time = statistics.mean(avg_response_times) if avg_response_times else 0
        
        # Resource usage summary
        peak_memory_usage = max((max(m.memory_mb for m in r.resource_metrics) if r.resource_metrics else 0) for r in self.test_results)
        peak_cpu_usage = max((max(m.cpu_percent for m in r.resource_metrics) if r.resource_metrics else 0) for r in self.test_results)
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "pass_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                "total_operations": all_operations,
                "successful_operations": all_successful,
                "failed_operations": all_failed,
                "overall_success_rate": (all_successful / all_operations) * 100 if all_operations > 0 else 0,
                "overall_avg_response_time": overall_avg_response_time,
                "peak_memory_usage_mb": peak_memory_usage,
                "peak_cpu_usage_percent": peak_cpu_usage
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "test_type": r.test_type.value,
                    "passed": r.passed,
                    "duration": r.duration,
                    "total_operations": r.performance_metrics.total_operations,
                    "operations_per_second": r.performance_metrics.operations_per_second,
                    "error_rate": r.performance_metrics.error_rate,
                    "avg_response_time": r.performance_metrics.average_response_time,
                    "failure_reason": r.failure_reason,
                    "recommendations": r.recommendations
                }
                for r in self.test_results
            ],
            "recommendations": self._generate_overall_recommendations(),
            "performance_baseline": self._establish_performance_baseline()
        }
    
    def _generate_overall_recommendations(self) -> List[str]:
        """Generate overall recommendations based on all test results."""
        recommendations = set()
        
        for result in self.test_results:
            recommendations.update(result.recommendations)
        
        # Add overall recommendations
        failed_tests = [r for r in self.test_results if not r.passed]
        if len(failed_tests) > len(self.test_results) * 0.5:
            recommendations.add("System may not be ready for production load")
        
        high_error_rate_tests = [r for r in self.test_results if r.performance_metrics.error_rate > 5.0]
        if high_error_rate_tests:
            recommendations.add("Address high error rates in operations")
        
        slow_tests = [r for r in self.test_results if r.performance_metrics.average_response_time > 10.0]
        if slow_tests:
            recommendations.add("Optimize performance for better response times")
        
        return list(recommendations)
    
    def _establish_performance_baseline(self) -> Dict[str, float]:
        """Establish performance baseline from test results."""
        if not self.test_results:
            return {}
        
        successful_tests = [r for r in self.test_results if r.passed]
        if not successful_tests:
            return {}
        
        return {
            "baseline_avg_response_time": statistics.mean(r.performance_metrics.average_response_time for r in successful_tests),
            "baseline_operations_per_second": statistics.mean(r.performance_metrics.operations_per_second for r in successful_tests),
            "baseline_error_rate": statistics.mean(r.performance_metrics.error_rate for r in successful_tests),
            "baseline_memory_usage_mb": statistics.mean(max(m.memory_mb for m in r.resource_metrics) if r.resource_metrics else 0 for r in successful_tests),
            "baseline_cpu_usage_percent": statistics.mean(max(m.cpu_percent for m in r.resource_metrics) if r.resource_metrics else 0 for r in successful_tests)
        }


@pytest.fixture
def stress_test_framework(security_config, security_logger):
    """Create stress test framework."""
    return StressTestFramework(security_config, security_logger)


@pytest.fixture
def load_test_config():
    """Create load test configuration."""
    return StressTestConfig(
        test_type=StressTestType.LOAD,
        duration_seconds=60,
        concurrent_operations=10,
        target_operations_per_second=5,
        max_memory_mb=1024,
        max_cpu_percent=80.0,
        timeout_seconds=300,
        ramp_up_seconds=10,
        ramp_down_seconds=5
    )


@pytest.fixture
def spike_test_config():
    """Create spike test configuration."""
    return StressTestConfig(
        test_type=StressTestType.SPIKE,
        duration_seconds=90,
        concurrent_operations=50,
        target_operations_per_second=None,
        max_memory_mb=2048,
        max_cpu_percent=90.0,
        timeout_seconds=600,
        ramp_up_seconds=0,
        ramp_down_seconds=10
    )


@pytest.fixture
def endurance_test_config():
    """Create endurance test configuration."""
    return StressTestConfig(
        test_type=StressTestType.ENDURANCE,
        duration_seconds=300,  # 5 minutes for testing
        concurrent_operations=5,
        target_operations_per_second=2,
        max_memory_mb=1024,
        max_cpu_percent=70.0,
        timeout_seconds=900,
        ramp_up_seconds=30,
        ramp_down_seconds=30
    )


class TestAdvancedStressFramework:
    """Test the advanced stress testing framework."""
    
    def test_load_test_execution(self, stress_test_framework, load_test_config, pdf_operations_secure, security_temp_dir):
        """Test load test execution."""
        def test_operation():
            # Simple test operation
            test_pdf = security_temp_dir / "load_test.pdf"
            test_pdf.touch()
            return pdf_operations_secure.rotate_pdf(str(test_pdf), [90], str(security_temp_dir / "load_output.pdf"))
        
        result = stress_test_framework.run_load_test(test_operation, load_test_config)
        
        assert isinstance(result, StressTestResult)
        assert result.test_name == "load_test"
        assert result.test_type == StressTestType.LOAD
        assert result.duration > 0
        assert isinstance(result.passed, bool)
    
    def test_spike_test_execution(self, stress_test_framework, spike_test_config, pdf_operations_secure, security_temp_dir):
        """Test spike test execution."""
        def test_operation():
            test_pdf = security_temp_dir / "spike_test.pdf"
            test_pdf.touch()
            return pdf_operations_secure.rotate_pdf(str(test_pdf), [90], str(security_temp_dir / "spike_output.pdf"))
        
        result = stress_test_framework.run_spike_test(test_operation, spike_test_config)
        
        assert isinstance(result, StressTestResult)
        assert result.test_name == "spike_test"
        assert result.test_type == StressTestType.SPIKE
    
    @pytest.mark.slow
    def test_endurance_test_execution(self, stress_test_framework, endurance_test_config, pdf_operations_secure, security_temp_dir):
        """Test endurance test execution."""
        def test_operation():
            test_pdf = security_temp_dir / "endurance_test.pdf"
            test_pdf.touch()
            return pdf_operations_secure.rotate_pdf(str(test_pdf), [90], str(security_temp_dir / "endurance_output.pdf"))
        
        result = stress_test_framework.run_endurance_test(test_operation, endurance_test_config)
        
        assert isinstance(result, StressTestResult)
        assert result.test_name == "endurance_test"
        assert result.test_type == StressTestType.ENDURANCE
    
    def test_resource_monitoring(self, stress_test_framework):
        """Test resource monitoring functionality."""
        monitor = ResourceMonitor(interval_seconds=0.1)
        
        monitor.start_monitoring()
        time.sleep(1)  # Monitor for 1 second
        monitor.stop_monitoring()
        
        assert len(monitor.metrics) > 0
        
        peak_usage = monitor.get_peak_usage()
        avg_usage = monitor.get_average_usage()
        
        assert "peak_cpu_percent" in peak_usage
        assert "peak_memory_mb" in peak_usage
        assert "avg_cpu_percent" in avg_usage
        assert "avg_memory_mb" in avg_usage
    
    def test_stress_test_report_generation(self, stress_test_framework, load_test_config, pdf_operations_secure, security_temp_dir):
        """Test stress test report generation."""
        def test_operation():
            test_pdf = security_temp_dir / "report_test.pdf"
            test_pdf.touch()
            return pdf_operations_secure.rotate_pdf(str(test_pdf), [90], str(security_temp_dir / "report_output.pdf"))
        
        # Run a test
        stress_test_framework.run_load_test(test_operation, load_test_config)
        
        # Generate report
        report = stress_test_framework.generate_stress_test_report()
        
        assert "summary" in report
        assert "test_results" in report
        assert "recommendations" in report
        assert "performance_baseline" in report
        
        summary = report["summary"]
        assert "total_tests" in summary
        assert "passed_tests" in summary
        assert "total_operations" in summary
        assert "overall_success_rate" in summary
"