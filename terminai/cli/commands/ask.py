"""
Implementation of the 'ask' command for TerminAI.
This handler is responsible for processing user's query, gathering relevant terminal context, generating ai response and displaying the result to the user.
"""

import click    # For cli functionality
from rich.console import Console
from rich.prompt import Confirm
import subprocess

# Relative imports
from ..core.ai import generate_ai_response
from ..core.context import get_terminal_context

console = Console()

def handle_ask_command(query: str) -> None:
    """Handle the 'ask' command"""
    console.print(f"[bold green]Processing query:[/bold green] {query}")
    
    try:
        # Get terminal context
        context = get_terminal_context()
        
        # Generate AI response
        console.print("[yellow]Thinking...[/yellow]")
        response = generate_ai_response(query, context)
        
        # Display the response 
        console.print("\n[bold cyan]Suggested command:[/bold cyan]")
        console.print(f"[green]{response}[/green]")
        
        # Auto run command prompt
        if Confirm.ask("Run this command?"):
            console.print("[yellow]Executing command...[/yellow]")
            
            # Execute the command
            process = subprocess.run(
                response,
                # TODO: Add additional safeguards for untrusted input passed to shell
                shell = True,               # Command is executed through the shell 
                capture_output = True,      # Captures stdout and stderr
                text = True                 # Ensures output is decoded as text
            )
            
            # Display the command output
            if process.stdout:
                console.print("[bold]Output:[/bold]")
            console.print(process.stdout)
        
            if process.stderr:
                console.print("[bold red]Error:[/bold red]")
                console.print(process.stderr)
            
            console.print(f"[bold green]Command executed with return code: {process.returncode}[/bold green]")
        else: 
            console.print("[yellow]Command not executed[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        