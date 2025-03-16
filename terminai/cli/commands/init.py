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
        "- Commands are stored [bold]locally only[/bold] in ~/.terminai/history.log\n"
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
            "You can now use [bold]terminai debug --context[/bold] for enhanced debugging.",
            title="Setup Complete",
            border_style="green"
        ))
    else:
        console.print("[bold red]Initialization failed.[/bold red]")

def get_shell_config_files() -> List[Path]:
    """
    Find which shell configuration files exist on the system.
    
    Returns:
        List of paths to shell configuration files
    """
    configs  = []
    
    # Check for bash configuration
    bashrc = Path.home() / ".bashrc"
    bash_profile = Path.home() / ".bash_profile"        # Alternative bash configurations on some systems
    
    if bashrc.exists():
        configs.append(bashrc)
    if bash_profile.exists():
        configs.append(bash_profile)
    
    # Check for zsh configurations
    zshrc = Path.home() / ".zshrc"
    if zshrc.exists():
        configs.append(zshrc)
    
    return configs

# Helper function
def add_logging_to_shell_configs(config_files: List[Path]) -> bool:
    """
    Add command logging to shell configuration files.
    
    Args:
        config_files: List of shell configuration files to modify
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create the logging script content
        logging_script = create_logging_script()
        
        # Writing the logging script to the .terminai directory
        logging_script_path = Path.home() / ".terminai" / "logger.sh"
        with open(logging_script_path, 'w') as f:
            f.write(logging_script)
            
        # Make it executable
        os.chmod(logging_script_path, 0o755) # Modifying file permissions. 0o755 is octal for read+write+execute for owner, read+execute for others
        
        # Add source commands to each config file
        for config_file in config_files:
            add_source_command(config_file, logging_script_path)
        
        return True
    except Exception as e:
        console.print(f"[bold red]Error setting up logging:[/bold red] {str(e)}")
        return False
    
def create_logging_script() -> str:
    """
    Create the shell script that will handle command logging.

    Returns:
        Shell script content as a string 
    """
    return """
    #!/bin/bash
    # TerminAI Command Logger
    # This script logs shell commands and their outputs to a file for the TerminAI debug command
    
    # Create log directory if it does't exist 
    mkdir -p ~/.terminai
    
    # Function to log commands
    terminai_log_command() {
        # Don't log the 'terminai' command itself to avoid noise
        if [[ $1 != terminai* ]]; then 
            # Add timestamp, log to file, and rotate if needed
            echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> ~/.terminai/history.log
        
            # Keep only the last 100 entries
            if [ -f ~/.terminai/history.log ]; then
                tail -n 100 ~/.terminai/history.log > ~/.terminai/history.log.tmp
                mv ~/.terminai/history.log.tmp ~/.terminai/history.log
            fi
        fi
    }
    
    # Set up command logging based on shell
    if [ -n "$BASH_VERSION" ]; then
        # For Bash
        if [ -z "$PROMPT_COMMAND" ]; then
            PROMPT_COMMAND='termiai_log_command "$(history 1 | sed "s/^[ ]*[0-9]*[ ]*//")"'
        else
            PROMPT_COMMAND='termiai_log_command "$(history 1 | sed "s/^[ ]*[0-9]*[ ]*//")"'"
            ${PROMPT_COMMAND}"
        fi
    elif [ -n "$ZSH_VERSION" ]; then
        # For Zsh
        preexec() {
            termiai_log_command "$1"
        }
    fi

    # Print initialization message only once per session
    if [ -z "$TERMIAI_INITIALIZED" ]; then
        TERMIAI_INITIALIZED=1
        echo "TerminAI command logging initialized."
    fi 
    """

def add_source_command(config_file: Path, script_path: Path) -> None:
    """
    Add a source command to a shell configuration file.
    
    Args:
        config_file: Path to the shell configuration file
        script_path: Path to the logging script
    """
    source_command = f"\n# Added by TerminAI\n[ -f {script_path} ] && source {script_path}\n"
    
    # Check if the source command is already in the file
    with open(config_file, 'r') as f:
        content = f.read()
    
    if str(script_path) not in content:
        # Append the source command to the file
        with open(config_file, 'a') as f:
            f.write(source_command)
        console.print(f"[green]Added logging to {config_file}[/green]")
    else:
        console.print(f"[yellow]Logging already configured in {config_file}[/yellow]")
        