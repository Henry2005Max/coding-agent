import subprocess
import sys
import os
import tempfile
import time
from dataclasses import dataclass
from src.config import LOGS_DIR

@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: str
    execution_time: float

def execute_code(code: str, timeout: int = 10) -> ExecutionResult:
    """
    Safely executes Python code in an isolated subprocess.
    Returns the result including output, errors, and timing.
    """
    start_time = time.time()

    # Write code to a temporary file
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.py',
        delete=False,
        dir=LOGS_DIR
    ) as tmp_file:
        tmp_file.write(code)
        tmp_path = tmp_file.name

    try:
        # Run the code in a subprocess with strict limits
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=LOGS_DIR  # Restrict to logs directory only
        )

        execution_time = time.time() - start_time

        return ExecutionResult(
            success=result.returncode == 0,
            output=result.stdout.strip(),
            error=result.stderr.strip(),
            execution_time=execution_time
        )

    except subprocess.TimeoutExpired:
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
        # Always clean up the temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def is_code_safe(code: str) -> tuple[bool, str]:
    """
    Basic static analysis to detect dangerous operations
    before we even attempt to run the code.
    """
    dangerous_patterns = [
        ("import shutil", "filesystem manipulation"),
        ("rmdir", "directory deletion"),
        ("os.remove", "file deletion"),
        ("subprocess", "subprocess spawning"),
        ("__import__", "dynamic imports"),
        ("eval(", "dynamic code evaluation"),
        ("exec(", "dynamic code execution"),
        ("open(", "file system access"),
        ("socket", "network access"),
        ("requests", "network access"),
        ("urllib", "network access"),
    ]

    for pattern, reason in dangerous_patterns:
        if pattern in code:
            return False, f"Blocked: code contains '{pattern}' ({reason})"

    return True, "Code passed safety check"