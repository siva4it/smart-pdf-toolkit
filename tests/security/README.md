# Security and Stress Testing Framework

This directory contains a comprehensive security and stress testing framework for Smart PDF Toolkit. The framework provides automated testing capabilities for security vulnerabilities, performance bottlenecks, and system stability under various load conditions.

## Overview

The framework consists of several key components:

1. **Security Testing Framework** - Tests for security vulnerabilities and attack vectors
2. **Stress Testing Framework** - Performance and load testing capabilities
3. **Comprehensive Test Runner** - Unified interface for running all tests
4. **Automated Reporting** - Detailed reports with risk assessment and recommendations
5. **CI/CD Integration** - GitHub Actions workflows for automated testing

## Components

### Security Testing (`comprehensive_security_framework.py`)

The security testing framework includes:

- **Password Security Tests**: Password strength validation, bypass attempts, brute force protection
- **Input Validation Tests**: Malicious input handling, buffer overflow protection, injection attack prevention
- **File Handling Security**: Malicious PDF handling, file traversal prevention, zip bomb protection
- **Memory Safety Tests**: Memory exhaustion scenarios, leak detection, large file handling
- **Concurrency Tests**: Race condition detection, deadlock prevention, concurrent operation stability

### Stress Testing (`stress_testing_framework.py`)

The stress testing framework provides:

- **Load Testing**: Configurable concurrent operations with resource monitoring
- **Performance Benchmarking**: Standardized benchmarks for all major operations
- **Resource Monitoring**: Real-time memory and CPU usage tracking
- **Scalability Testing**: Testing system behavior under increasing load
- **Endurance Testing**: Long-running tests to detect stability issues

### Comprehensive Test Runner (`comprehensive_test_runner.py`)

The unified test runner offers:

- **Integrated Execution**: Run security, stress, and benchmark tests together
- **Detailed Reporting**: Executive summaries, risk assessments, compliance status
- **CI/CD Integration**: Exit codes and artifacts for automated pipelines
- **Configurable Testing**: Flexible test configuration and execution options

## Usage

### Running Individual Test Suites

```bash
# Run security tests only
python tests/security/comprehensive_test_runner.py --test-types security

# Run stress tests only
python tests/security/comprehensive_test_runner.py --test-types stress

# Run benchmark tests only
python tests/security/comprehensive_test_runner.py --test-types benchmark
```

### Running Comprehensive Tests

```bash
# Run all test types
python tests/security/comprehensive_test_runner.py --test-types security stress benchmark

# Save results to file
python tests/security/comprehensive_test_runner.py --output results.json

# Show summary only
python tests/security/comprehensive_test_runner.py --summary-only
```

### Using pytest

```bash
# Run security test suite
pytest tests/security/test_comprehensive_suite.py::TestComprehensiveSecuritySuite -v

# Run stress test suite
pytest tests/security/test_comprehensive_suite.py::TestComprehensiveStressSuite -v

# Run integration tests
pytest tests/security/test_comprehensive_suite.py::TestComprehensiveIntegration -v

# Run all comprehensive tests
pytest tests/security/test_comprehensive_suite.py -v
```

## Configuration

### Test Configuration (`security_test_config.yaml`)

The framework uses a YAML configuration file to define:

- Test suite parameters and thresholds
- Security test scenarios and inputs
- Stress test configurations and limits
- Performance benchmarks and targets
- Reporting and compliance requirements

### Environment Variables

- `PYTHONPATH`: Set to project root for module imports
- `STRESS_TEST_TYPE`: Override stress test configuration (light/medium/heavy)
- `LOG_LEVEL`: Set logging level (DEBUG/INFO/WARNING/ERROR)

## Test Categories

### Security Tests

1. **Password Security**
   - Weak password detection
   - Password bypass attempts
   - Brute force protection

2. **Input Validation**
   - Malicious input handling
   - Buffer overflow protection
   - Injection attack prevention

3. **File Security**
   - Malicious PDF handling
   - File traversal prevention
   - Zip bomb protection

4. **Memory Safety**
   - Memory exhaustion scenarios
   - Memory leak detection
   - Large file handling

