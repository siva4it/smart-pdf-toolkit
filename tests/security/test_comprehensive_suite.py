"""Comprehensive Security and Stress Test Suite.

This module provides pytest-compatible tests for comprehensive security
and stress testing of Smart PDF Toolkit.
"""

import pytest
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List

from smart_pdf_toolkit.core.config import Config
from .comprehensive_security_framework import SecurityTestOrchestrator
from .stress_testing_framework import StressTestFramework, StressTestConfig
from .comprehensive_test_runner import ComprehensiveTestRunner


class TestComprehensiveSecuritySuite:
    """Comprehensive security test suite."""
    
    @pytest.fixture(scope="class")
    def test_config(self):
        """Create test configuration."""
        config = Config()
        config.temp_dir = Path(tempfile.mkdtemp(prefix="security_tests_"))
        config.output_dir = config.temp_dir / "output"
        config.output_dir.mkdir(exist_ok=True)
        yield config
        
        # Cleanup
        try:
            shutil.rmtree(config.temp_dir)
        except Exception:
            pass
    
    @pytest.fixture(scope="class")
    def security_orchestrator(self, test_config):
        """Create security test orchestrator."""
        return SecurityTestOrchestrator(test_config)
    
    def test_password_security_suite(self, security_orchestrator):
        """Test password security test suite."""
        results = security_orchestrator.run_comprehensive_tests(['password_security'])
        
        assert 'password_security' in results['suite_results']
        suite_result = results['suite_results']['password_security']
        
        # Check that tests were executed
        assert suite_result['passed'] + suite_result['failed'] > 0
        
        # Check for critical password security failures
        critical_failures = [
            test for test in suite_result['tests'] 
            if not test.passed and test.severity == 'critical'
        ]
        
        # Should have no critical password security failures
        assert len(critical_failures) == 0, f"Critical password security failures: {critical_failures}"
    
    def test_input_validation_suite(self, security_orchestrator):
        """Test input validation test suite."""
        results = security_orchestrator.run_comprehensive_tests(['input_validation'])
        
        assert 'input_validation' in results['suite_results']
        suite_result = results['suite_results']['input_validation']
        
        # Check that tests were executed
        assert suite_result['passed'] + suite_result['failed'] > 0
        
        # Input validation should catch most malicious inputs
        success_rate = (suite_result['passed'] / (suite_result['passed'] + suite_result['failed'])) * 100
        assert success_rate >= 80, f"Input validation success rate too low: {success_rate}%"
    
    def test_file_handling_security_suite(self, security_orchestrator):
        """Test file handling security test suite."""
        results = security_orchestrator.run_comprehensive_tests(['file_handling'])
        
        assert 'file_handling' in results['suite_results']
        suite_result = results['suite_results']['file_handling']
        
        # Check that tests were executed
        assert suite_result['passed'] + suite_result['failed'] > 0
        
        # File handling should be secure
        critical_failures = [
            test for test in suite_result['tests'] 
            if not test.passed and test.severity == 'critical'
        ]
        
        # Should have minimal critical file handling failures
        assert len(critical_failures) <= 1, f"Too many critical file handling failures: {critical_failures}"
    
    def test_memory_stress_suite(self, security_orchestrator):
        """Test memory stress test suite."""
        results = security_orchestrator.run_comprehensive_tests(['memory_stress'])
        
        assert 'memory_stress' in results['suite_results']
        suite_result = results['suite_results']['memory_stress']
        
        # Check that tests were executed
        assert suite_result['passed'] + suite_result['failed'] > 0
        
        # Memory usage should be reasonable
        memory_usage = suite_result['memory_usage']
        assert memory_usage['delta_mb'] < 1000, f"Excessive memory usage: {memory_usage['delta_mb']}MB"
    
    def test_concurrent_stress_suite(self, security_orchestrator):
        """Test concurrent operations stress test suite."""
        results = security_orchestrator.run_comprehensive_tests(['concurrent_stress'])
        
        assert 'concurrent_stress' in results['suite_results']
        suite_result = results['suite_results']['concurrent_stress']
        
        # Check that tests were executed
        assert suite_result['passed'] + suite_result['failed'] > 0
        
        # Concurrent operations should be stable
        success_rate = (suite_result['passed'] / (suite_result['passed'] + suite_result['failed'])) * 100
        assert success_rate >= 70, f"Concurrent operations success rate too low: {success_rate}%"
    
    def test_comprehensive_security_report(self, security_orchestrator):
        """Test comprehensive security report generation."""
        results = security_orchestrator.run_comprehensive_tests()
        
        # Check report structure
        assert 'summary' in results
        assert 'failures_by_severity' in results
        assert 'suite_results' in results
        assert 'recommendations' in results
        
        # Check summary metrics
        summary = results['summary']
        assert 'total_tests' in summary
        assert 'passed' in summary
        assert 'failed' in summary
        assert 'success_rate' in summary
        
        # Success rate should be reasonable
        assert summary['success_rate'] >= 60, f"Overall success rate too low: {summary['success_rate']}%"


