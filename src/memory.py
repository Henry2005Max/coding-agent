from dataclasses import dataclass, asdict
from typing import List, Optional
import json
from datetime import datetime


@dataclass
class Attempt:
    """Represents a single attempt by the agent"""
    iteration: int
    code: str
    success: bool
    output: str
    error: str
    test_results: Optional[dict] = None  # {total, passed, failed, failures: [...]}
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class ShortTermMemory:
    """
    Stores the last N attempts with structured data.
    Enables pattern detection and reflection.
    """
    
    def __init__(self, max_size: int = 5):
        self.max_size = max_size
        self.attempts: List[Attempt] = []
    
    def add(self, attempt: Attempt):
        """Add an attempt to memory, keeping only the last max_size attempts"""
        self.attempts.append(attempt)
        if len(self.attempts) > self.max_size:
            self.attempts.pop(0)  # Remove oldest
    
    def get_all(self) -> List[Attempt]:
        """Get all attempts in memory"""
        return self.attempts.copy()
    
    def get_recent(self, n: int) -> List[Attempt]:
        """Get the last N attempts"""
        return self.attempts[-n:] if n <= len(self.attempts) else self.attempts.copy()
    
    def clear(self):
        """Clear all attempts from memory"""
        self.attempts.clear()
    
    def count(self) -> int:
        """Number of attempts in memory"""
        return len(self.attempts)
    
    def has_pattern(self, pattern_type: str) -> bool:
        """
        Detect if a specific error pattern is repeating.
        
        Pattern types:
        - 'same_error': Same error message in last 2 attempts
        - 'same_test_failure': Same test failing in last 2 attempts
        - 'no_progress': No successful tests in last 3 attempts
        """
        if pattern_type == 'same_error' and len(self.attempts) >= 2:
            last_two = self.attempts[-2:]
            if not last_two[0].success and not last_two[1].success:
                # Both failed - check if error is similar
                error1 = last_two[0].error.split('\n')[0]  # First line of error
                error2 = last_two[1].error.split('\n')[0]
                return error1 == error2
        
        elif pattern_type == 'same_test_failure' and len(self.attempts) >= 2:
            last_two = self.attempts[-2:]
            if last_two[0].test_results and last_two[1].test_results:
                failures1 = [f['test_name'] for f in last_two[0].test_results.get('failures', [])]
                failures2 = [f['test_name'] for f in last_two[1].test_results.get('failures', [])]
                # Check if any test failed in both attempts
                return bool(set(failures1) & set(failures2))
        
        elif pattern_type == 'no_progress' and len(self.attempts) >= 3:
            last_three = self.attempts[-3:]
            # Check if all three attempts had zero passing tests
            for attempt in last_three:
                if attempt.success:
                    return False
                if attempt.test_results and attempt.test_results.get('passed', 0) > 0:
                    return False
            return True
        
        return False
    
    def get_summary(self) -> dict:
        """Get a summary of all attempts in memory"""
        if not self.attempts:
            return {'total_attempts': 0}
        
        return {
            'total_attempts': len(self.attempts),
            'successful_attempts': sum(1 for a in self.attempts if a.success),
            'failed_attempts': sum(1 for a in self.attempts if not a.success),
            'most_recent_error': self.attempts[-1].error if not self.attempts[-1].success else None,
            'progress': self._calculate_progress()
        }
    
    def _calculate_progress(self) -> str:
        """Determine if the agent is making progress"""
        if len(self.attempts) < 2:
            return "insufficient_data"
        
        recent = self.attempts[-3:] if len(self.attempts) >= 3 else self.attempts
        
        # Check if tests are improving
        if all(a.test_results for a in recent):
            passed_counts = [a.test_results.get('passed', 0) for a in recent]
            if passed_counts == sorted(passed_counts):  # Increasing
                return "improving"
            elif passed_counts == sorted(passed_counts, reverse=True):  # Decreasing
                return "regressing"
        
        # Check if moving from errors to test failures (that's progress)
        has_execution_error = any(not a.test_results and not a.success for a in recent)
        has_test_failures = any(a.test_results and not a.success for a in recent)
        
        if has_execution_error and has_test_failures:
            return "mixed"
        
        return "stable"
    
    def to_json(self) -> str:
        """Serialize memory to JSON"""
        return json.dumps([asdict(a) for a in self.attempts], indent=2)
    
    def from_json(self, json_str: str):
        """Load memory from JSON"""
        data = json.loads(json_str)
        self.attempts = [Attempt(**item) for item in data]


def build_reflection_prompt(memory: ShortTermMemory) -> str:
    """
    Build a reflection prompt based on memory.
    This helps the agent analyze its past failures before trying again.
    """
    if memory.count() == 0:
        return ""
    
    summary = memory.get_summary()
    attempts = memory.get_all()
    
    reflection = "\n## Reflection on Previous Attempts\n\n"
    reflection += f"You have made {summary['total_attempts']} attempt(s) so far.\n"
    reflection += f"Progress status: {summary['progress']}\n\n"
    
    # Pattern detection warnings
    if memory.has_pattern('same_error'):
        reflection += "⚠️ WARNING: You've had the same error in your last 2 attempts. Try a completely different approach.\n\n"
    
    if memory.has_pattern('same_test_failure'):
        reflection += "⚠️ WARNING: The same test is failing repeatedly. Focus specifically on fixing that test.\n\n"
    
    if memory.has_pattern('no_progress'):
        reflection += "⚠️ WARNING: No tests have passed in 3 attempts. Consider rewriting from scratch with a simpler approach.\n\n"
    
    # Recent attempt summary
    if len(attempts) >= 2:
        reflection += "Recent attempts:\n"
        for attempt in attempts[-3:]:  # Last 3
            status = "✅ SUCCESS" if attempt.success else "❌ FAILED"
            reflection += f"\nAttempt {attempt.iteration}: {status}\n"
            
            if attempt.test_results:
                passed = attempt.test_results.get('passed', 0)
                total = attempt.test_results.get('total_tests', 0)
                reflection += f"  Tests: {passed}/{total} passed\n"
                
                if attempt.test_results.get('failures'):
                    reflection += "  Failed tests:\n"
                    for failure in attempt.test_results['failures'][:2]:  # Show first 2
                        reflection += f"    - {failure['test_name']}: {failure['message']}\n"
            
            if not attempt.success and attempt.error:
                error_preview = attempt.error.split('\n')[0][:100]
                reflection += f"  Error: {error_preview}\n"
    
    reflection += "\nBefore writing new code, ask yourself:\n"
    reflection += "1. What specifically went wrong in the last attempt?\n"
    reflection += "2. Am I repeating the same approach? Should I try something different?\n"
    reflection += "3. Are there edge cases I'm missing?\n\n"
    
    return reflection