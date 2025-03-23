"""
Context module for TerminAI.
This gathers information about the terminal environment to provide context for AI queries.
"""

import os
import platform     # For getting system information
import subprocess   # For running terminal commands to gather information
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def get_os_info() -> str:
    """Get the operating system information"""
    return f"{platform.system()} {platform.release()}"

def get_shell() -> str:
    """Get the current shell"""
    return os.environ.get("SHELL", "Unknown")   # Checking environment variable, else fallback to "Unknown"

def get_current_directory() -> str:
    """Get the current working directory"""
    return os.getcwd()

# Main context function
def get_terminal_context() -> Dict[str, Any]:
    """
    Get basic information about the terminal environment.
    
    Returns:
        Dictionary with OS, shell, and current directory information
    """
    try:
        context = {
            "os" : get_os_info(),
            "shell" : get_shell(),
            "current_dir" : get_current_directory(),
            "username" : os.environ.get("USER", "Unknown")
        }
        return context
    
    except Exception as e:
        logger.error(f"Error getting terminal context: {e}")
        return { "error" : f"Failed to get context information: {str(e)}"}

def get_recent_commands_with_outputs() -> Dict[str, Any]:
    """
    Get recent commands and their outputs from the TerminAI logs.
    
    Returns:
        Dictionary with commands list and has_outputs flag
    """    
    commands = []
    has_outputs = False
    
    # Path to command log
    log_path = os.path.expanduser("~/.terminai/commands.log")
    
    # Check if log file exists
    if not os.path.exists(log_path):
        return {"commands": commands, "has_outputs": has_outputs}
    
    try:
        # Read the command log file
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        # Process each line (format: timestamp|exit_code|cmd_id|command)
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            parts = line.split('|', 3)  # Split into 4 parts
            if len(parts) < 4:
                continue
        
        timestamp, exit_code_str, cmd_id, command = parts
        
        # Create command entry
        cmd_entry = {
            "command": command,
            "timestamp": timestamp
        }
        
        # Add exit code if available
        try:
            cmd_entry["exit_code"] = int(exit_code_str)
        except ValueError:
            pass
            
        # Check for output file
        output_path = os.path.expanduser(f"~/.terminai/output_{cmd_id}.log")
        if os.path.exists(output_path):
            try:
                with open(output_path, 'r') as f:
                    output = f.read()
                cmd_entry["output"] = output
                has_outputs = True
            except:
                pass
        
        commands.append(cmd_entry)
    except Exception as e:
        # Handle any errors by returning an empty result
        return {"commands": [], "has_outputs": False, "error": str(e)}
    
    return {"commands": commands, "has_outputs": has_outputs}
        