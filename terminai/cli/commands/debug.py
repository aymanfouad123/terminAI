"""
Implementation of the 'debug' command for TerminAI.
This handles debugging terminal errors using AI assistance.
"""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ..core.ai import generate_ai_response
from ..core.context import get_terminal_context

console = Console()

def handle_debug_command(error_message: str) -> None:
    """
    Handle the 'debug' command by analyzing an error message and suggesting fixes.
    
    Args:
        error_message: The error message to analyze
    """
    console.print(f"[bold yellow]Analyzing error:[/bold yellow] {error_message}")
    
    try: 
        # Get terminal context
        context = get_terminal_context()
        
        # Debugging prompt 
        debug_prompt = f"""
        I received this error in my terminal: "{error_message}"
        Act like a senior engineer who has good technical knowledge of codebases and can point out why an error is occuring.
        Please explain:
        1. What this error means
        2. The most likely cause
        3. How to fix it
        4. How to prevent it in the future
        
        Format your response as markdown with clear sections.
        """
        
        # Generating response 
        console.print("[yello]Analysing...[/yellow]")
        response = generate_ai_response(debug_prompt, context, command_type="debug")
        
        # Displaying the formatted response 
        console.print("\n[bold cyan]Error Analysis:[/bold cyan]")
        console.print(Panel(Markdown(response), title="TerminAI Debug Results", border_style="cyan"))
        
    except Exception as e:
        console.print(f"[bold red]Error analyzing error message:[/bold red] {str(e)}")