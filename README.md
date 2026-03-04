# Self-Improving Coding Agent

> An autonomous AI agent that writes code, runs tests, learns from failures, and improves over time.

Built over 7 days as a hands on AI engineering project. Features production-grade sandboxing, test-driven development, memory systems, and automatic safety mechanisms.

-----

## Features

### Core Capabilities

- Autonomous Iteration - Tries, fails, reflects, and improves until success
- Test-Driven Development - Writes tests alongside code automatically
- Dual Memory System - Short-term (last 5 attempts) + long term (persistent across sessions)
- Pattern Detection - Identifies when stuck and changes strategy
- Learning from History - Retrieves similar past solutions for new problems

### Production Safety

- Circuit Breaker - Stops after 3 consecutive failures to prevent waste
- Rate Limiting - 20 API requests per minute maximum
- Sandboxed Execution - CPU (5s), memory (256MB), and file size (10MB) limits
- Advanced Safety Checks - Detects infinite loops and missing base cases
- Execution Tracking - Full audit trail for debugging

### Intelligence Features

- Similarity Search - Keyword-based matching finds relevant past solutions
- Reflection Mechanism - Analyzes failures before next attempt
- Progress Tracking - Monitors if improving, regressing, or stuck
- Cross-Session Learning - Remembers patterns across different goals

-----

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Anthropic API key (get one at console.anthropic.com)
- macOS or Linux (Windows WSL supported)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/coding-agent.git
cd coding-agent

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install anthropic python-dotenv rich

# 4. Configure API key
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# 5. Run the agent
python3 main.py --demo
```

### First Run

```bash
# Interactive mode
python3 main.py

# Direct mode
python3 main.py "write a function that calculates factorial with tests"

# Demo mode
python3 main.py --demo

# See examples
python3 main.py --examples

# View statistics
python3 main.py --stats
```

-----

## How It Works

### The Agent Loop

```
1. User gives goal
   "write a factorial function"
   
2. Check long-term memory
   Found: "fibonacci function" (40% similar)
   
3. Claude writes code + tests
   Uses past patterns as reference
   
4. Safety checks
   - Static analysis
   - Advanced pattern detection
   
5. Execute in sandbox
   CPU: 5s, Memory: 256MB, Files: 10MB
   
6. Run tests
   All 3 tests passed
   
7. Success! Save to long-term memory
   Solution stored for future reference
```

### When Tests Fail

```
Tests failed: 1/3 passed

Failed test: test_factorial_of_5
AssertionError: 206 != 120

Agent reflects:
"The bug is in the recursive call. I'm adding +1 when I shouldn't."

Tries again with fix → Success!
```

-----

## Architecture

### 7-Layer System

**Layer 1: CLI & User Interface**

- Entry point (main.py)
- Argument parsing
- Interactive mode

**Layer 2: Agent Loop**

- Prompt building (src/agent.py)
- API calls
- Iteration control

**Layer 3: Memory Systems**

- Short-term: Last 5 attempts (src/memory.py)
- Long-term: Persistent solutions (src/long_term_memory.py)

**Layer 4: Safety Systems**

- Circuit breaker (src/safety.py)
- Rate limiter
- Advanced checks

**Layer 5: Test Runner**

- unittest integration (src/test_runner.py)
- Structured results

**Layer 6: Code Executor**

- Subprocess isolation (src/executor.py)
- Resource limits

**Layer 7: Configuration**

- Settings (src/config.py)
- Environment variables (.env)

-----

## Usage Examples

### Example 1: Basic Function

```bash
python3 main.py "write a function that checks if a number is prime with tests"
```

Output:

```
Goal achieved in 2 iteration(s)!

Session stats: 2 attempts, 1 succeeded
Long-term memory: 1 solutions stored
Circuit breaker: 1 failures, success rate 50%
```

### Example 2: Algorithm

```bash
python3 main.py "write a function that implements binary search with tests"
```

### Example 3: Data Structure

```bash
python3 main.py "write a class that implements a stack with push, pop, and peek with tests"
```

### Demo Mode

```bash
python3 main.py --demo
```

Choose from pre-built examples:

1. Factorial function
1. Prime number checker
1. String reversal

### View Statistics

```bash
python3 main.py --stats
```

Output:

```
System Statistics:
• Solutions in long-term memory: 5
• Max iterations per goal: 5
• Short-term memory size: 5 attempts
• Circuit breaker threshold: 3 failures
• Rate limit: 20 requests/minute
```

-----

## Configuration

### Environment Variables (.env)

```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### System Configuration (src/config.py)

