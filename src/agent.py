import anthropic
import json
import re
import os
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from src.config import ANTHROPIC_API_KEY, MODEL, MAX_ITERATIONS, MAX_TOKENS
from src.executor import execute_code, is_code_safe, ExecutionResult
from src.test_runner import run_tests, TestResult
from src.memory import ShortTermMemory, Attempt, build_reflection_prompt
from src.long_term_memory import LongTermMemory, Solution, build_retrieval_context
from src.safety import CircuitBreaker, RateLimiter, AdvancedSafetyChecker

console = Console()
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def extract_code(text: str):
    """Pull Python code out of the model's markdown response."""
    pattern = r"```python\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[0].strip() if matches else None


def log_attempt(goal: str, iteration: int, code: str, result: ExecutionResult):
    """Save each attempt to a log file for later review."""
    log_path = os.path.join("logs", f"attempt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    log_data = {
        "goal": goal,
        "iteration": iteration,
        "code": code,
        "success": result.success,
        "output": result.output,
        "error": result.error,
        "execution_time": result.execution_time,
        "timestamp": datetime.now().isoformat()
    }
    with open(log_path, "w") as f:
        json.dump(log_data, f, indent=2)


def build_system_prompt() -> str:
    return """You are an expert Python coding agent. Your job is to write correct, working Python code to achieve a given goal.

Rules you must follow:
1. Always write code WITH unit tests using Python's unittest framework
2. Define the main function/logic first, then create a test class that inherits from unittest.TestCase
3. Write multiple test cases covering different scenarios (normal cases, edge cases, error cases)
4. Wrap everything in ```python ... ``` markdown blocks
5. Only use Python standard library — no external packages
6. Keep code simple and focused on the goal
7. If you are given test failure details, analyze them and fix the code

Example structure:
```python
import unittest

# Your main code here
def my_function(x):
    return x * 2

# Your tests here
class TestMyFunction(unittest.TestCase):
    def test_positive_number(self):
        self.assertEqual(my_function(5), 10)
    
    def test_zero(self):
        self.assertEqual(my_function(0), 0)
    
    def test_negative(self):
        self.assertEqual(my_function(-3), -6)
```

When you respond, always:
- Briefly explain what you are doing (1-2 sentences)
- Then provide the complete code block
"""


def build_user_prompt(goal: str, memory: ShortTermMemory, long_term_memory: LongTermMemory) -> str:
    """Build the prompt including reflection, history, and similar past solutions."""
    prompt = f"Goal: {goal}\n\n"

    # Check for similar past solutions
    similar = long_term_memory.find_similar(goal, top_k=2, min_similarity=0.3)
    if similar:
        prompt += build_retrieval_context(similar)

    if memory.count() == 0:
        prompt += "This is your first attempt. Write code with tests to achieve the goal."
    else:
        # Add reflection prompt
        prompt += build_reflection_prompt(memory)
        
        # Add detailed history
        prompt += "\n## Previous Attempts History\n\n"
        for attempt in memory.get_all():
            prompt += f"--- Attempt {attempt.iteration} ---\n"
            prompt += f"Code:\n```python\n{attempt.code}\n```\n"
            
            if attempt.success:
                prompt += f"Result: ✅ SUCCESS\n"
                if attempt.test_results:
                    prompt += f"All {attempt.test_results['total_tests']} tests passed!\n"
                prompt += f"Output: {attempt.output}\n\n"
            else:
                prompt += f"Result: ❌ FAILED\n"
                
                if attempt.test_results:
                    prompt += f"Tests: {attempt.test_results['passed']}/{attempt.test_results['total_tests']} passed\n"
                    if attempt.test_results['failures']:
                        prompt += "Failed tests:\n"
                        for failure in attempt.test_results['failures']:
                            prompt += f"  - {failure['test_name']}: {failure['message']}\n"
                
                prompt += f"Error: {attempt.error}\n\n"
        
        prompt += "Analyze the failures above and write corrected code with tests."

    return prompt


