"""
Implementation of the 'debug' command for TerminAI.
This handles debugging terminal errors using AI assistance.
"""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from terminai.cli.commands.init import get_recent_commands_with_outputs

from ..core.ai import generate_ai_response
from ..core.context import get_terminal_context

console = Console()

def handle_debug_command(error_message: str, include_context: bool = False) -> None:
    """
    Handle the 'debug' command by analyzing an error message with optional command context.
    
    Args:
        error_message: The error message to analyze
        include_context: Whether to include recent command history as context
    """
    
    # Error message is required
    if not error_message:
        console.print("[bold yellow]Please provide an error message to analyze.[/bold yellow]")
        console.print("Example: [bold]terminai debug \"permission denied\"[/bold]")
        console.print("Add [bold]--context[/bold] to include your recent commands and their outputs.")
        return
        
    console.print(f"[bold yellow]Analyzing error:[/bold yellow] {error_message}")
    
    try: 
        # Get terminal context
        context = get_terminal_context()
        
        # Add command history with outputs if requested
        if include_context:
            history_data = get_recent_commands_with_outputs()
            
            if history_data["commands"]:
                context["recent_commands"] = history_data["commands"]
                console.print(f"[dim]Including context from your last {len(history_data['commands'])} commands...[/dim]")
                
                if history_data.get("has_outputs"):
                    console.print("[dim]Including command outputs in analysis...[/dim]")
                else:
                    console.print("[dim]No command outputs available in recent history.[/dim]")
            else:
                console.print("[yellow]No command history found. Is command logging initialized?[/yellow]")
                console.print("[yellow]Run 'terminai init' to set up command logging.[/yellow]")
        
        # Build prompt with available context
        debug_prompt = build_debug_prompt(error_message, context)
        
        # Generate response using AI
        console.print("[yellow]Analyzing...[/yellow]")
        response = generate_ai_response(debug_prompt, context, command_type="debug")
        
        # Display the formatted response
        console.print("\n[bold cyan]Error Analysis:[/bold cyan]")
        console.print(Panel(Markdown(response), title="TerminAI Debug Results", border_style="cyan"))
        
    except Exception as e:
        # Escape any Rich markup characters in the error message
        error_msg = escape(str(e))
        console.print(f"[bold red]Error analyzing error message:[/bold red] {error_msg}")
        
def build_debug_prompt(error_message: str, context: Dict[str, Any]) -> str:
    """
    Build a detailed prompt for debugging based on available context.
    
    Args:
        error_message: The error message to analyze
        context: Terminal context including command history if available
        
    Returns:
        Prompt string for the AI
    """
    # Core prompt
    prompt = f"""
    I received this error in my terminal: "{error_message}"
    
    Please explain:
    1. What this error means
    2. The most likely cause
    3. How to fix it
    4. How to prevent it in the future
    
    Format your response as markdown with clear sections.
    """
    
    # Add system context
    if context.get("os") or context.get("shell"):
        prompt += "\n\nSystem information:"
        if context.get("os"):
            prompt += f"\n- Operating System: {context['os']}"
        if context.get("shell"):
            prompt += f"\n- Shell: {context['shell']}"
        if context.get("current_dir"):
            prompt += f"\n- Current Directory: {context['current_dir']}"
    
    # Add command history if available
    if "recent_commands" in context and context["recent_commands"]:
        prompt += "\n\nRecent commands and their outputs:\n"
        
        for i, cmd in enumerate(context["recent_commands"]):
            # Format the command line with additional info
            cmd_line = f"{i+1}. [{cmd.get('timestamp', 'Unknown time')}] `{cmd['command']}`"
            
            # Add exit code indicator
            if "exit_code" in cmd:
                status = "✓" if cmd["exit_code"] == 0 else f"✗ (exit code: {cmd['exit_code']})"
                cmd_line += f" {status}"
                
            prompt += f"{cmd_line}\n"
            
            # Add output if available
            if "output" in cmd:
                prompt += f"   Output:\n   ```\n   {cmd['output']}\n   ```\n"
        
        prompt += "\nPlease analyze the error in the context of these recent commands and their outputs."
    
    return prompt