```python
# Model Settings
MODEL = "claude-sonnet-4-5-20250929"
MAX_ITERATIONS = 5
MAX_TOKENS = 4096

# Sandbox Configuration
CPU_TIME_LIMIT = 5  # seconds
MEMORY_LIMIT_MB = 256
FILE_SIZE_LIMIT_MB = 10
EXECUTION_TIMEOUT = 10

# Memory Configuration
SHORT_TERM_MEMORY_SIZE = 5
SIMILARITY_THRESHOLD = 0.3

# Safety Configuration
MAX_CONSECUTIVE_FAILURES = 3
MAX_API_REQUESTS = 20
RATE_LIMIT_WINDOW_SECONDS = 60
```

-----

## Safety Features

### Multi-Layer Protection

|Layer|Feature        |Protection                                       |
|-----|---------------|-------------------------------------------------|
|1    |Static Analysis|Blocks file operations, network access, eval/exec|
|2    |Advanced Checks|Detects infinite loops, missing base cases       |
|3    |CPU Limit      |5 seconds maximum compute time                   |
|4    |Memory Limit   |256MB maximum RAM usage                          |
|5    |File Size Limit|10MB maximum per file                            |
|6    |Circuit Breaker|Stops after 3 consecutive failures               |
|7    |Rate Limiter   |20 API requests per minute                       |

### What Gets Blocked

```python
# Blocked by static analysis
os.remove("file.txt")
import socket
eval("malicious_code")

# Blocked by advanced checks
while True:  # No break
    pass

def factorial(n):  # No base case
    return n * factorial(n-1)

# Blocked by resource limits
[0] * 10000000  # 10M elements
for i in range(10000000):  # 10M iterations
    pass
```

-----

## Project Structure

```
coding-agent/
├── src/
│   ├── __init__.py
│   ├── agent.py           # Main agent loop
│   ├── config.py          # Configuration
│   ├── executor.py        # Sandboxed execution
│   ├── memory.py          # Short-term memory
│   ├── long_term_memory.py # Persistent storage
│   ├── safety.py          # Safety systems
│   └── test_runner.py     # Test integration
├── memory/
│   └── solutions.json     # Stored solutions
├── logs/                  # Execution logs
├── screenshots/           # Project screenshots
├── main.py                # CLI entry point
├── .env                   # API key (gitignored)
├── .gitignore
├── requirements.txt
├── README.md
└── DAILY_LOG.md           # Development history
```

-----

## Development Timeline

|Day|Feature                                |Lines Added|
|---|---------------------------------------|-----------|
|1  |Foundation, basic agent loop, executor |594        |
|2  |Production sandbox with resource limits|166        |
|3  |Test runner with unittest integration  |205        |
|4  |Short-term memory + reflection         |318        |
|5  |Long-term memory with persistence      |286        |
|6  |Circuit breaker + advanced safety      |294        |
|7  |CLI polish + final documentation       |150        |

**Total:** ~2,013 lines of production code

-----

## Troubleshooting

### “API key not found”

```bash
# Make sure .env file exists
cat .env

# Should show: ANTHROPIC_API_KEY=sk-ant-...
```

### “Circuit breaker open”

```bash
# Reset by restarting the agent
# Or check why it's failing repeatedly
```

### “Rate limit exceeded”

```bash
# Wait 60 seconds
# Or increase limit in src/config.py
```

### “Module not found”

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install anthropic python-dotenv rich
```

-----

## Contributing

Contributions welcome! Please follow these steps:

1. Fork the repository
1. Create a feature branch (git checkout -b feature/amazing-feature)
1. Commit your changes (git commit -m ‘Add amazing feature’)
1. Push to the branch (git push origin feature/amazing-feature)
1. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/yourusername/coding-agent.git
cd coding-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

-----

-----

## Acknowledgments

- Built with Claude (Anthropic)
- Inspired by the 2026 AI Engineer Roadmap by @rohit4verse
- Part of my 300 Days of Code Challenge

-----

## Stats

- Development Time: 7 days
- Safety Layers: 7
- Memory Systems: 2

-----

## Links

- GitHub: https://github.com/Henry2005Max/coding-agent
- Author LinkedIn: [https://linkedin.com/in/yourprofile](https://www.linkedin.com/in/henry-ehindero-6aab57220?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=ios_app)

-----

Built with care as a learning project - March 2026
