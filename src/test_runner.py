import unittest
import sys
import io
from dataclasses import dataclass
from typing import List


@dataclass
class TestResult:
    """Structured test result with pass/fail details"""
    total_tests: int
    passed: int
    failed: int
    errors: int
    failures: List[dict]  # List of {test_name, error_type, message, traceback}
    success: bool  # True only if all tests passed


def run_tests(code: str) -> TestResult:
    """
    Runs unittest tests embedded in the code.
    Expects code to contain a class that inherits from unittest.TestCase.
    
    Returns structured results showing which tests passed/failed and why.
    """
    # Capture stdout/stderr during test execution
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    # Create a namespace to execute the code
    namespace = {}
    
    try:
        # Execute the code to define the test class
        exec(code, namespace)
        
        # Find all TestCase classes defined in the code
        test_classes = [
            obj for obj in namespace.values()
            if isinstance(obj, type) and issubclass(obj, unittest.TestCase) and obj != unittest.TestCase
        ]
        
        if not test_classes:
            return TestResult(
                total_tests=0,
                passed=0,
                failed=0,
                errors=1,
                failures=[{
                    'test_name': 'code_structure',
                    'error_type': 'NoTestsFound',
                    'message': 'No unittest.TestCase class found in code',
                    'traceback': ''
                }],
                success=False
            )
        
        # Create a test suite from all test classes
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        for test_class in test_classes:
            suite.addTests(loader.loadTestsFromTestCase(test_class))
        
        # Run the tests with a custom result object
        runner = unittest.TextTestRunner(stream=stdout_capture, verbosity=2)
        result = runner.run(suite)
        
        # Parse failures and errors
        failures = []
        
        for test, traceback in result.failures:
            failures.append({
                'test_name': str(test),
                'error_type': 'AssertionError',
                'message': traceback.split('\n')[-2] if '\n' in traceback else traceback,
                'traceback': traceback
            })
        
        for test, traceback in result.errors:
            # Extract the actual error type from traceback
            error_lines = traceback.strip().split('\n')
            error_type = error_lines[-1].split(':')[0] if error_lines else 'Error'
            
            failures.append({
                'test_name': str(test),
                'error_type': error_type,
                'message': traceback.split('\n')[-1] if '\n' in traceback else traceback,
                'traceback': traceback
            })
        
        return TestResult(
            total_tests=result.testsRun,
            passed=result.testsRun - len(result.failures) - len(result.errors),
            failed=len(result.failures),
            errors=len(result.errors),
            failures=failures,
            success=result.wasSuccessful()
        )
    
    except Exception as e:
        # Code failed to execute at all
        import traceback as tb
        return TestResult(
            total_tests=0,
            passed=0,
            failed=0,
            errors=1,
            failures=[{
                'test_name': 'code_execution',
                'error_type': type(e).__name__,
                'message': str(e),
                'traceback': tb.format_exc()
            }],
            success=False
        )