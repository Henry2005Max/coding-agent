# Self-Improving Coding Agent

> An autonomous agent that writes code, runs tests, and learns from failures.
> Built with Python + Claude API (Anthropic).

---

## Project Overview

This is an intermediate-level AI engineering project. The agent receives a goal, writes Python code to achieve it, executes that code safely, and if it fails, it reads the error, reflects on what went wrong, and tries again. It does not stop until the code works or it hits a maximum iteration limit.

**Core concepts this project teaches:**
- Agentic loops (Plan → Execute → Test → Reflect)
- Safe code execution via subprocesses
- Prompt engineering and conversation history
- Memory and logging
- Code safety and static analysis

---

## Project Structure

```
coding-agent/
├── src/
│   ├── __init__.py       # Makes src a Python package
│   ├── config.py         # API keys, model settings, paths
│   ├── agent.py          # Main agent loop and Claude API calls
│   └── executor.py       # Safe code execution and safety checks
├── tests/                # (Future) automated tests
├── memory/               # (Future) long-term memory storage
├── logs/                 # Auto-generated execution logs (JSON)
├── venv/                 # Python virtual environment (not pushed to GitHub)
├── main.py               # Entry point — run this to start the agent
├── .env                  # Your API key (never pushed to GitHub)
├── .gitignore            # Protects secrets and junk files
└── README.md             # This file
```

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.9.6 | Core language |
| Anthropic SDK | Claude API calls |
| python-dotenv | Load API key from .env file |
| rich | Pretty terminal output |
| resource module | CPU/memory limits (Unix systems) |
| unittest | Built-in test framework |

---

## Setup Instructions (Start Fresh on Any Machine)

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/coding-agent.git
cd coding-agent
```

### 2. Create and activate virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 3. Upgrade pip
```bash
pip install --upgrade pip
```

### 4. Install dependencies
```bash
pip install anthropic python-dotenv rich
```

### 5. Create your .env file
```bash
touch .env
```

Open `.env` and add:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Get your API key from: https://console.anthropic.com

### 6. Run the agent
```bash
python3 main.py
```

---

## How to Use

### Interactive mode
```bash
python3 main.py
```
The agent will prompt you to type your goal.

### Inline mode
```bash
python3 main.py "write a function that returns the fibonacci sequence up to n terms"
```

### Example goals to try
- `write a function that calculates the factorial of a number and print factorial of 5`
- `write a program that checks if a number is prime and test it with 17`
- `write a function that reverses a string and print the reverse of hello world`

---

## How the Agent Works (The Loop)

```
You give a goal
        ↓
Iteration 1:
  Claude writes code
        ↓
  Safety check (static analysis)
        ↓
  Execute in sandboxed subprocess
        ↓
  Did it pass? ──YES──→ Done! Print success.
        ↓ NO
  Log the failure + error message
        ↓
Iteration 2:
  Claude receives the goal + previous error
  Claude reflects and writes corrected code
        ↓
  ... repeat up to MAX_ITERATIONS (default: 5)
