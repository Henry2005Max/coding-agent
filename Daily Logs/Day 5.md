## Day 5 — Long-Term Memory with Persistent Learning

**Date:** March 2, 2026   
**Status:** ✅ Complete

### Goals

Add persistent memory that survives across sessions. Enable the agent to learn from past successes and retrieve similar solutions for new problems.

### The Problem

**Days 1-4 behavior:**
Every time the agent stops, memory is wiped. Each new session starts from zero. If you solve factorial today and fibonacci tomorrow, the agent doesn’t remember the recursive pattern it learned.

**Example of waste:**

```
Monday: Goal = "write factorial function"
Agent tries 3 times, finally succeeds with recursion

Tuesday: Goal = "write fibonacci function"  
Agent tries 3 times again, discovers recursion works
```

The agent solved the same conceptual problem (recursion) twice without learning.

**What we needed:**

- Store successful solutions permanently
- Retrieve similar past solutions for new problems
- Learn patterns across sessions
- Build a knowledge base over time

### The Solution: Persistent Long-Term Memory

Instead of expensive vector embeddings (which require PyTorch/TensorFlow), we built a **keyword-based similarity system** that’s:

- Lightweight (no ML dependencies)
- Fast (keyword matching is instant)
- Effective for code (keywords matter more than semantics)
- Easy to understand and debug

#### Architecture Overview

```
User gives goal → Agent checks long-term memory
                ↓
    Found similar solutions? 
                ↓
    YES: Include in prompt as examples
                ↓
    Agent writes code using past patterns
                ↓
    Success? → Save to long-term memory
```

### Implementation Details

#### 1. Solution Dataclass

Structured storage for successful attempts:

```python
@dataclass
class Solution:
    goal: str                    # Original problem statement
    code: str                    # The working code
    test_results: dict           # How many tests passed
    timestamp: str               # When it was solved
    keywords: List[str]          # Extracted for matching
    iterations_to_solve: int     # How hard was it?
```

**Why store iterations_to_solve?**
If a problem took 5 iterations, that tells us it was hard. When we retrieve it later, we can warn: “This is a complex pattern.”

#### 2. Keyword Extraction

Convert natural language goals into searchable keywords.

**Algorithm:**

```python
def extract_keywords(text: str) -> List[str]:
    # 1. Lowercase everything
    # 2. Extract words (alphanumeric only)
    # 3. Remove stop words (the, and, or, is, etc.)
    # 4. Remove very short words (< 3 chars)
    # 5. Remove duplicates
    # 6. Return unique keywords
```

**Example:**

```
Input: "write a function that calculates factorial of a number"
Output: ['function', 'calculates', 'factorial', 'number']
```

**Why this works:**
For code problems, keywords like “factorial”, “recursion”, “loop”, “sort” capture the essence better than full semantic embeddings.

#### 3. Similarity Calculation

Use **Jaccard similarity**: intersection / union of keyword sets.

**Formula:**

```
similarity = |keywords1 ∩ keywords2| / |keywords1 ∪ keywords2|
```

**Example:**

```python
goal1 = "write factorial function"
keywords1 = ['factorial', 'function']

goal2 = "write fibonacci function"  
keywords2 = ['fibonacci', 'function']

intersection = {'function'}  # 1 word in common
union = {'factorial', 'fibonacci', 'function'}  # 3 total unique words

similarity = 1/3 = 0.33 = 33%
```

**Why Jaccard?**

- Simple and fast
- Works well for short texts (goals are usually 5-10 words)
- Intuitive: more shared keywords = higher similarity
- No need for ML models or training data

#### 4. LongTermMemory Class

**Core methods:**

**`add(solution)`**

- Appends solution to list
- Saves to `memory/solutions.json` immediately
- Persistent across sessions

**`find_similar(goal, top_k=3, min_similarity=0.2)`**

- Extracts keywords from new goal
- Calculates similarity to all stored solutions
- Filters by minimum threshold (default 20%)
- Returns top K matches sorted by similarity

**`save()` and `load()`**

