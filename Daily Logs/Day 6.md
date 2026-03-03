## Day 6 — Circuit Breaker + Advanced Safety Layer

**Date:** March 3rd , 2026  
**Duration:** ..4 hours  
**Status:** ✅ Complete

### Goals

Add production-grade safety systems to prevent runaway failures, API abuse, and resource waste. Transform the agent from a prototype to a production-ready system.

### The Problem

**Days 1-5 behavior:**
The agent is smart but not robust. It can:

- Run indefinitely even when stuck (burns API credits)
- Make unlimited API requests (potential abuse)
- Execute dangerous code that basic static analysis misses
- Have no audit trail for debugging failures

**Real-world scenario:**

```
Monday: Agent gets stuck on a hard problem
Attempt 1: Fails
Attempt 2: Fails
Attempt 3: Fails
... continues for 20 attempts ...
Attempt 20: Still failing
→ $50 in API credits burned with zero progress
→ No safety mechanism to stop it
```

**What we needed:**

- Automatic stop after repeated failures (circuit breaker)
- Rate limiting to prevent API abuse
- Detection of dangerous patterns static analysis misses
- Execution tracking for debugging
- Production hardening

### The Solution: Multi-Layer Safety System

#### Architecture Overview

```
User gives goal
    ↓
Check circuit breaker (is it already open?)
    ↓
Check rate limiter (too many requests?)
    ↓
Generate code
    ↓
Basic static analysis (Day 1)
    ↓
Advanced safety check (NEW - Day 6)
    ↓
Execute code
    ↓
Record attempt in circuit breaker
    ↓
Success? → Reset and continue
Failure? → Check if circuit should open
```

### Implementation Details

#### 1. Circuit Breaker Pattern

**Concept:**
Like an electrical circuit breaker, it “trips” (opens) when detecting dangerous conditions, preventing further execution until manually reset.

**Three trigger conditions:**

**Trigger 1: Consecutive Failures**

```python
max_consecutive_failures = 3

if last_3_attempts.all_failed():
    circuit.open()
    reason = "3 consecutive failures"
```

**Trigger 2: High Failure Rate in Time Window**

```python
failure_window = 5 minutes
max_attempts_per_window = 10

if failures_in_last_5_min >= 8:  # 80% failure rate
    circuit.open()
    reason = "8/10 failures in 5 minutes"
```

**Why this matters:**

- Prevents wasting API credits on hopeless tasks
- Forces human intervention when agent is stuck
- Saves money and time

**Data structure:**

```python
@dataclass
class ExecutionAttempt:
    timestamp: datetime
    success: bool
    error_type: Optional[str]
```

Stores every execution attempt with timing and outcome. Used to calculate failure patterns.

**Circuit states:**

- **CLOSED** (normal): Agent can execute
- **OPEN** (tripped): Agent blocked from executing
- **Reason**: Why it opened (shown to user)

**Example output:**

```
🛑 CIRCUIT BREAKER OPEN
Reason: Circuit opened: 3 consecutive failures
The agent has been stopped to prevent further waste. Human intervention required.
```

#### 2. Rate Limiter

**Concept:**
Limits API requests per time window to prevent abuse and respect API quotas.

**Implementation:**
Uses a sliding window algorithm:

1. Track timestamps of all requests
1. On each new request, remove timestamps older than window
1. Count remaining requests
1. Allow if under limit, block if over

**Algorithm:**

```python
def can_proceed():
    now = datetime.now()
    
    # Remove old requests (outside 60-second window)
    requests = [r for r in requests if now - r < 60 seconds]
    
    if len(requests) >= 20:
        return False, "Rate limit exceeded. Wait X seconds."
    
    return True, ""
```

**Why sliding window?**
Better than fixed window (e.g., “20 per minute starting at :00”).

- Prevents burst at window boundaries
- More consistent enforcement
- Fair distribution over time

**Default limits:**

- 20 requests per 60 seconds
- Configurable in config.py

**Example output:**

```
🚫 RATE LIMIT EXCEEDED
Rate limit exceeded. Wait 42 seconds.
```

#### 3. Advanced Safety Checker

Goes beyond basic keyword matching (Day 1) to detect dangerous patterns through code analysis.

**Check 1: Infinite Loop Detection**

**Pattern 1: `while True` without break**

```python
# DANGEROUS
while True:
    print("Hello")

# SAFE
while True:
    if condition:
        break
```

**Detection:**

```python
if 'while True:' in code:
    if 'break' not in code and 'return' not in code:
        block("Infinite loop: while True without break")
```

**Pattern 2: Recursion without base case**

```python
# DANGEROUS
def factorial(n):
    return n * factorial(n - 1)  # No base case!

# SAFE
def factorial(n):
    if n <= 1:  # Base case
        return 1
    return n * factorial(n - 1)
```

