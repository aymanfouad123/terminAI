import click
from rich.console import Console

console = Console() # Initializing the console for rich text

# Define the main command group
@click.group()
@click.version_option(version="0.1.0")
def cli():
    """TerminAI: Your AI-powered terminal assistant."""
    pass

@cli.command()
@click.argument("query")
def ask(query):
    """Ask for a specific terminal command or workflow help."""
    console.print(f"[bold green]You asked:[/bold green] {query}")
    console.print(f"[yellow]This command will eventually use AI to answer your query.[/yellow]")

@cli.command()
def version():
    """Display the version of TerminAI."""
    console.print("[bold]TerminAI[/bold] version 0.1.0")

def main():
    """Main entry point for the CLI."""
    cli()

if __name__ == "__main__":
    main()