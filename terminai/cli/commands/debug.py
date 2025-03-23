"""
Implementation of the 'debug' command for TerminAI.
This handles debugging terminal errors using AI assistance.
"""
from typing import Dict, Any, List, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from terminai.cli.commands.init import get_recent_commands_with_outputs

from ..core.ai import generate_ai_response
from ..core.context import get_terminal_context

console = Console()

def handle_debug_command(error_message: Optional[str] = None, include_context: bool = False, auto_analyse: bool = False) -> None:
    """
    Handle the 'debug' command by analyzing terminal errors or activity.
    
    Args:
        error_message: The error message to analyze (optional if auto_analyze is True)
        include_context: Whether to include recent command history as context
        auto_analyze: Whether to automatically analyze recent terminal activity
    """
    
    # Get command history if context is requested
    history_data = get_recent_commands_with_outputs() if include_context else {"commands": [], "has_outputs": False}
    
    # For auto-analyze mode, we need to infer the problem from recent activity
    if auto_analyse:
        if not history_data["commands"]:
            console.print("[bold yellow]No recent command history found.[/bold yellow]")
            console.print("Run [bold]terminai init[/bold] to set up command logging first.")
            return

        console.print("[bold cyan]Analyzing your recent terminal activity...[/bold cyan]")
        
        # Find the most recent failed command
        error_detected = False
        for cmd in history_data["commands"]:
            if cmd.get("exit_code", 0) != 0:
                if not error_message:
                    error_message = f"Command failed: {cmd['command']}"
                error_detected = True
                break
        
        # If no errors found, just analyse recent activity
        if not error_detected:
            error_message = "Explain what these recent commands are doing and if there are any potential issues or improvements."
        
    # Error message is required if not auto-analysing 
    if not error_message and not auto_analyse:
        console.print("[bold yellow]Please provide an error message to analyze.[/bold yellow]")
        console.print("Example: [bold]terminai debug \"permission denied\"[/bold]")
        console.print("Or use [bold]terminai debug -a[/bold] to automatically analyze recent activity.")
        return
    
    if error_message:
        console.print(f"[bold yellow]Analyzing error:[/bold yellow] {error_message}")
    
    try: 
        # Get terminal context
        context = get_terminal_context()
        
        # Add command history 
        if include_context and history_data["commands"]:
            context["recent_commands"] = history_data["commands"]
            console.print(f"[dim]Including context from your last {len(history_data['commands'])} commands...[/dim]")
            if history_data.get("has_outputs"):
                console.print("[dim]Including command outputs in analysis...[/dim]")
        
        
        # Build prompt with available context
        debug_prompt = build_debug_prompt(error_message, context, auto_analyse)
        
        # Generate response using AI
        console.print("[yellow]Analyzing...[/yellow]")
        response = generate_ai_response(debug_prompt, context, command_type="debug")
        
        # Display the formatted response
        console.print("\n[bold cyan]Terminal Analysis:[/bold cyan]")
        console.print(Panel(Markdown(response), title="TerminAI Debug Results", border_style="cyan"))
        
    except Exception as e:
        console.print(f"[bold red]Error during analysis:[/bold red] {str(e)}")
        
def build_debug_prompt(error_message: str, context: Dict[str, Any], auto_mode: bool = False) -> str:
    """
    Build a detailed prompt for debugging based on available context.
    
    Args:
        error_message: The error message to analyze
        context: Terminal context including command history if available
        auto_mode: Whether this is an automatic analysis
        
    Returns:
        Prompt string for the AI
    """
    # Core prompt - adjust based on mode
    if auto_mode:
        prompt = """
        I need you to analyze my recent terminal activity.
        
        Please:
        1. Explain what these commands are doing
        2. Identify any errors or inefficiencies
        3. Suggest improvements or best practices
        4. Provide educational context about the commands
        
        Format your response as markdown with clear sections.
        """
    else:
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
            
            # Add exit code indicator using words instead of symbols
            if "exit_code" in cmd:
                if cmd["exit_code"] == 0:
                    status = "[SUCCESS]"
                else:
                    status = f"[FAILED] (exit code: {cmd['exit_code']})"
                cmd_line += f" {status}"
                
            prompt += f"{cmd_line}\n"
            
            # Add output if available
            if "output" in cmd and cmd["output"]:
                # Limit output to prevent token overflow
                output = cmd["output"]
                if len(output) > 500:
                    output = output[:500] + "... (truncated)"
                prompt += f"   Output:\n   ```\n   {output}\n   ```\n"
        
        if auto_mode:
            prompt += "\nPlease analyze these recent commands and their outputs, explaining what they're doing and identifying any issues."
        else:
            prompt += "\nPlease analyze the error in the context of these recent commands and their outputs."
    
    return prompt