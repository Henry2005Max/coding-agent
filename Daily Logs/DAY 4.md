## Day 4 — Short-Term Memory + Reflection Mechanism

**Date:** February 24, 2026  
**Duration:** ~3 hours  
**Status:** ✅ Complete

### Goals
Give the agent the ability to remember its last 5 attempts, detect patterns in failures, and reflect before trying again.

### The Problem

**Days 1-3 behavior:**
Agent has conversation history (sees previous attempts in same session), but doesn't actively *analyze patterns*. It might make the same mistake 3 times without realizing it's stuck.

**Example of what we needed to prevent:**
```
Attempt 1: Forgot base case → RecursionError
Attempt 2: Fixed base case wrong → RecursionError  
Attempt 3: Still wrong base case → RecursionError
Attempt 4: Finally gets it right
```

**What we wanted:**
```
Attempt 1: Forgot base case → RecursionError
Attempt 2: Still RecursionError
⚠️ WARNING: Same error twice. Try a different approach.
Attempt 3: Uses completely different strategy → Success
```

### The Solution: Memory + Reflection System

#### 1. Short-Term Memory (`ShortTermMemory` class)
Stores the last N attempts (default: 5) with full structured data.

**Features:**
- Stores `Attempt` dataclass with: iteration, code, success, output, error, test_results, timestamp
- Automatically removes oldest when limit reached (FIFO queue)
- Methods: `add()`, `get_all()`, `get_recent(n)`, `clear()`, `count()`
- JSON serialization for persistence

#### 2. Attempt Dataclass
Structured storage for each attempt:

```python
@dataclass
class Attempt:
    iteration: int
    code: str
    success: bool
    output: str
    error: str
    test_results: Optional[dict] = None  # {total, passed, failed, failures: [...]}
    timestamp: str = ""
```

**Why `test_results` is a dict:**
Stores parsed test data from executor:
- `total_tests`: how many tests ran
- `passed`: how many passed
- `failed`: how many failed
- `failures`: list of dicts with `test_name` and `message`

#### 3. Pattern Detection
Three types of patterns detected:

**Pattern 1: `same_error`**
- Checks if last 2 attempts failed with identical error message (first line)
- Use case: Agent is stuck in a loop, needs to try different approach

**Pattern 2: `same_test_failure`**
- Checks if same test name appears in failures of last 2 attempts
- Use case: Agent keeps failing the same test, needs to focus on that specific case

**Pattern 3: `no_progress`**
- Checks if last 3 attempts all had zero passing tests
- Use case: Agent should scrap current approach and start fresh

**Implementation:**
```python
def has_pattern(self, pattern_type: str) -> bool:
    if pattern_type == 'same_error' and len(self.attempts) >= 2:
        last_two = self.attempts[-2:]
        if not last_two[0].success and not last_two[1].success:
            error1 = last_two[0].error.split('\n')[0]
            error2 = last_two[1].error.split('\n')[0]
            return error1 == error2
    # ... other patterns
```

#### 4. Progress Tracking
Calculates if agent is making progress:

**Progress states:**
- `improving` — test pass count increasing over last 3 attempts
- `regressing` — test pass count decreasing
- `mixed` — has both execution errors and test failures (moving from crashes to logic bugs = progress)
- `stable` — same performance across attempts
- `insufficient_data` — fewer than 2 attempts

**Algorithm:**
```python
def _calculate_progress(self) -> str:
    recent = self.attempts[-3:]
    
    # Check if tests are improving
    if all(a.test_results for a in recent):
        passed_counts = [a.test_results.get('passed', 0) for a in recent]
        if passed_counts == sorted(passed_counts):
            return "improving"
        elif passed_counts == sorted(passed_counts, reverse=True):
            return "regressing"
    
    # Moving from crashes to test failures is progress
    has_execution_error = any(not a.test_results and not a.success for a in recent)
    has_test_failures = any(a.test_results and not a.success for a in recent)
    if has_execution_error and has_test_failures:
        return "mixed"
    
    return "stable"
```

#### 5. Reflection Prompt Builder
`build_reflection_prompt(memory)` generates a detailed analysis before each attempt.

**Components:**
1. **Attempt count and progress status**
   ```
   You have made 2 attempt(s) so far.
   Progress status: improving
   ```

2. **Pattern warnings** (if detected)
   ```
   ⚠️ WARNING: You've had the same error in your last 2 attempts. 
   Try a completely different approach.
   ```

3. **Recent attempt summary** (last 3)
   ```
   Attempt 1: ❌ FAILED
     Tests: 0/2 passed
     Failed tests:
       - test_factorial_of_5: AssertionError: 206 != 120
     Error: AssertionError: 206 != 120
   ```

4. **Reflection questions**
   ```
   Before writing new code, ask yourself:
   1. What specifically went wrong in the last attempt?
   2. Am I repeating the same approach? Should I try something different?
   3. Are there edge cases I'm missing?
   ```

### Integration Into Agent

