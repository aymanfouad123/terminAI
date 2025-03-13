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
     