- JSON serialization for persistence
- Loads on initialization
- Saves after every addition

**Storage format:**

```json
[
  {
    "goal": "write a factorial function",
    "code": "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)",
    "test_results": {"total_tests": 3, "passed": 3, "failed": 0},
    "timestamp": "2026-02-24T14:00:00",
    "keywords": ["factorial", "function"],
    "iterations_to_solve": 2
  }
]
```

#### 5. Retrieval Context Builder

Formats similar solutions into a readable prompt section.

**Output example:**

```
## 💡 Relevant Past Solutions

I found similar problems I've solved before:

**Similar Solution 1** (similarity: 40%)
Goal: write a factorial function
Solved in: 2 iteration(s)
Code approach:
```python
def factorial(n):
    return 1 if n <= 1 else n * factorial(n-1)
...
```

Tests passed: 3/3

💡 Tip: You can adapt patterns from these solutions, but make sure to write tests for the new goal.

```
This gets injected into the agent's prompt BEFORE it writes code.

### Integration Into Agent

#### Updated `build_user_prompt()`

**New signature:**
```python
def build_user_prompt(goal: str, memory: ShortTermMemory, long_term_memory: LongTermMemory) -> str:
```

**New section added:**

```python
# Check for similar past solutions
similar = long_term_memory.find_similar(goal, top_k=2, min_similarity=0.3)
if similar:
    prompt += build_retrieval_context(similar)
```

Now the prompt includes:

1. Similar past solutions (if any)
1. Reflection on current attempts (short-term memory)
1. Full history of this session
1. Instructions to analyze and fix

#### Updated `run_agent()`

**On startup:**

```python
long_term_memory = LongTermMemory()

# Check for similar solutions
similar = long_term_memory.find_similar(goal, top_k=2, min_similarity=0.3)
if similar:
    console.print(f"💡 Found {len(similar)} similar past solution(s)")
    for solution, similarity in similar:
        console.print(f"  - '{solution.goal}' (similarity: {similarity:.0%})")
```

**On success:**

```python
if result.success:
    # Store in long-term memory
    solution = Solution(
        goal=goal,
        code=code,
        test_results=test_results,
        timestamp=datetime.now().isoformat(),
        keywords=[],  # Auto-generated by dataclass
        iterations_to_solve=iteration
    )
    long_term_memory.add(solution)
    console.print("💾 Solution saved to long-term memory")
```

**On completion:**

```python
ltm_stats = long_term_memory.get_stats()
console.print(f"Long-term memory: {ltm_stats['total_solutions']} solutions stored")
```

### Files Created/Modified

**New file:**

- `src/long_term_memory.py` — 235 lines

**Modified files:**

- `src/agent.py` — Added long_term_memory parameter to build_user_prompt, updated run_agent to use LongTermMemory (+45 lines)
- `src/config.py` — Added LONG_TERM_MEMORY_PATH, SIMILARITY_THRESHOLD, MAX_SIMILAR_SOLUTIONS (+6 lines)

**Total new code:** ~286 lines

### Testing Results

#### Test 1: Keyword Extraction

```python
goal1 = "write a function that calculates factorial of a number"
goal2 = "write a function that computes fibonacci sequence"
goal3 = "write a factorial function with recursion"

keywords1 = extract_keywords(goal1)
# Output: ['number', 'factorial', 'function', 'calculates']

keywords2 = extract_keywords(goal2)
# Output: ['fibonacci', 'computes', 'function', 'sequence']

keywords3 = extract_keywords(goal3)
# Output: ['factorial', 'function', 'recursion']
```

✅ Correctly extracts meaningful keywords  
✅ Removes stop words (a, the, that, of)  
✅ No duplicates

#### Test 2: Similarity Calculation

```python
sim_1_2 = calculate_similarity(keywords1, keywords2)
# factorial vs fibonacci: 14.29%

sim_1_3 = calculate_similarity(keywords1, keywords3)
# factorial vs factorial with recursion: 40.00%
```

✅ Different problems = low similarity (14%)  
✅ Same problem different phrasing = high similarity (40%)  
✅ Jaccard similarity working correctly

