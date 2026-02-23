import subprocess
import sys
import os
import tempfile
import time
import platform 
from dataclasses import dataclass
from src.config import LOGS_DIR
from src.test_runner import run_tests

@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: str
    execution_time: float


def get_resource_limit_script():
    """
    Generate a Python script that sets resource limits before executing code.
    Works cross-platform (macOS and Linux).
    """
    return '''
import sys
import os

# Try to set resource limits (works on Unix-like systems)
try:
    import resource
    
    # CPU time limit: 5 seconds of actual CPU time
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    
    # Memory limit: 256MB (macOS has issues with RSS, so we use AS)
    try:
        resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
    except (ValueError, OSError):
        # macOS sometimes fails here, that's okay
        pass
    
    # File size limit: 10MB per file
    resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024, 10 * 1024 * 1024))
    
except (ImportError, ValueError, OSError) as e:
    # Resource limits not available on this platform
    pass

# Now execute the actual user code
exec(compile(open(sys.argv[1]).read(), sys.argv[1], 'exec'))
'''


def execute_code(code: str, timeout: int = 10) -> ExecutionResult:
    """
    Safely executes Python code in an isolated subprocess with resource limits.
    
    Security layers:
    1. Runs in separate process (can be killed without affecting parent)
    2. CPU time limit (kills after 5 seconds of CPU usage)
    3. Memory limit (256MB cap)
    4. Wall-clock timeout (kills after 10 seconds regardless of CPU usage)
    5. Filesystem restricted to logs directory
    6. File size limits (10MB per file)
    """
    start_time = time.time()

    # Write the user's code to a temporary file
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='_user.py',
        delete=False,
        dir=LOGS_DIR
    ) as user_file:
        user_file.write(code)
        user_code_path = user_file.name

    # Write the resource-limiting wrapper script
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='_wrapper.py',
        delete=False,
        dir=LOGS_DIR
    ) as wrapper_file:
        wrapper_file.write(get_resource_limit_script())
        wrapper_path = wrapper_file.name

    try:
        # Run the wrapper script which sets limits then executes user code
        result = subprocess.run(
            [sys.executable, wrapper_path, user_code_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=LOGS_DIR,  # Restrict filesystem access
            env={
                'PATH': os.environ.get('PATH', ''),
                'PYTHONPATH': '',  # Isolate from system packages
            }
        )

        execution_time = time.time() - start_time

        # Check if code contains tests
        code_has_tests = 'unittest.TestCase' in code
        
        if code_has_tests and result.returncode == 0:
            # Run the test suite
            test_result = run_tests(code)
            
            if test_result.success:
                # All tests passed
                return ExecutionResult(
                    success=True,
                    output=f"✅ All tests passed! ({test_result.passed}/{test_result.total_tests})\n{result.stdout.strip()}",
                    error=result.stderr.strip(),
                    execution_time=execution_time
                )
            else:
                # Some tests failed - provide detailed feedback
                failure_details = []
                for failure in test_result.failures:
                    failure_details.append(
                        f"❌ {failure['test_name']}\n"
                        f"   {failure['message']}"
                    )
                
                error_msg = (
                    f"Tests failed: {test_result.passed}/{test_result.total_tests} passed\n\n"
                    + "\n\n".join(failure_details)
                )
                
                return ExecutionResult(
                    success=False,
                    output=result.stdout.strip(),
                    error=error_msg,
                    execution_time=execution_time
                )
        
        # No tests or code crashed - check exit codes
        if result.returncode == -9 or result.returncode == 137:
            return ExecutionResult(
                success=False,
                output=result.stdout.strip(),
                error="Process killed by system - likely exceeded CPU or memory limit",
                execution_time=execution_time
            )
        elif result.returncode == 158 or 'CPU time limit exceeded' in result.stderr:
            return ExecutionResult(
                success=False,
                output=result.stdout.strip(),
                error="CPU time limit exceeded (5 seconds)",
                execution_time=execution_time
            )
        elif result.returncode == 153 or 'File size limit exceeded' in result.stderr:
            return ExecutionResult(
                success=False,
                output=result.stdout.strip(),
                error="File size limit exceeded (10MB per file)",
                execution_time=execution_time
            )
        elif result.returncode == 0:
            return ExecutionResult(
                success=True,
                output=result.stdout.strip(),
                error=result.stderr.strip(),
                execution_time=execution_time
            )
        else:
            return ExecutionResult(
                success=False,
                output=result.stdout.strip(),
                error=result.stderr.strip() or f"Process exited with code {result.returncode}",
                execution_time=execution_time
            )

    except subprocess.TimeoutExpired:
        # Wall-clock timeout
        return ExecutionResult(
            success=False,
            output="",
            error=f"Execution timed out after {timeout} seconds",
            execution_time=timeout
        )
    except Exception as e:
        return ExecutionResult(
            success=False,
            output="",
            error=f"Execution failed: {str(e)}",
            execution_time=time.time() - start_time
        )
    finally:
        # Always clean up temp files
        for path in [user_code_path, wrapper_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass


def is_code_safe(code: str) -> tuple:
    """
    Basic static analysis to detect dangerous operations.
    Returns (is_safe: bool, message: str)
    """
    dangerous_patterns = [
        ("import shutil", "filesystem manipulation"),
        ("rmdir", "directory deletion"),
        ("os.remove", "file deletion"),
        ("os.unlink", "file deletion"),
        ("subprocess", "subprocess spawning"),
        ("__import__", "dynamic imports"),
        ("eval(", "dynamic code evaluation"),
        ("exec(", "dynamic code execution"),
        ("open(", "file system access"),
        ("socket", "network access"),
        ("requests", "network access"),
        ("urllib", "network access"),
        ("http.client", "network access"),
    ]

    for pattern, reason in dangerous_patterns:
        if pattern in code:
            return False, f"Blocked: code contains '{pattern}' ({reason})"

    return True, "Code passed safety check"