class TestComprehensiveStressSuite:
    """Comprehensive stress test suite."""
    
    @pytest.fixture(scope="class")
    def test_config(self):
        """Create test configuration."""
        config = Config()
        config.temp_dir = Path(tempfile.mkdtemp(prefix="stress_tests_"))
        config.output_dir = config.temp_dir / "output"
        config.output_dir.mkdir(exist_ok=True)
        yield config
        
        # Cleanup
        try:
            shutil.rmtree(config.temp_dir)
        except Exception:
            pass
    
    @pytest.fixture(scope="class")
    def stress_framework(self, test_config):
        """Create stress test framework."""
        return StressTestFramework(test_config)
    
    def test_light_load_stress(self, stress_framework):
        """Test light load stress testing."""
        config = StressTestConfig(
            duration_seconds=10,
            concurrent_operations=2,
            max_memory_mb=512,
            operations_per_second_target=1.0
        )
        
        def simple_operation():
            # Simple operation for testing
            test_pdf = stress_framework.config.temp_dir / "light_test.pdf"
            test_pdf.touch()
            return stress_framework.pdf_operations.split_pdf(
                pdf_path=str(test_pdf),
                output_dir=str(stress_framework.config.temp_dir / "light_split")
            )
        
        result = stress_framework.run_load_test(simple_operation, config, "Light Load Test")
        
        # Check basic metrics
        assert result.total_operations > 0
        assert result.operations_per_second > 0
        assert result.peak_memory_mb < config.max_memory_mb
        
        # Success rate should be high for light load
        success_rate = (result.successful_operations / result.total_operations) * 100
        assert success_rate >= 80, f"Light load success rate too low: {success_rate}%"
    
    def test_medium_load_stress(self, stress_framework):
        """Test medium load stress testing."""
        config = StressTestConfig(
            duration_seconds=15,
            concurrent_operations=5,
            max_memory_mb=1024,
            operations_per_second_target=0.8
        )
        
        def medium_operation():
            # Medium complexity operation
            test_pdfs = []
            for i in range(2):
                test_pdf = stress_framework.config.temp_dir / f"medium_test_{i}.pdf"
                test_pdf.touch()
                test_pdfs.append(test_pdf)
            
            output_pdf = stress_framework.config.temp_dir / "medium_merged.pdf"
            return stress_framework.pdf_operations.merge_pdfs(
                pdf_paths=[str(pdf) for pdf in test_pdfs],
                output_path=str(output_pdf)
            )
        
        result = stress_framework.run_load_test(medium_operation, config, "Medium Load Test")
        
        # Check metrics
        assert result.total_operations > 0
        assert result.peak_memory_mb < config.max_memory_mb
        
        # Success rate should be reasonable for medium load
        success_rate = (result.successful_operations / result.total_operations) * 100
        assert success_rate >= 70, f"Medium load success rate too low: {success_rate}%"
    
    def test_memory_monitoring(self, stress_framework):
        """Test memory monitoring during stress tests."""
        config = StressTestConfig(
            duration_seconds=10,
            concurrent_operations=3,
            max_memory_mb=512
        )
        
        def memory_intensive_operation():
            # Operation that uses some memory
            test_pdf = stress_framework.config.temp_dir / "memory_test.pdf"
            test_pdf.touch()
            
            # Create some data in memory
            data = "A" * 1000000  # 1MB of data
            
            return stress_framework.content_extractor.extract_text(
                pdf_path=str(test_pdf),
                output_path=str(stress_framework.config.temp_dir / "memory_text.txt")
            )
        
        result = stress_framework.run_load_test(memory_intensive_operation, config, "Memory Monitoring Test")
        
        # Check that memory was monitored
        assert result.peak_memory_mb > 0
        assert result.avg_memory_mb > 0
        assert result.peak_memory_mb >= result.avg_memory_mb
    
    def test_concurrent_operations_stability(self, stress_framework):
        """Test stability of concurrent operations."""
        config = StressTestConfig(
            duration_seconds=20,
            concurrent_operations=8,
            max_memory_mb=1024
        )
        
        operations = [
            lambda: self._create_split_op(stress_framework),
            lambda: self._create_merge_op(stress_framework),
            lambda: self._create_rotate_op(stress_framework),
            lambda: self._create_extract_op(stress_framework)
        ]
        
        import random
        def mixed_operation():
            return random.choice(operations)()
        
        result = stress_framework.run_load_test(mixed_operation, config, "Concurrent Stability Test")
        
        # Check stability metrics
        assert result.total_operations > 0
        
        # Error rate should be acceptable
        error_rate = (result.failed_operations / result.total_operations) * 100
        assert error_rate <= 30, f"Concurrent operations error rate too high: {error_rate}%"
    
    def test_benchmark_suite_execution(self, stress_framework):
        """Test benchmark suite execution."""
        # Run a subset of benchmarks for testing
        benchmark_results = {}
        
        # Test PDF split benchmark
        benchmark_results['pdf_split'] = stress_framework.benchmark_pdf_split()
        
        # Check benchmark results
        assert 'pdf_split' in benchmark_results
        split_result = benchmark_results['pdf_split']
        
        assert split_result.total_operations > 0
        assert split_result.operations_per_second > 0
        assert split_result.peak_memory_mb > 0
    
    def test_stress_test_report_generation(self, stress_framework):
        """Test stress test report generation."""
        # Run a few quick stress tests
        config = StressTestConfig(duration_seconds=5, concurrent_operations=2)
        
        results = []
        for i in range(2):
            def test_op():
                test_pdf = stress_framework.config.temp_dir / f"report_test_{i}.pdf"
                test_pdf.touch()
                return stress_framework.pdf_operations.split_pdf(
                    str(test_pdf), str(stress_framework.config.temp_dir / f"report_split_{i}")
                )
            
            result = stress_framework.run_load_test(test_op, config, f"Report Test {i}")
            results.append(result)
        
        # Generate report
        report = stress_framework.generate_stress_test_report(results)
        
        # Check report structure
        assert 'summary' in report
        assert 'test_results' in report
        assert 'performance_bottlenecks' in report
        assert 'recommendations' in report
        
        # Check summary metrics
        summary = report['summary']
        assert 'total_tests' in summary
        assert 'total_operations' in summary
        assert 'overall_success_rate' in summary
    
    # Helper methods
    
    def _create_split_op(self, framework):
        """Create a split operation."""
        test_pdf = framework.config.temp_dir / "concurrent_split.pdf"
        test_pdf.touch()
        return framework.pdf_operations.split_pdf(
            str(test_pdf), str(framework.config.temp_dir / "concurrent_split_out")
        )
    
    def _create_merge_op(self, framework):
        """Create a merge operation."""
        test_pdfs = []
        for i in range(2):
            test_pdf = framework.config.temp_dir / f"concurrent_merge_{i}.pdf"
            test_pdf.touch()
            test_pdfs.append(test_pdf)
        
        return framework.pdf_operations.merge_pdfs(
            [str(pdf) for pdf in test_pdfs],
            str(framework.config.temp_dir / "concurrent_merged.pdf")
        )
    
    def _create_rotate_op(self, framework):
        """Create a rotate operation."""
        test_pdf = framework.config.temp_dir / "concurrent_rotate.pdf"
        test_pdf.touch()
        return framework.pdf_operations.rotate_pdf(
            str(test_pdf), [90], str(framework.config.temp_dir / "concurrent_rotated.pdf")
        )
    
    def _create_extract_op(self, framework):
        """Create an extract operation."""
        test_pdf = framework.config.temp_dir / "concurrent_extract.pdf"
        test_pdf.touch()
        return framework.content_extractor.extract_text(
            str(test_pdf), str(framework.config.temp_dir / "concurrent_text.txt")
        )