**Detection:**

```python
# 1. Find all function definitions
functions = re.findall(r'def (\w+)\(', code)

# 2. For each function
for func_name in functions:
    # 3. Check if function calls itself
    if func_name in function_body:
        # 4. Check for base case (if + return)
        if 'if' not in early_lines or 'return' not in early_lines:
            block("Infinite recursion: no base case")
```

**Why this works:**
Most recursive functions follow the pattern:

```python
def recursive(n):
    if base_case:  # Always near the top
        return value
    return recursive(modified_n)
```

We check if this pattern exists in the first ~200 characters.

**Check 2: Resource Abuse Detection**

**Pattern 1: Large allocations**

```python
# DANGEROUS: Tries to allocate 10 million elements
big_list = [0] * 10000000
```

**Detection:**

```python
pattern = r'\[\s*\d+\s*\]\s*\*\s*\d{6,}'  # [X] * 1000000+
if re.search(pattern, code):
    block("Large list allocation (millions of elements)")
```

**Pattern 2: Expensive loops**

```python
# DANGEROUS: 10 million iterations
for i in range(10000000):
    process(i)
```

**Detection:**

```python
pattern = r'for.+range\(\s*\d{6,}'  # range(1000000+)
if re.search(pattern, code):
    block("Loop with 1M+ iterations")
```

**Why regex patterns?**

- Fast (no AST parsing needed)
- Catches common mistakes
- Easy to add new patterns
- Works on incomplete code

**Combined check:**

```python
is_safe, warnings = AdvancedSafetyChecker.check_all(code)

if not is_safe:
    print("⚠️ ADVANCED SAFETY WARNING:")
    for warning in warnings:
        print(f"  - {warning}")
    skip_execution()
```

### Integration Into Agent

#### Updated `run_agent()` Flow

**Before Day 6:**

```python
for iteration in range(MAX_ITERATIONS):
    call_api()
    execute_code()
    if success:
        return
```

**After Day 6:**

```python
circuit_breaker = CircuitBreaker()
rate_limiter = RateLimiter()

for iteration in range(MAX_ITERATIONS):
    # Check circuit breaker
    if circuit_breaker.is_open:
        print("🛑 CIRCUIT BREAKER OPEN")
        break
    
    # Check rate limiter
    if not rate_limiter.can_proceed():
        print("🚫 RATE LIMIT EXCEEDED")
        break
    
    rate_limiter.record_request()
    
    call_api()
    
    # Basic safety
    if not is_code_safe(code):
        continue
    
    # Advanced safety (NEW)
    is_safe, warnings = AdvancedSafetyChecker.check_all(code)
    if not is_safe:
        print(f"⚠️ SAFETY WARNING: {warnings}")
        circuit_breaker.record_attempt(success=False)
        continue
    
    execute_code()
    circuit_breaker.record_attempt(success=result.success)
```

**Key changes:**

1. Create safety instances at start
1. Check circuit breaker before each iteration
1. Check rate limiter before API calls
1. Run advanced safety after basic checks
1. Record all attempts in circuit breaker
1. Show safety stats in final summary

#### New Status Display

**During execution:**

```
--- Iteration 3/5 ---
Memory: 0 succeeded, 2 failed | Progress: regressing
[Calling Claude API...]
```

**On circuit breaker trip:**

```
🛑 CIRCUIT BREAKER OPEN
Reason: Circuit opened: 3 consecutive failures
The agent has been stopped to prevent further waste. Human intervention required.
```

**On success:**

```
✅ Goal achieved in 2 iteration(s)!

Session stats: 2 attempts, 1 succeeded
Long-term memory: 5 solutions stored
Circuit breaker: 1 failures, success rate 50%
```

### Files Created/Modified

**New file:**

- `src/safety.py` — 235 lines

**Modified files:**

- `src/agent.py` — Integrated safety systems into run_agent (+50 lines)
- `src/config.py` — Added safety configuration constants (+9 lines)

**Total new code:** ~294 lines

### Testing Results

#### Test 1: Circuit Breaker

```python
cb = CircuitBreaker(max_consecutive_failures=3)

cb.record_attempt(success=False)  # Failure 1
print(cb.get_status())
# {'status': 'closed', 'failures': 1}

cb.record_attempt(success=False)  # Failure 2
print(cb.get_status())
# {'status': 'closed', 'failures': 2}

cb.record_attempt(success=False)  # Failure 3
print(cb.get_status())
# {'status': 'open', 'reason': '3 consecutive failures', 'failures': 3}

print(cb.is_open)  # True
```

✅ Circuit opens after exactly 3 failures  
✅ Provides clear reason  
✅ Status tracking works

