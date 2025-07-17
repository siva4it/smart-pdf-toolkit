#!/usr/bin/env python3
"""Comprehensive Security and Stress Test Runner.

This script provides a unified interface for running comprehensive security
and stress tests with detailed reporting and CI/CD integration.
"""

import sys
import os
import argparse
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from smart_pdf_toolkit.core.config import Config
    from tests.security.comprehensive_security_framework import SecurityTestOrchestrator
    from tests.security.stress_testing_framework import StressTestFramework, StressTestConfig
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the project root and dependencies are installed")
    sys.exit(1)


class ComprehensiveTestRunner:
    """Unified test runner for security and stress testing."""
    
    def __init__(self, config: Config, log_level: str = "INFO"):
        self.config = config
        self.setup_logging(log_level)
        
        self.security_orchestrator = SecurityTestOrchestrator(config)
        self.stress_framework = StressTestFramework(config)
        
        self.test_results = {}
        self.start_time = time.time()
    
    def setup_logging(self, log_level: str):
        """Set up logging configuration."""
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.config.temp_dir / "comprehensive_tests.log")
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_all_tests(self, test_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run all comprehensive tests.
        
        Args:
            test_types: List of test types to run. Options: ['security', 'stress', 'benchmark']
                       If None, runs all test types.
        
        Returns:
            Dictionary containing all test results
        """
        if test_types is None:
            test_types = ['security', 'stress', 'benchmark']
        
        self.logger.info(f"Starting comprehensive test suite: {test_types}")
        
        results = {
            'test_suite': 'comprehensive',
            'start_time': self.start_time,
            'test_types': test_types,
            'results': {}
        }
        
        # Run security tests
        if 'security' in test_types:
            self.logger.info("Running security tests...")
            try:
                security_results = self.security_orchestrator.run_comprehensive_tests()
                results['results']['security'] = security_results
                self.logger.info("Security tests completed")
            except Exception as e:
                self.logger.error(f"Security tests failed: {e}")
                results['results']['security'] = {'error': str(e)}
        
        # Run stress tests
        if 'stress' in test_types:
            self.logger.info("Running stress tests...")
            try:
                stress_results = self.run_stress_tests()
                results['results']['stress'] = stress_results
                self.logger.info("Stress tests completed")
            except Exception as e:
                self.logger.error(f"Stress tests failed: {e}")
                results['results']['stress'] = {'error': str(e)}
        
        # Run benchmark tests
        if 'benchmark' in test_types:
            self.logger.info("Running benchmark tests...")
            try:
                benchmark_results = self.run_benchmark_tests()
                results['results']['benchmark'] = benchmark_results
                self.logger.info("Benchmark tests completed")
            except Exception as e:
                self.logger.error(f"Benchmark tests failed: {e}")
                results['results']['benchmark'] = {'error': str(e)}
        
        results['end_time'] = time.time()
        results['total_duration'] = results['end_time'] - results['start_time']
        
        # Generate comprehensive report
        results['comprehensive_report'] = self.generate_comprehensive_report(results)
        
        self.test_results = results
        self.logger.info(f"Comprehensive test suite completed in {results['total_duration']:.2f} seconds")
        
        return results
    
    def run_security_tests(self, suites: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run security tests only."""
        self.logger.info("Running security test suite")
        return self.security_orchestrator.run_comprehensive_tests(suites)
    
    def run_stress_tests(self) -> Dict[str, Any]:
        """Run stress tests with various configurations."""
        self.logger.info("Running stress test suite")
        
        stress_configs = [
            StressTestConfig(
                duration_seconds=30,
                concurrent_operations=5,
                max_memory_mb=1024,
                operations_per_second_target=2.0
            ),
            StressTestConfig(
                duration_seconds=60,
                concurrent_operations=10,
                max_memory_mb=2048,
                operations_per_second_target=1.0
            ),
            StressTestConfig(
                duration_seconds=120,
                concurrent_operations=3,
                max_memory_mb=1536,
                operations_per_second_target=0.5
            )
        ]
        
        stress_results = []
        
        for i, config in enumerate(stress_configs):
            self.logger.info(f"Running stress test configuration {i+1}/{len(stress_configs)}")
            
            # Test different operation types
            test_operations = [
                ('pdf_split', self._create_split_stress_test),
                ('pdf_merge', self._create_merge_stress_test),
                ('text_extraction', self._create_text_extraction_stress_test),
                ('concurrent_mixed', self._create_mixed_stress_test)
            ]
            
            for test_name, test_func in test_operations:
                try:
                    result = self.stress_framework.run_load_test(
                        test_func, config, f"Stress Test: {test_name}"
                    )
                    stress_results.append(result)
                except Exception as e:
                    self.logger.error(f"Stress test {test_name} failed: {e}")
        
        # Generate stress test report
        return self.stress_framework.generate_stress_test_report(stress_results)
    
    def run_benchmark_tests(self) -> Dict[str, Any]:
        """Run benchmark test suite."""
        self.logger.info("Running benchmark test suite")
        return self.stress_framework.run_benchmark_suite()
    
    def generate_comprehensive_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive report combining all test results."""
        report = {
            'executive_summary': self._generate_executive_summary(results),
            'security_analysis': self._analyze_security_results(results.get('results', {}).get('security', {})),
            'performance_analysis': self._analyze_performance_results(results.get('results', {})),
            'recommendations': self._generate_comprehensive_recommendations(results),
            'risk_assessment': self._generate_risk_assessment(results),
            'compliance_status': self._generate_compliance_status(results)
        }
        
        return report
    
    def _generate_executive_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of all tests."""
        summary = {
            'total_duration_minutes': results.get('total_duration', 0) / 60,
            'test_types_executed': results.get('test_types', []),
            'overall_status': 'PASS',
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'performance_score': 0
        }
        
        # Analyze security results
        security_results = results.get('results', {}).get('security', {})
        if security_results and 'failures_by_severity' in security_results:
            failures = security_results['failures_by_severity']
            summary['critical_issues'] += failures.get('critical', 0)
            summary['high_issues'] += failures.get('high', 0)
            summary['medium_issues'] += failures.get('medium', 0)
        
        # Determine overall status
        if summary['critical_issues'] > 0:
            summary['overall_status'] = 'CRITICAL'
        elif summary['high_issues'] > 3:
            summary['overall_status'] = 'HIGH_RISK'
        elif summary['high_issues'] > 0 or summary['medium_issues'] > 5:
            summary['overall_status'] = 'MEDIUM_RISK'
        
        # Calculate performance score (0-100)
        performance_score = 100
        if summary['critical_issues'] > 0:
            performance_score -= 50
        if summary['high_issues'] > 0:
            performance_score -= summary['high_issues'] * 10
        if summary['medium_issues'] > 0:
            performance_score -= summary['medium_issues'] * 2
        
        summary['performance_score'] = max(0, performance_score)
        
        return summary
    
    def _analyze_security_results(self, security_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze security test results."""
        if not security_results or 'error' in security_results:
            return {'status': 'error', 'message': security_results.get('error', 'No security results')}
        
        analysis = {
            'total_tests': security_results.get('summary', {}).get('total_tests', 0),
            'success_rate': security_results.get('summary', {}).get('success_rate', 0),
            'critical_vulnerabilities': [],
            'high_vulnerabilities': [],
            'security_score': 0
        }
        
        # Extract critical and high severity failures
        critical_failures = security_results.get('critical_failures', [])
        high_failures = security_results.get('high_failures', [])
        
        analysis['critical_vulnerabilities'] = [
            {
                'test': failure.get('test_name', 'unknown'),
                'error': failure.get('error_message', 'unknown error'),
                'category': failure.get('category', 'general')
            }
            for failure in critical_failures
        ]
        
        analysis['high_vulnerabilities'] = [
            {
                'test': failure.get('test_name', 'unknown'),
                'error': failure.get('error_message', 'unknown error'),
                'category': failure.get('category', 'general')
            }
            for failure in high_failures
        ]
        
        # Calculate security score
        security_score = 100
        security_score -= len(critical_failures) * 25
        security_score -= len(high_failures) * 10
        analysis['security_score'] = max(0, security_score)
        
        return analysis
    
    def _analyze_performance_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance test results."""
        analysis = {
            'stress_test_summary': {},
            'benchmark_summary': {},
            'performance_bottlenecks': [],
            'resource_usage': {}
        }
        
        # Analyze stress test results
        stress_results = results.get('stress', {})
        if stress_results and 'summary' in stress_results:
            analysis['stress_test_summary'] = {
                'total_operations': stress_results['summary'].get('total_operations', 0),
                'success_rate': stress_results['summary'].get('overall_success_rate', 0),
                'avg_ops_per_second': stress_results['summary'].get('avg_operations_per_second', 0),
                'peak_memory_mb': stress_results['summary'].get('peak_memory_mb', 0),
                'peak_cpu_percent': stress_results['summary'].get('peak_cpu_percent', 0)
            }
            
            analysis['performance_bottlenecks'] = stress_results.get('performance_bottlenecks', [])
        
        # Analyze benchmark results
        benchmark_results = results.get('benchmark', {})
        if benchmark_results:
            # Extract key metrics from benchmark results
            benchmark_summary = {}
            for test_name, test_result in benchmark_results.items():
                if isinstance(test_result, dict) and 'operations_per_second' in test_result:
                    benchmark_summary[test_name] = {
                        'ops_per_second': test_result.get('operations_per_second', 0),
                        'success_rate': ((test_result.get('successful_operations', 0) / 
                                        max(test_result.get('total_operations', 1), 1)) * 100),
                        'avg_memory_mb': test_result.get('avg_memory_mb', 0)
                    }
            
            analysis['benchmark_summary'] = benchmark_summary
        
        return analysis
    
    def _generate_comprehensive_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate comprehensive recommendations based on all test results."""
        recommendations = []
        
        # Security recommendations
        security_results = results.get('results', {}).get('security', {})
        if security_results:
            security_recommendations = security_results.get('recommendations', [])
            recommendations.extend([f"Security: {rec}" for rec in security_recommendations])
        
        # Performance recommendations
        stress_results = results.get('results', {}).get('stress', {})
        if stress_results:
            performance_recommendations = stress_results.get('recommendations', [])
            recommendations.extend([f"Performance: {rec}" for rec in performance_recommendations])
        
        # General recommendations based on overall results
        executive_summary = self.generate_comprehensive_report(results).get('executive_summary', {})
        
        if executive_summary.get('critical_issues', 0) > 0:
            recommendations.append("URGENT: Address critical security issues before production deployment")
        
        if executive_summary.get('performance_score', 100) < 70:
            recommendations.append("Consider performance optimization before handling production workloads")
        
        if executive_summary.get('overall_status') == 'HIGH_RISK':
            recommendations.append("Conduct additional security review and testing")
        
        return recommendations
    
    def _generate_risk_assessment(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate risk assessment based on test results."""
        risk_assessment = {
            'overall_risk_level': 'LOW',
            'security_risk': 'LOW',
            'performance_risk': 'LOW',
            'operational_risk': 'LOW',
            'risk_factors': []
        }
        
        # Assess security risk
        security_results = results.get('results', {}).get('security', {})
        if security_results:
            critical_count = security_results.get('failures_by_severity', {}).get('critical', 0)
            high_count = security_results.get('failures_by_severity', {}).get('high', 0)
            
            if critical_count > 0:
                risk_assessment['security_risk'] = 'CRITICAL'
                risk_assessment['risk_factors'].append(f"{critical_count} critical security vulnerabilities")
            elif high_count > 2:
                risk_assessment['security_risk'] = 'HIGH'
                risk_assessment['risk_factors'].append(f"{high_count} high-severity security issues")
            elif high_count > 0:
                risk_assessment['security_risk'] = 'MEDIUM'
        
        # Assess performance risk
        stress_results = results.get('results', {}).get('stress', {})
        if stress_results:
            success_rate = stress_results.get('summary', {}).get('overall_success_rate', 100)
            peak_memory = stress_results.get('summary', {}).get('peak_memory_mb', 0)
            
            if success_rate < 80:
                risk_assessment['performance_risk'] = 'HIGH'
                risk_assessment['risk_factors'].append(f"Low success rate in stress tests: {success_rate:.1f}%")
            elif success_rate < 95:
                risk_assessment['performance_risk'] = 'MEDIUM'
            
            if peak_memory > 2048:  # 2GB
                risk_assessment['performance_risk'] = 'HIGH'
                risk_assessment['risk_factors'].append(f"High memory usage: {peak_memory:.1f}MB")
        
        # Determine overall risk level
        risk_levels = [risk_assessment['security_risk'], risk_assessment['performance_risk']]
        if 'CRITICAL' in risk_levels:
            risk_assessment['overall_risk_level'] = 'CRITICAL'
        elif 'HIGH' in risk_levels:
            risk_assessment['overall_risk_level'] = 'HIGH'
        elif 'MEDIUM' in risk_levels:
            risk_assessment['overall_risk_level'] = 'MEDIUM'
        
        return risk_assessment
    
    def _generate_compliance_status(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate compliance status based on test results."""
        compliance = {
            'security_compliance': 'PASS',
            'performance_compliance': 'PASS',
            'overall_compliance': 'PASS',
            'compliance_issues': []
        }
        
        # Check security compliance
        security_results = results.get('results', {}).get('security', {})
        if security_results:
            critical_count = security_results.get('failures_by_severity', {}).get('critical', 0)
            if critical_count > 0:
                compliance['security_compliance'] = 'FAIL'
                compliance['compliance_issues'].append(f"Critical security vulnerabilities: {critical_count}")
        
        # Check performance compliance
        stress_results = results.get('results', {}).get('stress', {})
        if stress_results:
            success_rate = stress_results.get('summary', {}).get('overall_success_rate', 100)
            if success_rate < 90:  # 90% success rate threshold
                compliance['performance_compliance'] = 'FAIL'
                compliance['compliance_issues'].append(f"Performance success rate below threshold: {success_rate:.1f}%")
        
        # Overall compliance
        if compliance['security_compliance'] == 'FAIL' or compliance['performance_compliance'] == 'FAIL':
            compliance['overall_compliance'] = 'FAIL'
        
        return compliance
    
    def save_results(self, output_file: Path, format: str = 'json'):
        """Save test results to file."""
        if not self.test_results:
            self.logger.warning("No test results to save")
            return
        
        try:
            if format.lower() == 'json':
                with open(output_file, 'w') as f:
                    json.dump(self.test_results, f, indent=2, default=str)
            else:
                self.logger.error(f"Unsupported output format: {format}")
                return
            
            self.logger.info(f"Test results saved to {output_file}")
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
    
    def print_summary(self):
        """Print a summary of test results."""
        if not self.test_results:
            print("No test results available")
            return
        
        report = self.test_results.get('comprehensive_report', {})
        executive_summary = report.get('executive_summary', {})
        
        print("\\n" + "="*60)
        print("COMPREHENSIVE TEST RESULTS SUMMARY")
        print("="*60)
        
        print(f"Overall Status: {executive_summary.get('overall_status', 'UNKNOWN')}")
        print(f"Performance Score: {executive_summary.get('performance_score', 0)}/100")
        print(f"Total Duration: {executive_summary.get('total_duration_minutes', 0):.1f} minutes")
        
        print(f"\\nIssues Found:")
        print(f"  Critical: {executive_summary.get('critical_issues', 0)}")
        print(f"  High: {executive_summary.get('high_issues', 0)}")
        print(f"  Medium: {executive_summary.get('medium_issues', 0)}")
        
        # Risk assessment
        risk_assessment = report.get('risk_assessment', {})
        print(f"\\nRisk Assessment:")
        print(f"  Overall Risk: {risk_assessment.get('overall_risk_level', 'UNKNOWN')}")
        print(f"  Security Risk: {risk_assessment.get('security_risk', 'UNKNOWN')}")
        print(f"  Performance Risk: {risk_assessment.get('performance_risk', 'UNKNOWN')}")
        
        # Compliance status
        compliance = report.get('compliance_status', {})
        print(f"\\nCompliance Status:")
        print(f"  Overall: {compliance.get('overall_compliance', 'UNKNOWN')}")
        print(f"  Security: {compliance.get('security_compliance', 'UNKNOWN')}")
        print(f"  Performance: {compliance.get('performance_compliance', 'UNKNOWN')}")
        
        # Top recommendations
        recommendations = report.get('recommendations', [])
        if recommendations:
            print(f"\\nTop Recommendations:")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"  {i}. {rec}")
        
        print("="*60)
    
    # Helper methods for stress tests
    
    def _create_split_stress_test(self):
        """Create a PDF split operation for stress testing."""
        test_pdf = self.config.temp_dir / "stress_test.pdf"
        test_pdf.touch()
        output_dir = self.config.temp_dir / "stress_split"
        output_dir.mkdir(exist_ok=True)
        
        return self.stress_framework.pdf_operations.split_pdf(
            pdf_path=str(test_pdf),
            output_dir=str(output_dir)
        )
    
    def _create_merge_stress_test(self):
        """Create a PDF merge operation for stress testing."""
        test_pdfs = []
        for i in range(3):
            test_pdf = self.config.temp_dir / f"stress_merge_{i}.pdf"
            test_pdf.touch()
            test_pdfs.append(test_pdf)
        
        output_pdf = self.config.temp_dir / "stress_merged.pdf"
        
        return self.stress_framework.pdf_operations.merge_pdfs(
            pdf_paths=[str(pdf) for pdf in test_pdfs],
            output_path=str(output_pdf)
        )
    
    def _create_text_extraction_stress_test(self):
        """Create a text extraction operation for stress testing."""
        test_pdf = self.config.temp_dir / "stress_extract.pdf"
        test_pdf.touch()
        output_txt = self.config.temp_dir / "stress_text.txt"
        
        return self.stress_framework.content_extractor.extract_text(
            pdf_path=str(test_pdf),
            output_path=str(output_txt)
        )
    
    def _create_mixed_stress_test(self):
        """Create a mixed operation for stress testing."""
        import random
        operations = [
            self._create_split_stress_test,
            self._create_merge_stress_test,
            self._create_text_extraction_stress_test
        ]
        
        selected_operation = random.choice(operations)
        return selected_operation()


def main():
    """Main entry point for the comprehensive test runner."""
    parser = argparse.ArgumentParser(description="Comprehensive Security and Stress Test Runner")
    
    parser.add_argument(
        '--test-types',
        nargs='+',
        choices=['security', 'stress', 'benchmark'],
        default=['security', 'stress', 'benchmark'],
        help='Types of tests to run'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        help='Output file for test results (JSON format)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    
    parser.add_argument(
        '--temp-dir',
        type=Path,
        help='Temporary directory for test files'
    )
    
    parser.add_argument(
        '--summary-only',
        action='store_true',
        help='Print only summary, skip detailed output'
    )
    
    args = parser.parse_args()
    
    # Set up configuration
    config = Config()
    
    if args.temp_dir:
        config.temp_dir = args.temp_dir
        config.temp_dir.mkdir(parents=True, exist_ok=True)
    else:
        config.temp_dir = Path(tempfile.mkdtemp(prefix="comprehensive_tests_"))
    
    config.output_dir = config.temp_dir / "output"
    config.output_dir.mkdir(exist_ok=True)
    
    try:
        # Create and run test runner
        runner = ComprehensiveTestRunner(config, args.log_level)
        
        # Run tests
        results = runner.run_all_tests(args.test_types)
        
        # Save results if output file specified
        if args.output:
            runner.save_results(args.output)
        
        # Print summary
        if not args.summary_only:
            print(json.dumps(results, indent=2, default=str))
        else:
            runner.print_summary()
        
        # Determine exit code based on results
        executive_summary = results.get('comprehensive_report', {}).get('executive_summary', {})
        critical_issues = executive_summary.get('critical_issues', 0)
        overall_status = executive_summary.get('overall_status', 'PASS')
        
        if critical_issues > 0 or overall_status == 'CRITICAL':
            sys.exit(2)  # Critical issues
        elif overall_status in ['HIGH_RISK', 'MEDIUM_RISK']:
            sys.exit(1)  # Non-critical issues
        else:
            sys.exit(0)  # Success
    
    except Exception as e:
        print(f"Test runner failed: {e}", file=sys.stderr)
        sys.exit(3)
    
    finally:
        # Clean up temporary directory if we created it
        if not args.temp_dir and config.temp_dir.exists():
            try:
                shutil.rmtree(config.temp_dir)
            except Exception as e:
                print(f"Warning: Failed to clean up temporary directory: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()