#### Test 3: Storage and Retrieval

```python
ltm = LongTermMemory()
print(ltm.count())  # 0

# Add a solution
solution = Solution(
    goal="write a factorial function",
    code="def factorial(n): ...",
    test_results={'total_tests': 3, 'passed': 3},
    timestamp="2026-02-24T14:00:00",
    keywords=[],
    iterations_to_solve=2
)
ltm.add(solution)
print(ltm.count())  # 1

# Retrieve similar
similar = ltm.find_similar("write a fibonacci function", top_k=1)
# Found: 'write a factorial function' (similarity: 33.33%)
```

✅ Solutions persist to disk  
✅ Retrieval finds similar problems  
✅ Similarity threshold filters irrelevant results

#### Test 4: Cross-Session Learning (Manual)

**Session 1:**

- Goal: “write a factorial function”
- Agent solves it in 2 iterations
- Solution saved to memory/solutions.json

**Session 2 (restart agent):**

- Goal: “write a fibonacci function”
- Agent loads long-term memory
- Finds factorial (33% similar)
- Uses recursive pattern from factorial
- Succeeds faster

✅ Memory persists across sessions  
✅ Agent learns from past patterns  
✅ Knowledge base grows over time

### Concepts Learned

**Jaccard similarity:**
Simple but effective similarity metric for sets. Used heavily in search engines and recommendation systems.

**Keyword extraction:**
NLP technique to identify important terms. We use simple word filtering instead of ML models (TF-IDF, word2vec).

**Why not embeddings?**
Vector embeddings (like sentence-transformers) would be more sophisticated, but:

- Require 100MB+ models
- Need PyTorch/TensorFlow (200MB+ dependencies)
- Slow initialization
- Overkill for simple code problems
- Harder to debug (black box)

Keywords work better for code because:

- Code problems are keyword-heavy (“sort”, “search”, “factorial”)
- Short texts (5-10 words)
- Exact matches matter more than semantic similarity
- Explainable and debuggable

**Persistent storage:**
JSON is perfect for small datasets (<1000 solutions). For larger scale, we’d use SQLite or a vector database.

**Trade-offs:**
We chose simplicity over sophistication. This system:

- ✅ Works immediately (no model download)
- ✅ Fast (keyword matching is instant)
- ✅ Understandable (you can read the JSON)
- ✅ Lightweight (no ML dependencies)
- ❌ Less accurate than embeddings for semantic similarity
- ❌ Won’t work well for very long texts

For our use case (code problems), the trade-off is worth it.

### Why This Matters

**Before Day 5:**
Every session is isolated. Agent starts from scratch every time. Solving 100 problems doesn’t make it better at problem 101.

**After Day 5:**
The agent builds a knowledge base. Each success makes future problems easier. After solving 10 recursive problems, it recognizes “this looks like recursion” immediately.

**Real-world analogy:**

- Days 1-4: Student with amnesia (forgets everything overnight)
- Day 5: Student with a notebook (writes down successful solutions, refers back to them)

**Practical impact:**

- Faster convergence on similar problems
- Fewer wasted iterations
- Pattern reuse across problem types
- Genuine learning over time

### Example Usage Flow

```
$ python3 main.py

Goal: write a function that reverses a string

💡 Found 0 similar past solution(s)

--- Iteration 1/5 ---
[Agent writes code and tests]
✅ All tests passed!

💾 Solution saved to long-term memory
Long-term memory: 1 solutions stored

---

$ python3 main.py

Goal: write a function that reverses a list

💡 Found 1 similar past solution(s)
  - 'write a function that reverses a string' (similarity: 50%)

[Prompt includes the string reversal solution as reference]

--- Iteration 1/5 ---
[Agent adapts the pattern]
✅ All tests passed!

💾 Solution saved to long-term memory  
Long-term memory: 2 solutions stored
```

The agent gets smarter with every problem solved.

### Commands Used

