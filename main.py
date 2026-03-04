
"""
Coding Agent - A self-improving AI coding assistant
Writes code, runs tests, learns from failures, and improves over time.
"""

import sys
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from src.agent import run_agent
from src.memory import ShortTermMemory
from src.long_term_memory import LongTermMemory
from src.safety import CircuitBreaker
from src.config import (
    MAX_ITERATIONS, 
    SHORT_TERM_MEMORY_SIZE,
    MAX_CONSECUTIVE_FAILURES,
    MAX_API_REQUESTS
)

console = Console()


def show_banner():
    """Display startup banner"""
    banner = """
    ╔═══════════════════════════════════════════════╗
    ║                                               ║
    ║       🤖  SELF-IMPROVING CODING AGENT  🤖      ║
    ║                                               ║
    ║   Writes code • Runs tests • Learns • Fixes   ║
    ║                                               ║
    ╚═══════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def show_stats():
    """Show current system statistics"""
    ltm = LongTermMemory()
    stats = ltm.get_stats()
    
    console.print("\n[bold cyan]📊 System Statistics:[/bold cyan]")
    console.print(f"  • Solutions in long-term memory: {stats.get('total_solutions', 0)}")
    console.print(f"  • Max iterations per goal: {MAX_ITERATIONS}")
    console.print(f"  • Short-term memory size: {SHORT_TERM_MEMORY_SIZE} attempts")
    console.print(f"  • Circuit breaker threshold: {MAX_CONSECUTIVE_FAILURES} failures")
    console.print(f"  • Rate limit: {MAX_API_REQUESTS} requests/minute")
    console.print()


def run_demo():
    """Run a demo with a pre-built example"""
    console.print("\n[bold green]🎬 Running Demo Mode[/bold green]\n")
    
    demo_goals = [
        "write a function that calculates factorial of a number with tests",
        "write a function that checks if a number is prime with tests",
        "write a function that reverses a string with tests"
    ]
    
    console.print("Available demo goals:")
    for i, goal in enumerate(demo_goals, 1):
        console.print(f"  {i}. {goal}")
    
    choice = console.input("\n[bold]Choose a demo (1-3) or press Enter for #1:[/bold] ").strip()
    
    if choice == "":
        choice = "1"
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(demo_goals):
            goal = demo_goals[idx]
            console.print(f"\n[dim]Selected: {goal}[/dim]\n")
            run_agent(goal)
        else:
            console.print("[red]Invalid choice. Using demo #1[/red]")
            run_agent(demo_goals[0])
    except ValueError:
        console.print("[red]Invalid input. Using demo #1[/red]")
        run_agent(demo_goals[0])


def clear_memory():
    """Clear long-term memory"""
    ltm = LongTermMemory()
    count = ltm.count()
    
    if count == 0:
        console.print("\n[yellow]No solutions in memory to clear.[/yellow]")
        return
    
    confirm = console.input(f"\n[bold red]Clear {count} solution(s) from memory? (yes/no):[/bold red] ").strip().lower()
    
    if confirm == "yes":
        ltm.clear()
        console.print("\n[green]✅ Memory cleared successfully.[/green]")
    else:
        console.print("\n[dim]Cancelled.[/dim]")


def show_examples():
    """Show example usage"""
    examples = """
# Example Goals

## Basic Functions
- write a function that calculates factorial with tests
- write a function that checks if a number is prime with tests
- write a function that reverses a string with tests

## Data Structures
- write a function that implements a stack with push, pop, and peek with tests
- write a function that finds the second largest number in a list with tests

## Algorithms
- write a function that implements binary search with tests
- write a function that sorts a list using bubble sort with tests

## String Manipulation
- write a function that checks if a string is a palindrome with tests
- write a function that counts vowels in a string with tests

## Tips
- Always ask for tests (the agent writes better code with test requirements)
- Be specific about edge cases you want handled
- If agent gets stuck, try rephrasing the goal
    """
    console.print(Markdown(examples))


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Self-Improving Coding Agent - Writes, tests, and learns from code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py "write a factorial function with tests"
  python3 main.py --demo
  python3 main.py --stats
  python3 main.py --examples
  python3 main.py --clear-memory

For more information: https://github.com/yourusername/coding-agent
        """
    )
    
    parser.add_argument(
        'goal',
        nargs='?',
        help='The coding goal for the agent to achieve'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run in demo mode with pre-built examples'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show system statistics and exit'
    )
    
    parser.add_argument(
        '--examples',
        action='store_true',
        help='Show example goals and exit'
    )
    
    parser.add_argument(
        '--clear-memory',
        action='store_true',
        help='Clear long-term memory'
    )
    
    parser.add_argument(
        '--no-banner',
        action='store_true',
        help='Skip startup banner'
    )
    
    args = parser.parse_args()
    
    # Show banner unless suppressed
    if not args.no_banner and not (args.stats or args.examples):
        show_banner()
    
    # Handle commands
    if args.stats:
        show_stats()
        return
    
    if args.examples:
        show_examples()
        return
    
    if args.clear_memory:
        clear_memory()
        return
    
    if args.demo:
        run_demo()
        return
    
    # Interactive or direct mode
    if args.goal:
        # Direct mode - goal provided as argument
        run_agent(args.goal)
    else:
        # Interactive mode - prompt for goal
        console.print("[bold]Enter your coding goal:[/bold]")
        console.print("[dim](Example: write a function that calculates factorial with tests)[/dim]\n")
        
        goal = console.input("[bold green]Goal:[/bold green] ").strip()
        
        if not goal:
            console.print("\n[red]No goal provided. Exiting.[/red]")
            console.print("[dim]Tip: Run 'python3 main.py --examples' to see example goals[/dim]")
            return
        
        console.print()  # Blank line for spacing
        run_agent(goal)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  Interrupted by user. Exiting...[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]❌ Fatal Error:[/bold red] {str(e)}")
        console.print("[dim]Please report this issue on GitHub[/dim]")
        sys.exit(1)