#### Updated `build_user_prompt()`
**Before Day 4:**
```python
def build_user_prompt(goal: str, history: list) -> str:
    prompt = f"Goal: {goal}\n\n"
    for attempt in history:
        prompt += f"Code: {attempt['code']}\n"
        prompt += f"Error: {attempt['error']}\n"
    return prompt
```

**After Day 4:**
```python
def build_user_prompt(goal: str, memory: ShortTermMemory) -> str:
    prompt = f"Goal: {goal}\n\n"
    
    if memory.count() == 0:
        prompt += "This is your first attempt."
    else:
        # Add reflection analysis
        prompt += build_reflection_prompt(memory)
        
        # Add structured history
        for attempt in memory.get_all():
            prompt += format_attempt(attempt)  # Includes test results
    
    return prompt
```

#### Updated `run_agent()`
**Key changes:**
1. Creates `ShortTermMemory` instance at start
2. Stores each attempt with `memory.add(Attempt(...))`
3. Shows memory summary after each iteration
4. Includes reflection in prompt building
5. Parses test results from executor output
6. Shows final stats when complete

**New features in loop:**
```python
# Show memory summary
if memory.count() > 0:
    summary = memory.get_summary()
    console.print(f"Memory: {summary['successful_attempts']} succeeded, "
                  f"{summary['failed_attempts']} failed | "
                  f"Progress: {summary['progress']}")

# Store attempt after execution
memory.add(Attempt(
    iteration=iteration,
    code=code,
    success=result.success,
    output=result.output,
    error=result.error,
    test_results=parse_test_results(result)
))
```

#### New Helper: `parse_test_results()`
Extracts structured test data from executor output.

**What it does:**
- Uses regex to find "X/Y passed" pattern
- Extracts failure details with test names and messages
- Returns dict with `total_tests`, `passed`, `failed`, `failures`
- Returns `None` if no test data found

**Example parsing:**
```
Input: "Tests failed: 1/2 passed\n\n❌ test_five\n   AssertionError: 206 != 120"

Output: {
    'total_tests': 2,
    'passed': 1,
    'failed': 1,
    'failures': [{
        'test_name': 'test_five',
        'message': 'AssertionError: 206 != 120'
    }]
}
```

### Files Created/Modified

**New file:**
- `src/memory.py` — 235 lines

**Modified files:**
- `src/agent.py` — Updated `build_user_prompt()` to use memory, rewrote `run_agent()` to integrate memory, added `parse_test_results()` (+80 lines)
- `src/config.py` — Added `SHORT_TERM_MEMORY_SIZE = 5` (+3 lines)

**Total new code:** ~318 lines

### Testing Results

#### Test 1: Memory Storage
```python
memory = ShortTermMemory(max_size=5)

memory.add(Attempt(
    iteration=1,
    code="def factorial(n):\n    return n * factorial(n-1)",
    success=False,
    output="",
    error="RecursionError: maximum recursion depth exceeded"
))

memory.add(Attempt(
    iteration=2,
    code="def factorial(n):\n    if n == 0:\n        return 0\n    return n * factorial(n-1)",
    success=False,
    output="",
    error="AssertionError: 0 != 1",
    test_results={'total_tests': 2, 'passed': 1, 'failed': 1, 'failures': [...]}
))

print(memory.get_summary())
```

**Output:**
```python
{
    'total_attempts': 2,
    'successful_attempts': 0,
    'failed_attempts': 2,
    'most_recent_error': 'AssertionError: 0 != 1',
    'progress': 'mixed'
}
```

✅ Memory stores attempts correctly  
✅ Progress tracking working (mixed = has both crashes and test failures)

#### Test 2: Pattern Detection
```python
# Same test failing twice
memory.add(Attempt(
    iteration=1,
    test_results={'failures': [{'test_name': 'test_add', 'message': '...'}]}
))
memory.add(Attempt(
    iteration=2,
    test_results={'failures': [{'test_name': 'test_add', 'message': '...'}]}
))

print(memory.has_pattern('same_test_failure'))  # True
```

✅ Detects when same test fails repeatedly

#### Test 3: Reflection Prompt
```python
prompt = build_reflection_prompt(memory)
print(prompt)
```

**Output:**
```
## Reflection on Previous Attempts

You have made 2 attempt(s) so far.
Progress status: improving

⚠️ WARNING: The same test is failing repeatedly. Focus specifically on fixing that test.

Recent attempts:

Attempt 1: ❌ FAILED
  Tests: 0/1 passed
  Failed tests:
    - test_add: expected 5, got -1
  Error: Test failed: expected 5, got -1

Attempt 2: ❌ FAILED
  Tests: 0/1 passed
  Failed tests:
    - test_add: expected 5, got 6
  Error: Test failed: expected 5, got 6

Before writing new code, ask yourself:
1. What specifically went wrong in the last attempt?
2. Am I repeating the same approach? Should I try something different?
3. Are there edge cases I'm missing?
```

✅ Detailed analysis of past attempts  
✅ Pattern warning displayed  
✅ Reflection questions prompt better thinking

