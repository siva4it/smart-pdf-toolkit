#!/usr/bin/env python3
"""Security Test Runner for CI/CD Integration.

This script runs comprehensive security and stress tests and provides
CI/CD friendly output and exit codes.
"""

import sys
import os
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from smart_pdf_toolkit.core.config import Config
    from tests.security.test_security_test_orchestrator import SecurityTestOrchestrator, TestSeverity
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the project root and dependencies are installed")
    sys.exit(1)


def setup_logging(log_level: str = "INFO", log_file: Optional[Path] = None) -> logging.Logger:
    """Set up logging configuration."""
    logger = logging.getLogger("security_test_runner")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive security and stress tests for Smart PDF Toolkit"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("security_test_results"),
        help="Output directory for test results (default: security_test_results)"
    )
    
    parser.add_argument(
        "--log-level", "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Log file path (optional)"
    )
    
    parser.add_argument(
        "--skip-stress-tests",
        action="store_true",
        help="Skip stress tests (faster execution for CI)"
    )
    
    parser.add_argument(
        "--skip-vulnerability-scan",
        action="store_true",
        help="Skip vulnerability scanning"
    )
    
    parser.add_argument(
        "--skip-malicious-pdf-tests",
        action="store_true",
        help="Skip malicious PDF handling tests"
    )
    
    parser.add_argument(
        "--stress-test-duration",
        type=int,
        default=30,
        help="Duration for stress tests in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Fail the build on warnings (not just critical/fail)"
    )
    
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Output results in JSON format to stdout"
    )
    
    parser.add_argument(
        "--ci-mode",
        action="store_true",
        help="Run in CI mode (optimized for CI/CD environments)"
    )
    
    return parser.parse_args()


def run_security_tests(args, logger) -> Dict[str, Any]:
    """Run the comprehensive security test suite."""
    
    # Create configuration
    config = Config()
    config.temp_dir = args.output_dir / "temp"
    config.output_dir = args.output_dir
    
    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create orchestrator
    orchestrator = SecurityTestOrchestrator(config, logger, args.output_dir)
    
    # Adjust settings for CI mode
    if args.ci_mode:
        logger.info("Running in CI mode - optimizing for CI/CD environment")
        # Reduce resource usage for CI
        stress_test_duration = min(args.stress_test_duration, 15)  # Max 15 seconds in CI
        include_stress_tests = not args.skip_stress_tests and stress_test_duration > 0
    else:
        stress_test_duration = args.stress_test_duration
        include_stress_tests = not args.skip_stress_tests
    
    # Run comprehensive security suite
    logger.info("Starting comprehensive security test suite...")
    
    result = orchestrator.run_comprehensive_security_suite(
        include_stress_tests=include_stress_tests,
        include_vulnerability_scan=not args.skip_vulnerability_scan,
        include_malicious_pdf_tests=not args.skip_malicious_pdf_tests,
        stress_test_duration=stress_test_duration
    )
    
    # Generate CI/CD report
    ci_report = orchestrator.generate_ci_cd_report(result)
    
    return {
        "orchestration_result": result,
        "ci_report": ci_report
    }


def print_summary(result, ci_report, logger):
    """Print test summary."""
    logger.info("\\n" + "=" * 60)
    logger.info("SECURITY TEST SUITE SUMMARY")
    logger.info("=" * 60)
    
    logger.info(f"Overall Status: {ci_report['status'].upper()}")
    logger.info(f"Success: {'YES' if ci_report['success'] else 'NO'}")
    logger.info(f"Duration: {ci_report['duration']:.1f} seconds")
    
    logger.info("\\nTest Results:")
    logger.info(f"  Total Tests: {ci_report['summary']['total_tests']}")
    logger.info(f"  Passed: {ci_report['summary']['passed_tests']}")
    logger.info(f"  Failed: {ci_report['summary']['failed_tests']}")
    logger.info(f"  Success Rate: {ci_report['summary']['success_rate']:.1f}%")
    
    logger.info("\\nSecurity Analysis:")
    logger.info(f"  Vulnerabilities Found: {ci_report['security']['vulnerabilities']}")
    logger.info(f"  Critical: {ci_report['security']['critical']}")
    logger.info(f"  High: {ci_report['security']['high']}")
    
    if 'performance' in ci_report:
        logger.info("\\nPerformance Testing:")
        logger.info(f"  Stress Tests: {ci_report['performance']['stress_tests']}")
        logger.info(f"  Failures: {ci_report['performance']['failures']}")
        logger.info(f"  Performance Issues: {ci_report['performance']['issues']}")
    
    if ci_report['recommendations']:
        logger.info("\\nTop Recommendations:")
        for i, rec in enumerate(ci_report['recommendations'], 1):
            logger.info(f"  {i}. {rec}")
    
    logger.info("=" * 60)


def determine_exit_code(ci_report, fail_on_warnings: bool) -> int:
    """Determine appropriate exit code based on test results."""
    status = ci_report['status']
    
    if status == 'critical':
        return 2  # Critical failure
    elif status == 'fail':
        return 1  # Failure
    elif status == 'warning' and fail_on_warnings:
        return 1  # Treat warnings as failures
    else:
        return 0  # Success


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Set up logging
    logger = setup_logging(args.log_level, args.log_file)
    
    try:
        logger.info("Smart PDF Toolkit - Security Test Runner")
        logger.info(f"Project root: {project_root}")
        logger.info(f"Output directory: {args.output_dir}")
        
        # Run security tests
        results = run_security_tests(args, logger)
        orchestration_result = results["orchestration_result"]
        ci_report = results["ci_report"]
        
        # Print summary
        if not args.json_output:
            print_summary(orchestration_result, ci_report, logger)
        
        # Output JSON if requested
        if args.json_output:
            print(json.dumps(ci_report, indent=2))
        
        # Determine exit code
        exit_code = determine_exit_code(ci_report, args.fail_on_warnings)
        
        if exit_code == 0:
            logger.info("✅ All security tests passed successfully!")
        elif exit_code == 1:
            logger.warning("⚠️  Security tests completed with issues")
        else:
            logger.error("❌ Critical security issues found!")
        
        logger.info(f"Test results saved to: {args.output_dir}")
        
        return exit_code
        
    except KeyboardInterrupt:
        logger.info("\\nTest execution interrupted by user")
        return 130  # Standard exit code for SIGINT
        
    except Exception as e:
        logger.error(f"Unexpected error during test execution: {e}")
        logger.exception("Full traceback:")
        return 3  # Unexpected error


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)