def run_agent(goal: str):
    """
    The main agent loop with safety, memory, and reflection.
    Plan → Execute → Test → Reflect → Learn → Repeat until success or max iterations.
    """
    console.print(Panel(f"[bold green]GOAL:[/bold green] {goal}", title="Coding Agent Starting"))

    # Initialize memory systems
    memory = ShortTermMemory(max_size=5)
    long_term_memory = LongTermMemory()
    
    # Initialize safety systems
    circuit_breaker = CircuitBreaker(max_consecutive_failures=3)
    rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
    
    messages = []
    
    # Check for similar past solutions
    similar = long_term_memory.find_similar(goal, top_k=2, min_similarity=0.3)
    if similar:
        console.print(f"\n[bold cyan]💡 Found {len(similar)} similar past solution(s)[/bold cyan]")
        for solution, similarity in similar:
            console.print(f"  - '{solution.goal}' (similarity: {similarity:.0%}, solved in {solution.iterations_to_solve} iterations)")

    for iteration in range(1, MAX_ITERATIONS + 1):
        console.print(f"\n[bold yellow]--- Iteration {iteration}/{MAX_ITERATIONS} ---[/bold yellow]")
        
        # Check circuit breaker
        if circuit_breaker.is_open:
            console.print(f"[bold red]🛑 CIRCUIT BREAKER OPEN[/bold red]")
            console.print(f"[bold red]Reason: {circuit_breaker.open_reason}[/bold red]")
            console.print("[dim]The agent has been stopped to prevent further waste. Human intervention required.[/dim]")
            break
        
        # Check rate limiter
        can_proceed, rate_msg = rate_limiter.can_proceed()
        if not can_proceed:
            console.print(f"[bold red]🚫 RATE LIMIT EXCEEDED[/bold red]")
            console.print(f"[bold red]{rate_msg}[/bold red]")
            break
        
        rate_limiter.record_request()
        
        # Show memory summary if we have previous attempts
        if memory.count() > 0:
            summary = memory.get_summary()
            console.print(f"[dim]Memory: {summary['successful_attempts']} succeeded, {summary['failed_attempts']} failed | Progress: {summary['progress']}[/dim]")

        # Build the prompt with reflection and retrieval
        user_prompt = build_user_prompt(goal, memory, long_term_memory)

        # Add to message history
        messages.append({"role": "user", "content": user_prompt})

        # Call the Claude API
        console.print("[dim]Calling Claude API...[/dim]")
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=build_system_prompt(),
            messages=messages
        )

        assistant_message = response.content[0].text
        messages.append({"role": "assistant", "content": assistant_message})

        console.print(f"\n[bold cyan]Claude's response:[/bold cyan] {assistant_message[:200]}...")

        # Extract code from response
        code = extract_code(assistant_message)

        if not code:
            console.print("[bold red]No code found in response. Retrying...[/bold red]")
            memory.add(Attempt(
                iteration=iteration,
                code="",
                success=False,
                output="",
                error="No code block returned by Claude"
            ))
            circuit_breaker.record_attempt(success=False, error_type="NoCodeReturned")
            continue

        # Show the code
        console.print(Panel(Syntax(code, "python", theme="monokai"), title=f"Code - Attempt {iteration}"))

        # Basic safety check
        is_safe, safety_message = is_code_safe(code)
        if not is_safe:
            console.print(f"[bold red]SAFETY BLOCK:[/bold red] {safety_message}")
            memory.add(Attempt(
                iteration=iteration,
                code=code,
                success=False,
                output="",
                error=safety_message
            ))
            circuit_breaker.record_attempt(success=False, error_type="SafetyBlock")
            continue
        
        # Advanced safety check
        is_safe_advanced, warnings = AdvancedSafetyChecker.check_all(code)
        if not is_safe_advanced:
            console.print(f"[bold red]⚠️ ADVANCED SAFETY WARNING:[/bold red]")
            for warning in warnings:
                console.print(f"  - {warning}")
            console.print("[dim]Skipping execution due to safety concerns.[/dim]")
            memory.add(Attempt(
                iteration=iteration,
                code=code,
                success=False,
                output="",
                error="; ".join(warnings)
            ))
            circuit_breaker.record_attempt(success=False, error_type="AdvancedSafetyBlock")
            continue

        # Execute the code
        console.print("[dim]Executing code...[/dim]")
        result = execute_code(code)

        # Parse test results if present
        test_results = None
        if "tests passed" in result.output.lower() or "tests failed" in result.error.lower():
            test_results = parse_test_results(result)

        # Record in circuit breaker
        circuit_breaker.record_attempt(success=result.success, error_type=result.error.split('\n')[0] if not result.success else None)

        # Store attempt in short-term memory
        memory.add(Attempt(
            iteration=iteration,
            code=code,
            success=result.success,
            output=result.output,
            error=result.error,
            test_results=test_results
        ))

        # Log this attempt to disk
        log_attempt(goal, iteration, code, result)

        # Show result
        if result.success:
            console.print(Panel(
                f"[bold green]SUCCESS[/bold green]\n{result.output}\nTime: {result.execution_time:.2f}s",
                title="Result"
            ))
            
            # Store successful solution in long-term memory
            if test_results:
                solution = Solution(
                    goal=goal,
                    code=code,
                    test_results=test_results,
                    timestamp=datetime.now().isoformat(),
                    keywords=[],
                    iterations_to_solve=iteration
                )
                long_term_memory.add(solution)
                console.print(f"[dim]💾 Solution saved to long-term memory[/dim]")
            
            console.print(f"\n[bold green]✅ Goal achieved in {iteration} iteration(s)![/bold green]")
            
            # Show final stats
            summary = memory.get_summary()
            ltm_stats = long_term_memory.get_stats()
            cb_status = circuit_breaker.get_status()
            console.print(f"[dim]Session stats: {summary['total_attempts']} attempts, {summary['successful_attempts']} succeeded[/dim]")
            console.print(f"[dim]Long-term memory: {ltm_stats['total_solutions']} solutions stored[/dim]")
            console.print(f"[dim]Circuit breaker: {cb_status['failures']} failures, success rate {cb_status['success_rate']:.0%}[/dim]")
            return True
        else:
            console.print(Panel(
                f"[bold red]FAILED[/bold red]\n{result.error}\nTime: {result.execution_time:.2f}s",
                title="Result"
            ))

    console.print(f"\n[bold red]❌ Agent stopped after {MAX_ITERATIONS} iterations without success.[/bold red]")
    
    # Show final stats
    summary = memory.get_summary()
    cb_status = circuit_breaker.get_status()
    console.print(f"[dim]Final stats: {summary['total_attempts']} attempts, progress was '{summary['progress']}'[/dim]")
    console.print(f"[dim]Circuit breaker: {cb_status['status']}, {cb_status['failures']} failures[/dim]")
    return False
