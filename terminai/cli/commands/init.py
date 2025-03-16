"""
Implementation of the 'init' command for TerminAI.
This handles the setup of command history logging for better debugging context.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

def handle_init_command(force: bool = False) -> None:
    """
    Initialize TerminAI command history logging.
    
    Args:
        force: If True, will overwrite existing configuration
    """
    
    # Install prompt
    console.print(Panel(
        "[bold]TerminAI Initialization[/bold]\n\n"
        "This will configure your shell to log recent commands for improved debugging.\n"
        "- Commands are stored [bold]locally only[/bold] in ~/.termiai/history.log\n"
        "- Logs are [bold]never[/bold] sent anywhere unless you explicitly run [bold]debug --context[/bold]\n"
        "- Only the last 100 commands are kept\n"
        "- No command output is logged, only the commands themselves",
        title="TerminAI Setup",
        border_style="cyan"
    ))
    
    # Checking for existing installation
    terminai_dir = Path.home() / ".terminai"
    if terminai_dir.exists() and not force:
        console.print("[yellow]TerminAI appears to be already initialized.[/yellow]")
        
        if not Confirm.ask("Do you want to re-initialize?"):
            console.print("[cyan]Initialization cancelled.[/cyan]")
            return      # Exits function early if user declines
        
    # Create .terminai directory if it doesn't exist 
    terminai_dir.mkdir(exist_ok=True)       # Param. prevents errors if the directory already exists (handling edge case)
    
    # Get shell configuration files
    shell_configs = get_shell_config_files()
    if not shell_configs:
        console.print("[bold red]No supported shell configuration files found.[/bold red]")
        console.print("TerminAI supports Bash and Zsh. Please set up manually.")
        return
    
    # Confirm with user before modifying files
    if not force:
        config_list = "\n".join([f"- {config}" for config in shell_configs])
        console.print(f"[yellow]This will modify the following files:[/yellow]\n{config_list}")
    
        if not Confirm.ask("Do you want to continue?"):
            console.print("[cyan]Initialization cancelled.[/cyan]")
            return
    
    # Add logging commands to shell configuration files
    success = add_logging_to_shell_configs(shell_configs)
    if success:
        console.print(Panel(
            "[green]TerminAI has been successfully initialized![/green]\n\n"
            "To activate command history logging, please:\n"
            "1. Restart your terminal OR\n"
            "2. Run [bold]source ~/.bashrc[/bold] (or [bold]source ~/.zshrc[/bold])\n\n"
            "You can now use [bold]termiai debug --context[/bold] for enhanced debugging.",
            title="Setup Complete",
            border_style="green"
        ))
    else:
        console.print("[bold red]Initialization failed.[/bold red]")