class TestComprehensiveIntegration:
    """Integration tests for comprehensive testing framework."""
    
    @pytest.fixture(scope="class")
    def test_config(self):
        """Create test configuration."""
        config = Config()
        config.temp_dir = Path(tempfile.mkdtemp(prefix="integration_tests_"))
        config.output_dir = config.temp_dir / "output"
        config.output_dir.mkdir(exist_ok=True)
        yield config
        
        # Cleanup
        try:
            shutil.rmtree(config.temp_dir)
        except Exception:
            pass
    
    @pytest.fixture(scope="class")
    def test_runner(self, test_config):
        """Create comprehensive test runner."""
        return ComprehensiveTestRunner(test_config, "INFO")
    
    def test_security_and_stress_integration(self, test_runner):
        """Test integration of security and stress testing."""
        # Run both security and stress tests
        results = test_runner.run_all_tests(['security', 'stress'])
        
        # Check that both test types were executed
        assert 'security' in results['results']
        assert 'stress' in results['results']
        
        # Check comprehensive report generation
        assert 'comprehensive_report' in results
        report = results['comprehensive_report']
        
        assert 'executive_summary' in report
        assert 'security_analysis' in report
        assert 'performance_analysis' in report
        assert 'risk_assessment' in report
        assert 'compliance_status' in report
    
    def test_executive_summary_generation(self, test_runner):
        """Test executive summary generation."""
        # Run a quick test suite
        results = test_runner.run_all_tests(['security'])
        
        executive_summary = results['comprehensive_report']['executive_summary']
        
        # Check required fields
        assert 'overall_status' in executive_summary
        assert 'performance_score' in executive_summary
        assert 'critical_issues' in executive_summary
        assert 'high_issues' in executive_summary
        assert 'medium_issues' in executive_summary
        
        # Performance score should be between 0 and 100
        assert 0 <= executive_summary['performance_score'] <= 100
    
    def test_risk_assessment_generation(self, test_runner):
        """Test risk assessment generation."""
        results = test_runner.run_all_tests(['security'])
        
        risk_assessment = results['comprehensive_report']['risk_assessment']
        
        # Check required fields
        assert 'overall_risk_level' in risk_assessment
        assert 'security_risk' in risk_assessment
        assert 'performance_risk' in risk_assessment
        assert 'risk_factors' in risk_assessment
        
        # Risk levels should be valid
        valid_risk_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        assert risk_assessment['overall_risk_level'] in valid_risk_levels
        assert risk_assessment['security_risk'] in valid_risk_levels
        assert risk_assessment['performance_risk'] in valid_risk_levels
    
    def test_compliance_status_generation(self, test_runner):
        """Test compliance status generation."""
        results = test_runner.run_all_tests(['security'])
        
        compliance_status = results['comprehensive_report']['compliance_status']
        
        # Check required fields
        assert 'overall_compliance' in compliance_status
        assert 'security_compliance' in compliance_status
        assert 'performance_compliance' in compliance_status
        assert 'compliance_issues' in compliance_status
        
        # Compliance status should be valid
        valid_compliance = ['PASS', 'FAIL']
        assert compliance_status['overall_compliance'] in valid_compliance
        assert compliance_status['security_compliance'] in valid_compliance
        assert compliance_status['performance_compliance'] in valid_compliance
    
    def test_recommendations_generation(self, test_runner):
        """Test recommendations generation."""
        results = test_runner.run_all_tests(['security'])
        
        recommendations = results['comprehensive_report']['recommendations']
        
        # Should have some recommendations
        assert isinstance(recommendations, list)
        
        # Each recommendation should be a string
        for rec in recommendations:
            assert isinstance(rec, str)
            assert len(rec) > 0
    
    @pytest.mark.slow
    def test_full_comprehensive_suite(self, test_runner):
        """Test full comprehensive test suite (marked as slow)."""
        # Run all test types
        results = test_runner.run_all_tests(['security', 'stress', 'benchmark'])
        
        # Check that all test types were executed
        assert 'security' in results['results']
        assert 'stress' in results['results']
        assert 'benchmark' in results['results']
        
        # Check overall execution
        assert results['total_duration'] > 0
        assert 'comprehensive_report' in results
        
        # Check that the test suite provides actionable insights
        report = results['comprehensive_report']
        assert len(report['recommendations']) > 0
        
        # Executive summary should provide clear status
        executive_summary = report['executive_summary']
        assert executive_summary['overall_status'] in ['PASS', 'MEDIUM_RISK', 'HIGH_RISK', 'CRITICAL']


# Pytest markers for different test categories
pytestmark = [
    pytest.mark.security,
    pytest.mark.stress,
    pytest.mark.integration
]