```
---
## File-by-File Explanation

### `src/config.py`
Loads the API key from `.env` using `python-dotenv`. Defines:
- Which Claude model to use
- Maximum iterations before giving up
- Maximum tokens per API response
- Paths for logs and memory directories

### `src/executor.py`
Two functions:

**`execute_code(code, timeout=10)`**
- Writes the code to a temporary `.py` file in the logs directory
- Runs it in a separate subprocess (isolated from the main program)
- Captures stdout and stderr
- Enforces a timeout (kills the process if it runs too long)
- Cleans up the temp file after execution
- Returns an `ExecutionResult` dataclass with: success, output, error, execution_time

**`is_code_safe(code)`**
- Scans code for dangerous patterns before execution
- Blocks: file deletion, subprocess spawning, network access, dynamic eval/exec, and more
- Returns `(True, "safe")` or `(False, "reason it was blocked")`

### `src/agent.py`
The brain. Key functions:

**`extract_code(text)`**
- Uses regex to pull Python code from Claude's markdown response
- Looks for ` ```python ... ``` ` blocks

**`log_attempt(goal, iteration, code, result)`**
- Saves every attempt as a JSON file in `/logs`
- Records: goal, code written, success/failure, output, error, timestamp

**`build_system_prompt()`**
- Tells Claude exactly how to behave: always wrap code in markdown, no external packages, fix errors if given feedback

**`build_user_prompt(goal, history)`**
- On first attempt: sends just the goal
- On subsequent attempts: sends the goal + full history of what was tried and what errors occurred
- This is how the agent "reflects" — Claude sees its own failures

**`run_agent(goal)`**
- The main loop (up to MAX_ITERATIONS)
- Calls Claude → extracts code → safety check → executes → logs → repeats if failed

### `main.py`
Entry point. Handles:
- Command line arguments (inline goal)
- Interactive input (if no argument given)
- Calls `run_agent()` and prints final success/failure message

---

## Day-by-Day Build Plan

| Day | What We Built | Status |
|-----|--------------|--------|
| Day 1 | Project structure, config, executor, agent loop, main entry point | ✅ Complete |
| Day 2 | Execution sandbox with CPU/memory limits | ✅ Complete |
| Day 3 | Test runner + structured failure detection | ✅ Complete |
| Day 4 | Short-term memory + reflection mechanism |  Upcoming |
| Day 5 | Long-term memory with vector embeddings |  Upcoming |
| Day 6 | Circuit breaker + advanced safety layer |  Upcoming |
| Day 7 | Polish, CLI improvements, full demo |  Upcoming |

---

## Quick Summary of Each Day

## Day 1 — Foundation

**Date:** February 17, 2026

### What We Built
- Complete project structure (folders, files, .gitignore)
- Virtual environment setup
- Configuration system with environment variables
- Basic code executor with subprocess isolation and timeout
- Static code safety checker
- Main agent loop with Claude API integration
- Conversation history and reflection
- JSON logging system
- Rich terminal UI

---

## Important Concepts Learned (Day 1)

**Virtual environment:** An isolated Python installation for a specific project. Keeps dependencies from conflicting with other projects or your system Python. Always activate with `source venv/bin/activate` before working.

**python-dotenv:** Loads variables from a `.env` file into `os.environ`. The pattern `os.getenv("KEY")` then reads them. This is the standard way to handle secrets, never hardcode API keys.

**Subprocess execution:** Running code in a separate process means if the code crashes, it does not crash the agent. The parent process captures stdout and stderr and reports back.

**Dataclass:** A Python class decorated with `@dataclass` that automatically generates `__init__`, `__repr__`, and other boilerplate. Used for `ExecutionResult` to cleanly bundle multiple return values.

**Agentic loop:** The core pattern of autonomous AI systems. Instead of a single request-response, the agent acts, observes the result, and decides what to do next, repeatedly, until the goal is achieved.

**Conversation history:** Claude has no memory between API calls. To give it context, we send the full history of messages every time. This is how it "remembers" its previous attempts and errors.

---
## Bugs Fixed During Day 1

### Bug 1: Python 3.9 type hint syntax error
**File:** `src/agent.py`, line 16

**Error:**
```
TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'
```

**Cause:** The `str | None` union type syntax was introduced in Python 3.10. We are running Python 3.9.6.

**Fix:** Changed the function signature from:
```python
def extract_code(text: str) -> str | None:
```
To:
```python
def extract_code(text: str):
```

**Lesson:** Always check which Python version introduced a feature before using it. Type hints are cosmetic, removing them does not break functionality.

---

### Bug 2: Insufficient API credits
**Error:**
```
anthropic.BadRequestError: 400 - Your credit balance is too low
```

**Cause:** New Anthropic accounts need credits loaded before making API calls.

**Fix:** Add credits at https://console.anthropic.com → Settings → Billing. $5 is sufficient for development.

---

### Concepts Learned
- Virtual environments for project isolation
- Environment variables for secrets management
- Subprocess execution for code isolation
- Dataclasses for clean data structures
- Agentic loops (act → observe → reflect → repeat)
- Conversation history for context retention

---

## Day 2 — Production-Grade Sandbox

**Date:** February 23, 2026

### The Problem We Solved
Day 1's executor had a fatal weakness: malicious or buggy code could still consume 100% CPU, use all RAM, write gigabytes to disk, and run for the full timeout destroying performance.

**Proof:**
```python
# Day 1: This runs at 100% CPU for 3 full seconds
while True:
    pass
```

### The Solution: Multi-Layer Resource Limits

We upgraded from basic timeout-only protection to a **6-layer security system**:

#### Layer 1: CPU Time Limit (5 seconds)
- Uses `resource.RLIMIT_CPU` to track actual CPU time
- Kills infinite loops after 5 seconds of CPU usage
- **Key insight:** CPU time ≠ wall-clock time. Sleeping uses 0 CPU time.

#### Layer 2: Memory Limit (256MB)
- Uses `resource.RLIMIT_AS` (address space limit)
- Caps total memory allocation
- **Platform note:** macOS sometimes ignores this; Linux respects it strictly

#### Layer 3: File Size Limit (10MB per file)
- Uses `resource.RLIMIT_FSIZE`
- Prevents gigabyte file writes

#### Layer 4: Wall-Clock Timeout (10 seconds)
- Original Day 1 protection, kept as backup
- Kills even low-CPU processes after 10 seconds

#### Layer 5: Filesystem Restriction
- Code runs with `cwd=LOGS_DIR`
- Limits file operations to logs directory only

#### Layer 6: Environment Isolation
- Clears `PYTHONPATH`
- Passes minimal environment variables
- Prevents access to system packages

### Technical Implementation: Wrapper Script Pattern

Instead of directly running user code, we use a two-file approach:

```python
# wrapper.py (generated dynamically)
import resource
resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
resource.setrlimit(resource.RLIMIT_AS, (256*1024*1024, 256*1024*1024))
resource.setrlimit(resource.RLIMIT_FSIZE, (10*1024*1024, 10*1024*1024))
exec(compile(open('user_code.py').read(), 'user_code.py', 'exec'))
```

**Why this works:** Resource limits must be set *before* code runs. The wrapper guarantees limits are in place before the first line executes.

### Error Detection

Different failures produce different exit codes:
- **Exit 0:** Success ✅
- **Exit -24 (SIGXCPU, macOS):** CPU limit exceeded
- **Exit 158 (Linux):** CPU limit exceeded
- **Exit -9 or 137 (SIGKILL):** Memory limit exceeded
- **Exit 153:** File size exceeded

We detect these and return user-friendly error messages.

### Testing Results

**Test 1: Infinite Loop**
```python
while True: pass
```
✅ Killed after ~5 seconds with "CPU time limit exceeded"  
❌ Day 1: Would run at 100% CPU for full 10-second timeout

**Test 2: Normal Code**
```python
def factorial(n):
    return 1 if n <= 1 else n * factorial(n-1)