5. **Concurrency Safety**
   - Race condition detection
   - Deadlock prevention
   - Concurrent operation stability

### Stress Tests

1. **Load Testing**
   - Light load (2-5 concurrent operations)
   - Medium load (5-10 concurrent operations)
   - Heavy load (10+ concurrent operations)

2. **Performance Benchmarks**
   - PDF operations (split, merge, rotate)
   - Content extraction (text, images)
   - Format conversion (PDF to images, images to PDF)
   - Security operations (password management)

3. **Resource Monitoring**
   - Memory usage tracking
   - CPU utilization monitoring
   - Execution time measurement
   - Error rate analysis

## Reporting

### Executive Summary

The framework generates executive summaries including:

- Overall test status and performance score
- Critical, high, and medium severity issues
- Risk assessment (security, performance, operational)
- Compliance status and recommendations

### Detailed Reports

Comprehensive reports include:

- Test execution details and metrics
- Security vulnerability analysis
- Performance bottleneck identification
- Resource usage patterns
- Actionable recommendations

### Risk Assessment

Risk assessments categorize findings by:

- **Critical**: Immediate security threats or system failures
- **High**: Significant security or performance issues
- **Medium**: Moderate issues requiring attention
- **Low**: Minor issues or informational findings

## CI/CD Integration

### GitHub Actions Workflow

The framework includes a comprehensive GitHub Actions workflow (`security-stress-tests.yml`) that:

- Runs security tests on multiple Python versions
- Executes stress tests with different load configurations
- Performs benchmark testing on scheduled runs
- Generates comprehensive reports and artifacts
- Provides PR comments with test results

### Exit Codes

The test runner uses standard exit codes for CI/CD integration:

- `0`: Success - All tests passed
- `1`: Warnings - Non-critical issues found
- `2`: Failures - Critical issues or test failures
- `3`: Errors - System errors or test runner failures

## Best Practices

### Writing Security Tests

1. **Test Real Attack Vectors**: Use actual malicious inputs and attack patterns
2. **Validate Error Handling**: Ensure graceful failure for invalid inputs
3. **Check Resource Limits**: Verify protection against resource exhaustion
4. **Test Edge Cases**: Include boundary conditions and unusual scenarios

### Writing Stress Tests

1. **Monitor Resources**: Track memory, CPU, and execution time
2. **Use Realistic Loads**: Test with representative workloads
3. **Gradual Ramp-up**: Increase load gradually to identify breaking points
4. **Measure Consistently**: Use standardized metrics for comparison

### Interpreting Results

1. **Focus on Critical Issues**: Address critical and high-severity findings first
2. **Consider Context**: Evaluate findings in the context of actual usage
3. **Track Trends**: Monitor performance and security metrics over time
4. **Validate Fixes**: Re-run tests after implementing fixes

## Troubleshooting

### Common Issues

1. **Memory Errors**: Increase system memory or reduce concurrent operations
2. **Timeout Errors**: Increase test timeouts or optimize operations
3. **Permission Errors**: Ensure proper file system permissions
4. **Dependency Errors**: Install all required dependencies

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
python tests/security/comprehensive_test_runner.py --log-level DEBUG
```

### Test Isolation

Each test uses isolated temporary directories to prevent interference:

- Security tests: `security_test_*`
- Stress tests: `stress_test_*`
- Integration tests: `integration_test_*`

## Contributing

When adding new tests:

1. Follow the existing test patterns and naming conventions
2. Include appropriate error handling and cleanup
3. Add documentation for new test scenarios
4. Update configuration files as needed
5. Test both success and failure scenarios

## Dependencies

Required packages:
- `pytest`: Test framework
- `psutil`: System resource monitoring
- `pyyaml`: Configuration file parsing
- `smart_pdf_toolkit`: Core toolkit modules

Optional packages:
- `pytest-cov`: Coverage reporting
- `pytest-xdist`: Parallel test execution
- `pytest-timeout`: Test timeout handling

## License

This testing framework is part of Smart PDF Toolkit and follows the same license terms.