#### Test 2: Rate Limiter

```python
rl = RateLimiter(max_requests=3, window_seconds=60)

for i in range(4):
    can_proceed, msg = rl.can_proceed()
    if can_proceed:
        rl.record_request()
        print(f"Request {i+1}: Allowed")
    else:
        print(f"Request {i+1}: {msg}")

# Output:
# Request 1: Allowed
# Request 2: Allowed
# Request 3: Allowed
# Request 4: Rate limit exceeded. Wait 59 seconds.
```

✅ Allows exactly 3 requests  
✅ Blocks 4th request  
✅ Calculates wait time correctly

#### Test 3: Infinite Loop Detection

```python
code = """
while True:
    print("Hello")
"""

is_safe, warnings = AdvancedSafetyChecker.check_all(code)
print(f"Safe: {is_safe}")
print(f"Warnings: {warnings}")

# Output:
# Safe: False
# Warnings: ["Potential infinite loop: 'while True' without break or return"]
```

✅ Detects `while True` without break  
✅ Returns clear warning message

#### Test 4: Missing Base Case Detection

```python
code = """
def factorial(n):
    return n * factorial(n - 1)
"""

is_safe, warnings = AdvancedSafetyChecker.check_all(code)
print(f"Safe: {is_safe}")
print(f"Warnings: {warnings}")

# Output:
# Safe: False
# Warnings: ["Potential infinite recursion in 'factorial': no obvious base case"]
```

✅ Detects recursion without base case  
✅ Identifies specific function name

#### Test 5: Safe Recursive Code

```python
code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""

is_safe, warnings = AdvancedSafetyChecker.check_all(code)
print(f"Safe: {is_safe}")

# Output:
# Safe: True
```

✅ Correctly identifies safe code  
✅ No false positives

### Concepts Learned

**Circuit breaker pattern:**
A design pattern from electrical engineering applied to software. Prevents cascading failures by automatically “breaking the circuit” when detecting problems.

**Common in:**

- Microservices (prevent calling failing services)
- Payment systems (stop retrying failed transactions)
- API clients (back off when rate limited)

**Sliding window algorithm:**
Better than fixed windows for rate limiting. Example:

- Fixed window: 20/minute starting at :00 → can get 40 requests in 2 seconds (20 at :59, 20 at :00)
- Sliding window: 20/minute → always enforces 20 per any 60-second span

**Static analysis vs dynamic analysis:**

- **Static**: Analyze code without running it (what we do)
- **Dynamic**: Analyze code while running it (profiling, debugging)

Our advanced safety checker is static analysis using:

- Regex pattern matching
- Simple string searching
- Keyword detection

**Trade-offs:**

- ✅ Fast (no execution needed)
- ✅ Safe (can’t harm system)
- ✅ Catches obvious mistakes
- ❌ Can’t catch all bugs (semantic issues, logic errors)
- ❌ False positives possible (safe code that looks dangerous)

**Audit trail:**
Recording every execution attempt creates a log for debugging. If agent fails mysteriously, you can see:

- How many attempts were made
- What errors occurred
- When circuit breaker triggered
- Rate limit violations

**Production hardening:**
The process of adding reliability, monitoring, and safety to prototype code:

- Error handling
- Rate limiting
- Circuit breakers
- Logging/metrics
- Graceful degradation

This is what separates toy projects from production systems.

### Why This Matters

**Before Day 6:**
Agent is a brilliant prototype that can waste unlimited money and get stuck forever.

**After Day 6:**
Agent is production-ready with automatic safety nets.

**Real-world impact:**

**Scenario 1: Student project**

- Day 5 agent: Fine (you’re watching it)
- Day 6 agent: Overkill but educational

**Scenario 2: Production deployment**

- Day 5 agent: Dangerous (could burn $1000 overnight)
- Day 6 agent: Safe (automatic limits and shutoffs)

**Scenario 3: Open source release**

- Day 5 agent: Irresponsible (users could hurt themselves)
- Day 6 agent: Responsible (built-in guardrails)

**Cost comparison:**
Without circuit breaker:

- 20 failed attempts × $0.50/attempt = $10 wasted

With circuit breaker:

- 3 failed attempts × $0.50/attempt = $1.50, then stops
- Savings: $8.50 per stuck problem

Over 100 problems with 10% getting stuck:

- Without: $100 wasted
- With: $15 wasted
- **Savings: $85**

### Commands Used