```bash
# Navigate and activate
cd ~/coding-agent
source venv/bin/activate

# Create long-term memory module
touch src/long_term_memory.py
open -e src/long_term_memory.py
# (Pasted implementation)

# Test module loading
python3 -c "from src.long_term_memory import LongTermMemory; print('Long-term memory loaded OK')"

# Update agent
open -e src/agent.py
# (Added import, updated build_user_prompt, updated run_agent)

# Test imports
python3 -c "from src.agent import build_user_prompt; print('build_user_prompt updated OK')"
python3 -c "from src.agent import run_agent; print('Agent with long-term memory loaded OK')"

# Test keyword extraction and similarity
python3 << 'EOF'
from src.long_term_memory import extract_keywords, calculate_similarity

goal1 = "write a factorial function"
goal2 = "write a fibonacci function"

keywords1 = extract_keywords(goal1)
keywords2 = extract_keywords(goal2)

print("Keywords 1:", keywords1)
print("Keywords 2:", keywords2)
print("Similarity:", calculate_similarity(keywords1, keywords2))
EOF

# Test full long-term memory system
python3 << 'EOF'
from src.long_term_memory import LongTermMemory, Solution

ltm = LongTermMemory()
print(f"Solutions: {ltm.count()}")

solution = Solution(
    goal="write a factorial function",
    code="def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)",
    test_results={'total_tests': 3, 'passed': 3, 'failed': 0, 'failures': []},
    timestamp="2026-02-24T14:00:00",
    keywords=[],
    iterations_to_solve=2
)
ltm.add(solution)

similar = ltm.find_similar("write a fibonacci function")
for sol, score in similar:
    print(f"Found: '{sol.goal}' (similarity: {score:.0%})")
EOF

# Update config
open -e src/config.py
# (Added LONG_TERM_MEMORY_PATH, SIMILARITY_THRESHOLD, MAX_SIMILAR_SOLUTIONS)

# Verify all components
python3 -c "
from src.agent import run_agent
from src.memory import ShortTermMemory
from src.long_term_memory import LongTermMemory
from src.config import LONG_TERM_MEMORY_PATH, SIMILARITY_THRESHOLD
print('✅ All Day 5 components loaded')
print(f'✅ Long-term memory path: {LONG_TERM_MEMORY_PATH}')
print(f'✅ Similarity threshold: {SIMILARITY_THRESHOLD}')
"

# Manual GitHub upload (git issues)
# Uploaded: src/long_term_memory.py, src/agent.py (modified), src/config.py (modified)
```

### Improvement Over Days 1-4

|Aspect          |Days 1-4              |Day 5                   |
|----------------|----------------------|------------------------|
|Memory duration |Session-only          |Permanent               |
|Learning        |Per-session           |Cross-session           |
|Pattern reuse   |None                  |Automatic               |
|Knowledge base  |Resets every time     |Grows over time         |
|Similar problems|Start from scratch    |Retrieve past solutions |
|Efficiency      |Same effort every time|Improves with experience|

**Key insight:** The agent now has a persistent identity. It’s not just a tool that executes tasks — it’s a system that learns and improves over time.

### Challenges Encountered

**Challenge 1: PyTorch installation failed**
Tried to install `sentence-transformers` for vector embeddings but hit network timeouts downloading PyTorch.

**Solution:** Pivoted to keyword-based similarity. Simpler, faster, and actually better for code problems.

**Lesson:** Don’t over-engineer. The simplest solution that works is often the best.

**Challenge 2: Deciding on similarity threshold**
Too low (10%) = retrieves irrelevant solutions  
Too high (60%) = rarely finds anything

**Solution:** Set default to 30%, configurable in config.py. This finds moderately similar problems without noise.

**Challenge 3: How much code to show in retrieval context**
Full code = too verbose, clutters prompt  
No code = not useful

**Solution:** Show first 300 characters with “…” to give flavor without overwhelming.

### Next Steps (Day 6)

- Circuit breaker pattern to prevent infinite loops
- Advanced safety layer (detect malicious patterns)
- Rate limiting on API calls
- Automatic rollback on critical failures
- Production hardening

-----

*Last updated: February 24, 2026*
