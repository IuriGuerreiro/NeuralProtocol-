"""
Custom Tools - Additional tools for the NeuralProtocol MCP Client

This module contains custom tools that extend the functionality
beyond what MCP servers provide.
"""

import os
import subprocess
import logging
from typing import List, Any, Optional
from pathlib import Path

from langchain.tools import tool


# Default workspace - use current directory or NeuralProtocol folder
default_workspace = os.getcwd()


@tool()
def run_command(command: str) -> str:
    """
    Execute commands in Windows Command Prompt with automatic PowerShell fallback.
    
    Args:
        command: The command to execute (works with both CMD and PowerShell syntax)
    
    Returns:
        The output of the command execution, with information about which shell was used
        
    Security note: Commands run with the same permissions as the current user.
    Be careful with commands that can modify system files or settings.
    """
    try:
        # First attempt: Try running in CMD
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=default_workspace  # Use NeuralProtocol workspace
        )
        
        if result.returncode == 0:
            return f"✅ Command executed successfully in CMD:\n{result.stdout}"
        else:
            # Check if it's a "not recognized" error (CMD failure)
            error_output = result.stderr.strip()
            if any(phrase in error_output.lower() for phrase in [
                "not recognized", "not recognized as an internal or external command",
                "is not recognized", "command not found"
            ]):
                # Try PowerShell fallback
                logging.info(f"🔄 CMD command failed, trying PowerShell: {command}")
                powershell_command = f'powershell -Command "{command}"'
                
                ps_result = subprocess.run(
                    powershell_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=default_workspace
                )
                
                if ps_result.returncode == 0:
                    return f"✅ Command executed successfully in PowerShell (CMD fallback):\n{ps_result.stdout}"
                else:
                    return f"❌ Both CMD and PowerShell failed.\nCMD error: {error_output}\nPowerShell error: {ps_result.stderr}"
            else:
                # Other type of error, return CMD error
                return f"❌ Command failed in CMD: {error_output}"
            
    except Exception as e:
        return f"❌ Error running command: {e}"


@tool()
def list_files(directory: str = ".", pattern: str = "*", include_hidden: bool = False) -> str:
    """
    List files and directories in a specified path with optional filtering.
    
    Args:
        directory: Directory path to list (default: current directory)
        pattern: File pattern to match (default: "*" for all files)
        include_hidden: Whether to include hidden files (default: False)
    
    Returns:
        Formatted string listing the contents of the directory
    """
    try:
        path = Path(directory).resolve()
        
        if not path.exists():
            return f"❌ Directory does not exist: {directory}"
        
        if not path.is_dir():
            return f"❌ Path is not a directory: {directory}"
        
        # Get all items matching pattern
        if pattern == "*":
            items = list(path.iterdir())
        else:
            items = list(path.glob(pattern))
        
        # Filter hidden files if requested
        if not include_hidden:
            items = [item for item in items if not item.name.startswith('.')]
        
        # Sort items: directories first, then files
        directories = sorted([item for item in items if item.is_dir()])
        files = sorted([item for item in items if item.is_file()])
        
        result = [f"📁 Contents of {path}:\n"]
        
        if directories:
            result.append("📂 Directories:")
            for dir_item in directories:
                result.append(f"  📁 {dir_item.name}/")
        
        if files:
            if directories:
                result.append("")
            result.append("📄 Files:")
            for file_item in files:
                try:
                    size = file_item.stat().st_size
                    size_str = f"({size:,} bytes)" if size < 1024 else f"({size/1024:.1f} KB)"
                    result.append(f"  📄 {file_item.name} {size_str}")
                except OSError:
                    result.append(f"  📄 {file_item.name} (size unknown)")
        
        if not directories and not files:
            result.append("📭 Directory is empty")
        
        result.append(f"\n📊 Total: {len(directories)} directories, {len(files)} files")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"❌ Error listing directory: {e}"


@tool()
def read_file_content(file_path: str, max_lines: int = 100) -> str:
    """
    Read and return the content of a text file.
    
    Args:
        file_path: Path to the file to read
        max_lines: Maximum number of lines to read (default: 100)
    
    Returns:
        The content of the file or an error message
    """
    try:
        path = Path(file_path).resolve()
        
        if not path.exists():
            return f"❌ File does not exist: {file_path}"
        
        if not path.is_file():
            return f"❌ Path is not a file: {file_path}"
        
        # Check file size
        size = path.stat().st_size
        if size > 1024 * 1024:  # 1MB limit
            return f"❌ File too large ({size:,} bytes). Maximum size is 1MB."
        
        # Read file content
        with open(path, 'r', encoding='utf-8', errors='ignore') as file:
            lines = []
            line_count = 0
            
            for line in file:
                if line_count >= max_lines:
                    lines.append(f"\n... (truncated after {max_lines} lines)")
                    break
                lines.append(f"{line_count + 1:4d}| {line.rstrip()}")
                line_count += 1
        
        content = "\n".join(lines)
        
        return f"📄 File: {path}\n📊 Size: {size:,} bytes, {line_count} lines\n\n{content}"
        
    except UnicodeDecodeError:
        return f"❌ Cannot read file (binary or encoding issue): {file_path}"
    except Exception as e:
        return f"❌ Error reading file: {e}"


