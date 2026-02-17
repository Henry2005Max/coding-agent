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
1. Always wrap your code in ```python ... ``` markdown blocks
2. Write complete, runnable code — no placeholders or TODOs
3. Only use Python standard library — no external packages
4. Keep code simple and focused on the goal
5. If you are given an error from a previous attempt, fix it

When you respond, always:
- Briefly explain what you are doing (1-2 sentences)
- Then provide the complete code block
"""


def build_user_prompt(goal: str, history: list) -> str:
    """Build the prompt including full history of past attempts."""
    prompt = f"Goal: {goal}\n\n"

    if not history:
        prompt += "This is your first attempt. Write code to achieve the goal."
    else:
        prompt += f"You have made {len(history)} previous attempt(s). Here is what happened:\n\n"
        for i, attempt in enumerate(history, 1):
            prompt += f"--- Attempt {i} ---\n"
            prompt += f"Code:\n```python\n{attempt['code']}\n```\n"
            if attempt['success']:
                prompt += f"Result: SUCCESS\nOutput: {attempt['output']}\n\n"
            else:
                prompt += f"Result: FAILED\nError: {attempt['error']}\n\n"
        prompt += "Analyze the errors above and write a corrected version of the code."

    return prompt


def run_agent(goal: str):
    """
    The main agent loop.
    Plan → Execute → Test → Reflect → Repeat until success or max iterations.
    """
    console.print(Panel(f"[bold green]GOAL:[/bold green] {goal}", title="Coding Agent Starting"))

    history = []
    messages = []

    for iteration in range(1, MAX_ITERATIONS + 1):
        console.print(f"\n[bold yellow]--- Iteration {iteration}/{MAX_ITERATIONS} ---[/bold yellow]")

        # Build the prompt for this iteration
        user_prompt = build_user_prompt(goal, history)

        # Add to message history (this is how Claude tracks conversation)
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

        console.print(f"\n[bold cyan]Claude says:[/bold cyan] {assistant_message[:200]}...")

        # Extract code from response
        code = extract_code(assistant_message)

        if not code:
            console.print("[bold red]No code found in response. Retrying...[/bold red]")
            history.append({"code": "none", "success": False, "output": "", "error": "No code block returned"})
            continue

        # Show the code
        console.print(Panel(Syntax(code, "python", theme="monokai"), title=f"Code - Attempt {iteration}"))

        # Safety check before running
        is_safe, safety_message = is_code_safe(code)
        if not is_safe:
            console.print(f"[bold red]SAFETY BLOCK:[/bold red] {safety_message}")
            history.append({"code": code, "success": False, "output": "", "error": safety_message})
            continue

        # Execute the code
        console.print("[dim]Executing code...[/dim]")
        result = execute_code(code)

        # Log this attempt
        log_attempt(goal, iteration, code, result)

        # Show result
        if result.success:
            console.print(Panel(
                f"[bold green]SUCCESS[/bold green]\nOutput: {result.output}\nTime: {result.execution_time:.2f}s",
                title="Result"
            ))
            console.print(f"\n[bold green]Goal achieved in {iteration} iteration(s)![/bold green]")
            return True
        else:
            console.print(Panel(
                f"[bold red]FAILED[/bold red]\nError: {result.error}\nTime: {result.execution_time:.2f}s",
                title="Result"
            ))
            history.append({
                "code": code,
                "success": False,
                "output": result.output,
                "error": result.error
            })

    console.print(f"\n[bold red]Agent stopped after {MAX_ITERATIONS} iterations without success.[/bold red]")
    return False