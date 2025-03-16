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
@cli.command()
@click.argument("query")
def ask(query):
    """Ask for a specific terminal command or workflow help."""
    from .commands.ask import handle_ask_command        # Lazy importing for faster startup and dependency separation
    handle_ask_command(query)
    
@cli.command()
@click.argument("error_message", required=True)
@click.option('--context', '-c', is_flag=True, help="Include your recent commands and outputs as context")
def debug(error_message, context):
    """
    Get detailed explanations and fixes for terminal-specific errors.
    
    Add --context to analyze the error in the context of your recent commands and outputs.
    """
    from .commands.debug import handle_debug_command
    handle_debug_command(error_message, context)

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