```bash
# Navigate and activate
cd ~/coding-agent
source venv/bin/activate

# Create safety module
touch src/safety.py
open -e src/safety.py
# (Pasted implementation, fixed Python 3.9 compatibility issues)

# Test module loading
python3 -c "from src.safety import CircuitBreaker, RateLimiter, AdvancedSafetyChecker; print('Safety module loaded OK')"

# Test circuit breaker
python3 << 'EOF'
from src.safety import CircuitBreaker

cb = CircuitBreaker(max_consecutive_failures=3)
cb.record_attempt(success=False)
cb.record_attempt(success=False)
cb.record_attempt(success=False)

print(f"Circuit open: {cb.is_open}")
print(f"Reason: {cb.open_reason}")
print(f"Status: {cb.get_status()}")
EOF

# Test rate limiter
python3 << 'EOF'
from src.safety import RateLimiter

rl = RateLimiter(max_requests=3, window_seconds=60)
for i in range(4):
    can_proceed, msg = rl.can_proceed()
    if can_proceed:
        rl.record_request()
        print(f"Request {i+1}: Allowed")
    else:
        print(f"Request {i+1}: {msg}")
EOF

# Test advanced safety checker
python3 << 'EOF'
from src.safety import AdvancedSafetyChecker

# Test infinite loop detection
code1 = "while True:\n    print('Hello')"
safe, warnings = AdvancedSafetyChecker.check_all(code1)
print(f"Infinite loop safe: {safe}, Warnings: {warnings}")

# Test safe recursive code
code2 = "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)"
safe, warnings = AdvancedSafetyChecker.check_all(code2)
print(f"Safe factorial: {safe}")

# Test unsafe recursive code
code3 = "def factorial(n):\n    return n * factorial(n-1)"
safe, warnings = AdvancedSafetyChecker.check_all(code3)
print(f"Unsafe factorial safe: {safe}, Warnings: {warnings}")
EOF

# Update agent
open -e src/agent.py
# (Added import, integrated safety into run_agent)

# Test integration
python3 -c "from src.agent import run_agent; print('Agent with safety systems loaded OK')"

# Update config
open -e src/config.py
# (Added MAX_CONSECUTIVE_FAILURES, MAX_API_REQUESTS, etc.)

# Verify all components
python3 -c "
from src.agent import run_agent
from src.safety import CircuitBreaker, RateLimiter, AdvancedSafetyChecker
from src.config import MAX_CONSECUTIVE_FAILURES, MAX_API_REQUESTS
print('✅ All Day 6 components loaded')
print(f'✅ Circuit breaker: Opens after {MAX_CONSECUTIVE_FAILURES} failures')
print(f'✅ Rate limiter: {MAX_API_REQUESTS} requests per minute')
"

# Manual GitHub upload
# Uploaded: src/safety.py (new), src/agent.py (modified), src/config.py (modified)
```

### Challenges Encountered

**Challenge 1: Python 3.9 f-string compatibility**
First implementation used `rf'def {func_name}\([^)]*\):[^}]+'` which breaks in Python 3.9.

**Solution:** Replaced with string concatenation:

```python
# Before (Python 3.10+)
pattern = rf'def {func_name}\([^)]*\):'

# After (Python 3.9 compatible)
pattern = 'def ' + func_name + '\\([^)]*\\):'
```

**Lesson:** Always test on target Python version. f-strings evolved significantly from 3.9 to 3.10+.

**Challenge 2: Deciding on circuit breaker thresholds**
Too low (1 failure) = opens too easily, prevents legitimate retries  
Too high (10 failures) = wastes too much money before stopping

**Solution:** Settled on 3 consecutive failures as default, configurable in config.py.

**Reasoning:**

- 1 failure = might be transient error
- 2 failures = could still be bad luck
- 3 failures = clear pattern, time to stop

**Challenge 3: Balancing safety vs flexibility**
Too strict = blocks valid code  
Too loose = allows dangerous code

**Solution:** Layered approach:

- Basic checks (strict): Block obvious dangers
- Advanced checks (moderate): Warn about suspicious patterns but explain why
- Circuit breaker (adaptive): Learns from repeated failures

### Improvement Over Days 1-5

|Aspect              |Days 1-5                   |Day 6                             |
|--------------------|---------------------------|----------------------------------|
|Failure handling    |Retry until max iterations |Stop after 3 consecutive failures |
|API protection      |None                       |20 requests/minute limit          |
|Loop detection      |Basic keyword search       |Pattern analysis + recursion check|
|Cost control        |Can waste unlimited credits|Automatic shutoff on problems     |
|Audit trail         |JSON logs only             |Full execution tracking           |
|Production readiness|Prototype                  |Production-ready                  |

**Key insight:** Adding safety systems transforms a clever prototype into a responsible production system that can be deployed, shared, and trusted.

### Next Steps (Day 7)

- CLI improvements and argument parsing
- Better error messages and help text
- Configuration file support
- Demo mode with example problems
- Final polish and documentation
- Comprehensive README update
- Release preparation

-----

*Last updated: February 24, 2026*
