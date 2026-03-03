import time
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta
import re


@dataclass
class ExecutionAttempt:
    """Track individual execution attempts for circuit breaker"""
    timestamp: datetime
    success: bool
    error_type: Optional[str] = None


class CircuitBreaker:
    """
    Prevents infinite loops of failures.
    
    Opens (stops execution) if:
    - N consecutive failures
    - No progress in M attempts
    - Too many attempts in short time window
    """
    
    def __init__(self, max_consecutive_failures: int = 3, 
                 failure_window_minutes: int = 5,
                 max_attempts_per_window: int = 10):
        self.max_consecutive_failures = max_consecutive_failures
        self.failure_window = timedelta(minutes=failure_window_minutes)
        self.max_attempts_per_window = max_attempts_per_window
        self.attempts: List[ExecutionAttempt] = []
        self.is_open = False
        self.open_reason = ""
    
    def record_attempt(self, success: bool, error_type: Optional[str] = None):
        """Record an execution attempt"""
        attempt = ExecutionAttempt(
            timestamp=datetime.now(),
            success=success,
            error_type=error_type
        )
        self.attempts.append(attempt)
        self._check_circuit()
    
    def _check_circuit(self):
        """Check if circuit should open (stop execution)"""
        if not self.attempts:
            return
        
        # Check 1: Too many consecutive failures
        recent_attempts = self.attempts[-self.max_consecutive_failures:]
        if len(recent_attempts) == self.max_consecutive_failures:
            if all(not a.success for a in recent_attempts):
                self.is_open = True
                self.open_reason = f"Circuit opened: {self.max_consecutive_failures} consecutive failures"
                return
        
        # Check 2: Too many attempts in short time
        now = datetime.now()
        recent = [a for a in self.attempts if now - a.timestamp < self.failure_window]
        if len(recent) >= self.max_attempts_per_window:
            failures = sum(1 for a in recent if not a.success)
            if failures >= self.max_attempts_per_window * 0.8:  # 80% failure rate
                self.is_open = True
                self.open_reason = f"Circuit opened: {failures}/{len(recent)} failures in {self.failure_window.seconds//60} minutes"
                return
    
    def reset(self):
        """Reset the circuit breaker"""
        self.is_open = False
        self.open_reason = ""
        self.attempts = []
    
    def get_status(self) -> dict:
        """Get current circuit breaker status"""
        total_attempts = len(self.attempts)
        if total_attempts == 0:
            return {'status': 'closed', 'attempts': 0}
        
        successes = sum(1 for a in self.attempts if a.success)
        failures = total_attempts - successes
        
        return {
            'status': 'open' if self.is_open else 'closed',
            'reason': self.open_reason if self.is_open else None,
            'total_attempts': total_attempts,
            'successes': successes,
            'failures': failures,
            'success_rate': successes / total_attempts if total_attempts > 0 else 0
        }


class RateLimiter:
    """
    Prevents API abuse by limiting requests per time window.
    """
    
    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests: List[datetime] = []
    
    def can_proceed(self) -> tuple:
        """
        Check if we can make another request.
        Returns (allowed, message)
        """
        now = datetime.now()
        
        # Remove old requests outside the window
        self.requests = [r for r in self.requests if now - r < self.window]
        
        if len(self.requests) >= self.max_requests:
            wait_time = (self.requests[0] + self.window - now).seconds
            return False, f"Rate limit exceeded. Wait {wait_time} seconds."
        
        return True, ""
    
    def record_request(self):
        """Record a new request"""
        self.requests.append(datetime.now())
    
    def get_status(self) -> dict:
        """Get current rate limiter status"""
        now = datetime.now()
        self.requests = [r for r in self.requests if now - r < self.window]
        
        return {
            'requests_in_window': len(self.requests),
            'max_requests': self.max_requests,
            'window_seconds': self.window.seconds,
            'remaining': self.max_requests - len(self.requests)
        }


class AdvancedSafetyChecker:
    """
    Additional safety checks beyond basic static analysis.
    Catches patterns that simple keyword matching misses.
    """
    
    @staticmethod
    def check_infinite_loop_risk(code: str) -> tuple:
        """Detect potential infinite loops"""
        # Check for while True without break
        if 'while True:' in code or 'while 1:' in code:
            if 'break' not in code and 'return' not in code:
                return False, "Potential infinite loop: 'while True' without break or return"
        
        # Check for recursion without base case
        function_defs = re.findall(r'def (\w+)\(', code)
        for func_name in function_defs:
            # Find the function body - simplified check
            if func_name in code:
                # Check if function calls itself (recursion)
                lines_after_def = code.split('def ' + func_name + '(')[1] if 'def ' + func_name + '(' in code else ''
                if func_name in lines_after_def:
                    # Check for base case keywords
                    if 'if' not in lines_after_def[:200] or 'return' not in lines_after_def[:200]:
                        return False, "Potential infinite recursion in '" + func_name + "': no obvious base case"
        
        return True, ""
    
    @staticmethod
    def check_resource_abuse(code: str) -> tuple:
        """Detect code that might abuse resources"""
        dangerous_patterns = [
            (r'\[\s*\d+\s*\]\s*\*\s*\d{6,}', "Large list allocation (millions of elements)"),
            (r'range\(\s*\d{7,}', "Large range (10M+ iterations)"),
            (r'for.+range\(\s*\d{6,}', "Loop with 1M+ iterations"),
        ]
        
        for pattern, description in dangerous_patterns:
            if re.search(pattern, code):
                return False, "Resource abuse risk: " + description
        
        return True, ""
    
    @staticmethod
    def check_all(code: str) -> tuple:
        """Run all advanced safety checks"""
        warnings = []
        
        # Infinite loop check
        safe, msg = AdvancedSafetyChecker.check_infinite_loop_risk(code)
        if not safe:
            warnings.append(msg)
        
        # Resource abuse check
        safe, msg = AdvancedSafetyChecker.check_resource_abuse(code)
        if not safe:
            warnings.append(msg)
        
        return len(warnings) == 0, warnings


def create_execution_summary(attempts: List, circuit_breaker: CircuitBreaker, 
                             rate_limiter: RateLimiter) -> dict:
    """Create a summary of execution session for logging"""
    return {
        'total_attempts': len(attempts),
        'circuit_breaker': circuit_breaker.get_status(),
        'rate_limiter': rate_limiter.get_status(),
        'timestamp': datetime.now().isoformat()
    }