print(f"Factorial of 5 is {factorial(5)}")
```
✅ `ExecutionResult(success=True, output='Factorial of 5 is 120', time=0.10s)`

### Files Modified

**src/executor.py** — Complete rewrite (255 lines)
- Added `get_resource_limit_script()` function
- Rewrote `execute_code()` with wrapper pattern
- Added exit code detection
- Added platform-aware error handling
- Environment isolation

**src/config.py** — Added sandbox configuration
```python
CPU_TIME_LIMIT = 5
MEMORY_LIMIT_MB = 256
FILE_SIZE_LIMIT_MB = 10
EXECUTION_TIMEOUT = 10
```

### Concepts Learned Day 2

**Resource limits:** OS-level caps on CPU time, memory, file sizes enforced by the kernel.

**CPU time vs wall-clock time:** CPU time = actual compute usage. Sleeping/waiting doesn't count.

**Exit codes and signals:** Process killed by signal N returns exit code -N. SIGXCPU (24) → exit -24.

**Wrapper script pattern:** Guarantee setup runs before user code by generating a wrapper that does setup then executes via `exec()`.

**Platform differences:** macOS and Linux handle resource limits differently. Always test your target platform.

**Production-grade:** With these protections, the agent can run unsupervised without freezing machines or filling disks.

### Why This Matters

Without Day 2's protections, an autonomous agent could:
- ❌ Freeze your machine (100% CPU)
- ❌ Crash from out-of-memory
- ❌ Fill your disk (gigabyte files)
- ❌ Cost money (expensive compute for minutes)

With Day 2's sandbox:
- ✅ CPU limited to 5 seconds
- ✅ Memory capped at 256MB
- ✅ Files limited to 10MB
- ✅ Safe to run unsupervised

---

## Key Features

### 🔒 Security
- Multi-layer sandbox with OS-enforced limits
- Static code analysis before execution
- Subprocess isolation
- Resource caps (CPU, memory, disk)
- Filesystem and network restrictions

### 🧪 Testing
- Automatic test generation
- unittest framework integration
- Structured pass/fail results
- Expected vs actual value reporting
- Per-test granular feedback

### 🔄 Self-Improvement
- Conversation history for context
- Failure logging with full details
- Iterative refinement loop
- Reflection on errors
- Max iteration circuit breaker

### 📊 Observability
- JSON logs for every attempt
- Rich terminal UI with syntax highlighting
- Execution timing
- Success/failure tracking

---


### Day 3 — Test Runner (Feb 23, 2026)
Integrated Python's unittest framework. Agent now writes tests alongside code and receives structured pass/fail feedback per test.

**Key achievement:** Precise, actionable feedback instead of vague errors.

**Before:** "RecursionError on line 4"  
**After:** "test_factorial_of_5 failed: expected 120, got 206"

---

Day 4 complete: Short-term memory with reflection and pattern detection

New features:
- src/memory.py: ShortTermMemory class stores last 5 attempts
- Attempt dataclass with structured attempt data  
- Pattern detection: same_error, same_test_failure, no_progress
- Progress tracking: improving/regressing/stable/mixed
- build_reflection_prompt() analyzes failures before next attempt
- Agent sees warnings when repeating mistakes

Integration:
- Updated build_user_prompt() to use memory instead of plain history
- run_agent() creates memory, stores attempts, shows stats
- parse_test_results() extracts test data from output
- Memory summary displayed after each iteration

Example:
Before: Blind trial-and-error, repeats same mistakes
After: "⚠️ WARNING: Same test failing repeatedly. Focus on fixing that test."

Days completed: 4/7


## Security Notes

- `.env` is in `.gitignore` — your API key is never pushed to GitHub
- `venv/` is in `.gitignore` — dependencies are not pushed (they're reinstalled from scratch)
- `logs/` is in `.gitignore` — execution logs stay local
- `memory/` is in `.gitignore` — memory files stay local
- The executor restricts code to run only inside the `logs/` directory
- Static analysis blocks dangerous operations before execution

---

## Author

Ehindero Henry
AI Engineering learning project — Day 4 of building a self-improving coding agent.
Started: February 17, 2026