#### Test 4: Integration
```python
from src.agent import build_user_prompt
from src.memory import ShortTermMemory, Attempt

memory = ShortTermMemory()
memory.add(Attempt(
    iteration=1,
    code="def add(a, b):\n    return a - b",
    success=False,
    error="Test failed: expected 5, got -1",
    test_results={'total_tests': 1, 'passed': 0, 'failed': 1, 'failures': [...]}
))

prompt = build_user_prompt("write a function that adds two numbers", memory)
print(prompt)
```

**Output includes:**
- Goal statement
- Reflection with warnings
- Full attempt history with code and errors
- Instruction to analyze and fix

✅ Full integration working

### Concepts Learned

**Short-term memory vs long-term memory:**
- **Short-term:** Last N attempts, stored in RAM, cleared when agent stops
- **Long-term:** (Day 5) Successful patterns stored permanently, retrieved for similar problems

**FIFO queue (First In, First Out):**
When memory is full, oldest attempt is removed when new one added. Like a sliding window over recent attempts.

**Pattern detection vs rule-based logic:**
We detect patterns by comparing attempt data, not by hardcoding specific error messages. This makes it generalize to any type of error.

**Progress as a metric:**
Not just "did it succeed?", but "is it getting closer?" Tracking test pass counts over time shows improvement even without full success.

**Reflection prompts:**
By explicitly asking the agent questions ("What went wrong? Are you repeating yourself?"), we nudge it toward meta-cognition and better strategies.

**Structured data enables intelligence:**
Storing test results as structured dicts (not just strings) enables:
- Counting passed tests
- Identifying specific failing tests
- Detecting repeated failures
- Tracking progress

**Memory as a teaching tool:**
The reflection prompt isn't just data — it's a teaching moment. The agent learns from its own history.

### Why This Matters

**Before Day 4:**
```
Agent tries approach A → fails
Agent tries approach A with small change → fails
Agent tries approach A with another small change → fails
Agent tries approach A again → fails
Agent finally tries approach B → succeeds
```

Wasteful, slow, frustrating.

**After Day 4:**
```
Agent tries approach A → fails
Agent tries approach A with small change → fails
⚠️ WARNING: Same error twice. Try a different approach.
Agent tries approach B → succeeds
```

Efficient, fast, intelligent.

**Real-world impact:**
- Fewer wasted API calls (saves money)
- Faster convergence to solution
- More human-like problem solving
- Clear visibility into agent's learning process

### Commands Used

```bash
# Create memory module
touch src/memory.py
open -e src/memory.py

# Test memory system
python3 -c "from src.memory import ShortTermMemory, Attempt, build_reflection_prompt; print('Memory module loaded OK')"

# Update agent
open -e src/agent.py
# (Added import, updated build_user_prompt, rewrote run_agent)

# Test integration
python3 -c "from src.agent import build_user_prompt; print('build_user_prompt updated OK')"
python3 -c "from src.agent import run_agent; print('Agent with memory loaded OK')"

# Test reflection prompt
python3 << 'EOF'
from src.memory import ShortTermMemory, Attempt, build_reflection_prompt
memory = ShortTermMemory()
memory.add(Attempt(iteration=1, code="...", success=False, error="RecursionError"))
memory.add(Attempt(iteration=2, code="...", success=False, error="AssertionError", test_results={...}))
print(memory.get_summary())
print(build_reflection_prompt(memory))
EOF

# Test full integration
touch test_memory_integration.py
python3 test_memory_integration.py
rm test_memory_integration.py

# Update config
open -e src/config.py
# (Added SHORT_TERM_MEMORY_SIZE = 5)

# Verify all components
python3 -c "
from src.agent import run_agent
from src.memory import ShortTermMemory, Attempt, build_reflection_prompt
from src.config import SHORT_TERM_MEMORY_SIZE
print('✅ All Day 4 components loaded')
print(f'✅ Memory size configured: {SHORT_TERM_MEMORY_SIZE}')
print('✅ Reflection system ready')
"

# Commit (had git issues, manual upload instead)
git add .
git commit -m "Day 4: short-term memory with reflection and pattern detection"
```

### Improvement Over Days 1-3

| Aspect | Days 1-3 | Day 4 |
|--------|----------|-------|
| Memory | Conversation history only | Structured short-term memory |
| Pattern awareness | None | Detects repeated errors and tests |
| Progress tracking | Binary (success/fail) | Quantified (improving/regressing/mixed) |
| Reflection | None | Explicit analysis before each attempt |
| Warnings | None | Alerts when stuck in loops |
| Learning | Passive | Active meta-cognition |

**Key insight:** Adding memory + reflection transforms the agent from a blind trial-and-error system into a learning system that improves its strategy over time.

### Next Steps (Day 5)
- Long-term memory with vector embeddings
- Store successful solutions permanently
- Retrieve similar past solutions for new problems
- Cross-session learning (agent remembers across different goals)
- Similarity search using embeddings

---

*Last updated: February 24, 2026*
