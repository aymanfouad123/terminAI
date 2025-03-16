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
    
    console.print(Panel(
        "[bold]TerminAI Initialization[/bold]\n\n"
        "This will configure your shell to automatically log your recent commands and outputs.\n"
        "- Commands and outputs are stored [bold]locally only[/bold] in your ~/.terminai directory\n"
        "- Only the last 5 commands and their outputs are kept\n"
        "- Logs are [bold]never[/bold] sent anywhere unless you explicitly run [bold]debug --context[/bold]\n"
        "- Command logging is optimized for minimal performance impact\n"
        "- To debug with context: [bold]terminai debug --context \"your error message\"[/bold]",
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
    Create a shell script that automatically logs recent commands and their outputs.
    Optimized for minimal performance impact while providing rich debugging context.
    
    Returns:
        Shell script content as a string
    """
    
    return """
    #!/bin/bash
    # TerminAI Command and Output Logger
    # Automatically logs last 5 commands and their outputs with minimal performance impact
    
    # Create log directory if it does't exist 
    mkdir -p ~/.terminai
    
    # Function to log commands with its output
    terminai_log_command_output() {
        # Get command and exit code
        local exit_code=$?
        local cmd="$(history 1 | sed 's/^[ ]*[0-9]*[ ]*//')"
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        
        # Don't log terminai commands to avoid noise 
        if [[ $cmd != terminai* ]]; then 
            # Create a unique ID for this command to link the command with the output
            local cmd_id=$(date +%s%N)
            # Write command with metadata 
            echo "${timestamp}|${exit_code}|${cmd_id}|${cmd}" >> ~/.terminai/commands.log
        
            # Rotate commands log to keep only last 5
            tail -n 5 ~/.terminai/commands.log > ~/.terminai/commands.log.tmp
            mv ~/.terminai/commands.log.tmp ~/.terminai/commands.log
        
            # Capture output from screen buffer if possible (non-blocking)
            # Different approach based on shell
            if [ -n "$BASH_VERSION" ]; then
                # For Bash: Try to get output from screen buffer or command
                if [ -n "$TERM_OUTPUT" ]; then
                    # Limit output size to prevent massive files, saving last 50 lines
                    echo "$TERM_OUTPUT" | tail -n 50 > ~/.terminai/output_${cmd_id}.log
                    # Reset terminal output for next command
                    unset TERM_OUTPUT
                fi
            elif [ -n "$ZSH_VERSION" ]; then
                # For Zsh: Similar approach
                if [ -n "$TERM_OUTPUT" ]; then
                    echo "$TERM_OUTPUT" | tail -n 50 > ~/.terminai/output_${cmd_id}.log
                    unset TERM_OUTPUT
                fi
            fi

            
            # Clean up old output files (keep only for the commands in commands.log)
            # This ensures we only store outputs for the most recent 5 commands
            for output_file in ~/.terminai/output_*.log; do
                if [ -f "$output_file" ]; then
                    file_id=$(basename "$output_file" | sed 's/output_\(.*\)\.log/\1/')
                    if ! grep -q "|$file_id|" ~/.terminai/commands.log; then
                        rm "$output_file"
                    fi
                fi
            done
        fi
    }
    
    # Function to capture output before showing the prompt
    terminai_capture_output() {
        # For non-terminai commands, try to capture output
        local cmd="$(history 1 | sed 's/^[ ]*[0-9]*[ ]*//')"
        if [[ $cmd != terminai* ]] && [[ -n "$cmd" ]]; then
            # Capture terminal output using screen tricks
            # This is a non-blocking approach that works in most terminals
            export TERM_OUTPUT=$(echo -e "\033[J\033[0;0H\033[6n" > /dev/tty; read -t 0.1 -s -d R pos; echo "$pos" | cut -d';' -f2-)
        fi
    }
    
    # Set up shell-specific hooks (optimized for performance)
    if [ -n "$BASH_VERSION" ]; then
        # For Bash
        # Store original PROMPT_COMMAND
        if [ -z "$ORIGINAL_PROMPT_COMMAND" ]; then
            ORIGINAL_PROMPT_COMMAND="$PROMPT_COMMAND"
        fi
        
        # Use PROMPT_COMMAND for both capturing and logging
        # This runs just before the prompt is displayed
        PROMPT_COMMAND='terminai_capture_output; terminai_log_command_output;'${ORIGINAL_PROMPT_COMMAND:+$ORIGINAL_PROMPT_COMMAND}
    elif [ -n "$ZSH_VERSION" ]; then
        # For Zsh
        # preexec runs before command execution
        preexec() {
            # Nothing needed here, we'll capture after command completes
        }
        
        # precmd runs after command completes, before prompt display
        precmd() {
            terminai_capture_output
            terminai_log_command_output
        }
    fi

    # Print initialization message only once per session
    if [ -z "$TERMINAI_INITIALIZED" ]; then
        export TERMINAI_INITIALIZED=1
        echo "TerminAI command logging initialized (automatically capturing last 5 commands)."
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
        
def get_recent_commands_with_outputs(limit: int = 5) -> Dict[str, Any]:
    """
    Get recent commands and their outputs from the automatic logging system.
    Optimized for fast retrieval of exactly what's needed.
    
    Args:
        limit: Maximum number of commands to retrieve (default: 5)
        
    Returns:
        Dict with recent commands and their outputs
    """
    result = {
        "commands": [],
        "has_outputs": False
    }
    
    try:
        # Get commands from the commands log
        cmd_log_path = Path.home() / ".terminai" / "commands.log"
        if cmd_log_path.exists():
            with open(cmd_log_path, 'r') as f:
                lines = f.readlines()
            
            # Parse the command entries. Format: timestamp|exit_code|cmd_id|command
            commands = []
            for line in lines:
                line = line.strip()
                if line: 
                    parts = line.split('|', 3)
                    if len(parts) >= 4:
                        timestamp, exit_code, cmd_id, command = parts
                        commands.append({
                            "timestamp": timestamp,
                            "exit_code": int(exit_code),
                            "cmd_id": cmd_id,
                            "command": command
                        })
            
            # Process commands (most recent first)
            for cmd in reversed(commands[:limit]):
                cmd_entry = {
                    "timestamp": cmd["timestamp"],
                    "command": cmd["command"],
                    "exit_code": cmd["exit_code"]
                }
                
                # Look for corresponding output file 
                output_file = Path.home() / ".terminai" / f"output_{cmd['cmd_id']}.log"
                if output_file.exists():
                    try:
                        with open(output_file, 'r') as f:
                            output_text = f.read()
                        
                        if output_text.strip():
                            cmd_entry["output"] = output_text.strip()
                            result["has_outputs"] = True
                    except Exception as e:
                        # If we can't read the output, just continue without it
                        pass
                
                result["commands"].append(cmd_entry)
        return result
    
    except Exception as e:
        console.print(f"[yellow]Error reading command history: {str(e)}[/yellow]")
        return result
                        