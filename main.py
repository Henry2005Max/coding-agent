import sys
from rich.console import Console
from rich.panel import Panel
from src.agent import run_agent

console = Console()

def main():
    console.print(Panel(
        "[bold cyan]Self-Improving Coding Agent[/bold cyan]\n"
        "[dim]Powered by Claude | Day 1 Build[/dim]",
        title="Welcome"
    ))

    if len(sys.argv) > 1:
        # Goal passed directly as command line argument
        goal = " ".join(sys.argv[1:])
    else:
        # Interactive mode
        console.print("\n[bold]What do you want the agent to build?[/bold]")
        console.print("[dim]Example: write a function that returns the fibonacci sequence up to n terms[/dim]\n")
        goal = input("Your goal: ").strip()

        if not goal:
            console.print("[red]No goal provided. Exiting.[/red]")
            sys.exit(1)

    success = run_agent(goal)

    if success:
        console.print("\n[bold green]Agent completed successfully.[/bold green]")
    else:
        console.print("\n[bold red]Agent could not complete the goal.[/bold red]")
        console.print("[dim]Check the logs/ folder to see what was attempted.[/dim]")

if __name__ == "__main__":
    main()
