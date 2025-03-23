import click
from rich.console import Console

console = Console()         # Initializing the console for rich text

# Define the main command group
@click.group()
@click.version_option(version="0.1.0")
def cli():
    """TerminAI: Your AI-powered terminal assistant."""
    pass

# Defining the ask command 
@cli.command(name="ask")
@click.argument("query")
def ask(query):
    """Ask for a specific terminal command or workflow help."""
    from .commands.ask import handle_ask_command        # Lazy importing for faster startup and dependency separation
    handle_ask_command(query)

'''
Goals for the debug command -
terminai debug "error message" - Analyzes a specific error without context
terminai debug "error message" -c - Analyzes a specific error with context
terminai debug -a - Automatically analyzes recent terminal activity with context
'''

@cli.command(name="debug")
@click.argument("error_message", required=False) # Option argument
@click.option('--context', '-c', is_flag=True, help="Include your recent commands and outputs as context")
@click.option('--auto', '-a', is_flag=True,help="Automatically analyze recent terminal activity without specifying an error")
def debug(error_message, context, auto):
    """
    Get detailed explanations and fixes for terminal errors.
    
    Run without arguments to analyze recent terminal activity automatically.
    """
    from .commands.debug import handle_debug_command
    handle_debug_command(error_message, context or auto)

# Shortcut sub-command
@cli.command(name="-debug")
def auto_debug():
    """Automatically analyze recent terminal activity."""
    from .commands.debug import handle_debug_command
    handle_debug_command(None, True, auto_analyze=True)     # Calling handler with auto-analysis mode enabled and forced context inclusion.

# Defining the version command 
@cli.command()
def version():
    """Display the version of TerminAI."""
    console.print("[bold]TerminAI[/bold] version 0.1.0")

def main():
    """Main entry point for the CLI."""
    cli()

if __name__ == "__main__":
    main()