# Self-Improving Coding Agent

> An autonomous agent that writes code, runs tests, and learns from failures.
> Built with Python + Claude API (Anthropic).

---

## Project Overview

This is an intermediate-level AI engineering project. The agent receives a goal, writes Python code to achieve it, executes that code safely, and if it fails — it reads the error, reflects on what went wrong, and tries again. It does not stop until the code works or it hits a maximum iteration limit.

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
| Day 2 | Execution sandbox with CPU/memory limits | 🔲 Upcoming |
| Day 3 | Test runner + structured failure detection | 🔲 Upcoming |
| Day 4 | Short-term memory + reflection mechanism | 🔲 Upcoming |
| Day 5 | Long-term memory with vector embeddings | 🔲 Upcoming |
| Day 6 | Circuit breaker + advanced safety layer | 🔲 Upcoming |
| Day 7 | Polish, CLI improvements, full demo | 🔲 Upcoming |

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

**Lesson:** Always check which Python version introduced a feature before using it. Type hints are cosmetic — removing them does not break functionality.

---

### Bug 2: Insufficient API credits
**Error:**
```
anthropic.BadRequestError: 400 - Your credit balance is too low
```

**Cause:** New Anthropic accounts need credits loaded before making API calls.

**Fix:** Add credits at https://console.anthropic.com → Settings → Billing. $5 is sufficient for development.

---

## Security Notes

- `.env` is in `.gitignore` — your API key is never pushed to GitHub
- `venv/` is in `.gitignore` — dependencies are not pushed (they're reinstalled from scratch)
- `logs/` is in `.gitignore` — execution logs stay local
- `memory/` is in `.gitignore` — memory files stay local
- The executor restricts code to run only inside the `logs/` directory
- Static analysis blocks dangerous operations before execution

---

## Important Concepts Learned (Day 1)

**Virtual environment:** An isolated Python installation for a specific project. Keeps dependencies from conflicting with other projects or your system Python. Always activate with `source venv/bin/activate` before working.

**python-dotenv:** Loads variables from a `.env` file into `os.environ`. The pattern `os.getenv("KEY")` then reads them. This is the standard way to handle secrets — never hardcode API keys.

**Subprocess execution:** Running code in a separate process means if the code crashes, it does not crash the agent. The parent process captures stdout and stderr and reports back.

**Dataclass:** A Python class decorated with `@dataclass` that automatically generates `__init__`, `__repr__`, and other boilerplate. Used for `ExecutionResult` to cleanly bundle multiple return values.

**Agentic loop:** The core pattern of autonomous AI systems. Instead of a single request-response, the agent acts, observes the result, and decides what to do next — repeatedly, until the goal is achieved.

**Conversation history:** Claude has no memory between API calls. To give it context, we send the full history of messages every time. This is how it "remembers" its previous attempts and errors.

---

## Author

Ehindero Henry
AI Engineering learning project — Day 1 of building a self-improving coding agent.
Started: February 17, 2026