import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-4-5-20250929"

# Agent Configuration
MAX_ITERATIONS = 5
MAX_TOKENS = 4096

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
MEMORY_DIR = os.path.join(BASE_DIR, "memory")

# Ensure directories exist
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(MEMORY_DIR, exist_ok=True)

# Sandbox Configuration
CPU_TIME_LIMIT = 5  # seconds of actual CPU time
MEMORY_LIMIT_MB = 256  # megabytes
FILE_SIZE_LIMIT_MB = 10  # megabytes per file
EXECUTION_TIMEOUT = 10  # wall-clock seconds

# Memory Configuration
SHORT_TERM_MEMORY_SIZE = 5  # Number of attempts to keep in memory

# Long-Term Memory Configuration
LONG_TERM_MEMORY_PATH = "memory/solutions.json"
SIMILARITY_THRESHOLD = 0.3  # Minimum 30% similarity to retrieve
MAX_SIMILAR_SOLUTIONS = 2  # Show top 2 similar solutions