@tool()
def write_file_content(file_path: str, content: str, append: bool = False) -> str:
    """
    Write content to a file.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        append: Whether to append to existing file (default: False, overwrites)
    
    Returns:
        Success or error message
    """
    try:
        path = Path(file_path).resolve()
        
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        mode = 'a' if append else 'w'
        action = "appended to" if append else "written to"
        
        with open(path, mode, encoding='utf-8') as file:
            file.write(content)
        
        size = path.stat().st_size
        
        return f"✅ Content {action} file: {path}\n📊 File size: {size:,} bytes"
        
    except Exception as e:
        return f"❌ Error writing file: {e}"


@tool()
def get_system_info() -> str:
    """
    Get basic system information.
    
    Returns:
        System information including OS, Python version, working directory, etc.
    """
    try:
        import platform
        import sys
        
        info = []
        info.append("🖥️ System Information:")
        info.append(f"  OS: {platform.system()} {platform.release()}")
        info.append(f"  Architecture: {platform.architecture()[0]}")
        info.append(f"  Machine: {platform.machine()}")
        info.append(f"  Python: {sys.version.split()[0]}")
        info.append(f"  Working Directory: {os.getcwd()}")
        info.append(f"  User: {os.getenv('USERNAME', os.getenv('USER', 'Unknown'))}")
        
        # Environment variables of interest
        env_vars = ['PATH', 'PYTHONPATH', 'VIRTUAL_ENV', 'CONDA_DEFAULT_ENV']
        for var in env_vars:
            value = os.getenv(var)
            if value:
                if var == 'PATH':
                    # Truncate PATH for readability
                    paths = value.split(os.pathsep)
                    if len(paths) > 3:
                        value = os.pathsep.join(paths[:3]) + f" ... (+{len(paths)-3} more)"
                info.append(f"  {var}: {value}")
        
        return "\n".join(info)
        
    except Exception as e:
        return f"❌ Error getting system info: {e}"


@tool()
def find_files(search_pattern: str, directory: str = ".", max_results: int = 50) -> str:
    """
    Search for files matching a pattern in a directory tree.
    
    Args:
        search_pattern: Pattern to search for (supports wildcards like *.py, *test*)
        directory: Directory to search in (default: current directory)
        max_results: Maximum number of results to return (default: 50)
    
    Returns:
        List of matching files with their paths and sizes
    """
    try:
        path = Path(directory).resolve()
        
        if not path.exists():
            return f"❌ Directory does not exist: {directory}"
        
        if not path.is_dir():
            return f"❌ Path is not a directory: {directory}"
        
        # Search for files
        matches = []
        count = 0
        
        for file_path in path.rglob(search_pattern):
            if count >= max_results:
                break
                
            if file_path.is_file():
                try:
                    size = file_path.stat().st_size
                    relative_path = file_path.relative_to(path)
                    size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                    matches.append(f"  📄 {relative_path} ({size_str})")
                    count += 1
                except OSError:
                    relative_path = file_path.relative_to(path)
                    matches.append(f"  📄 {relative_path} (size unknown)")
                    count += 1
        
        if not matches:
            return f"🔍 No files found matching pattern '{search_pattern}' in {path}"
        
        result = [f"🔍 Found {len(matches)} files matching '{search_pattern}' in {path}:\n"]
        result.extend(matches)
        
        if count >= max_results:
            result.append(f"\n... (showing first {max_results} results)")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"❌ Error searching files: {e}"


def get_all_custom_tools() -> List[Any]:
    """
    Get all available custom tools.
    
    Returns:
        List of all custom tool functions
    """
    return [
        run_command,
        list_files,
        read_file_content,
        write_file_content,
        get_system_info,
        find_files
    ]


def get_custom_tools_info() -> dict:
    """
    Get information about all custom tools.
    
    Returns:
        Dictionary with tool information
    """
    tools = get_all_custom_tools()
    
    tools_info = {
        "total_tools": len(tools),
        "tools": []
    }
    
    for tool_func in tools:
        tool_info = {
            "name": tool_func.name,
            "description": tool_func.description,
            "func": tool_func.func.__name__ if hasattr(tool_func, 'func') else tool_func.__name__
        }
        tools_info["tools"].append(tool_info)
    
    return tools_info
