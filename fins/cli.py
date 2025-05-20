#!/usr/bin/env python
"""
FINS CLI - Command Line Interface for the Financial Insights and Notation System.
This module serves as the main entry point for the FINS application.
"""

import sys
import argparse
from pathlib import Path
from typing import Tuple, Any, List, Optional
import os
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

# Add the parent directory to the path to allow imports from the fins package
sys.path.insert(0, str(Path(__file__).parent.parent))

from fins.dsl import FinsParser
from fins.dsl.output import Output
from fins.storage import Storage
from fins.formatting.formatters import TextBasketFormatter


def setup_storage_path() -> Path:
    """
    Set up the default storage path at ~/.fins/persistence.
    Creates the directory if it doesn't exist.
    
    Returns:
        Path: The storage directory path
    """
    storage_path = Path.home() / ".fins" / "persistence"
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path


def setup_history_file() -> Path:
    """
    Set up the command history file at ~/.fins/history.
    Creates the directory if it doesn't exist.
    
    Returns:
        Path: The history file path
    """
    history_dir = Path.home() / ".fins"
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir / "history"


def main():
    """
    Main entry point for the FINS CLI.
    Parses command line arguments and executes the appropriate command.
    """
    parser = argparse.ArgumentParser(
        description="FINS: Financial Insights and Notation System"
    )
    parser.add_argument(
        "-c", "--command",
        help="Execute a single FINS command (e.g., 'AAPL MSFT -> sort mcap desc')"
    )
    parser.add_argument(
        "-f", "--file", 
        help="Execute commands from a file"
    )
    parser.add_argument(
        "-v", "--version", 
        action="store_true", 
        help="Show version information"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    parser.add_argument(
        "--storage",
        help="Custom storage path (default: ~/.fins/persistence)",
        type=Path
    )

    args = parser.parse_args()

    # Import version from __init__.py
    from fins import __version__

    if args.version:
        print(f"FINS version {__version__}")
        return 0

    # Set up storage path and create Storage instance
    storage_path = args.storage if args.storage else setup_storage_path()
    storage = Storage(storage_path)
    fins_parser = FinsParser(storage)

    if args.command:
        exit_code, _ = run_command_mode(args.command, fins_parser, json_output=args.json)
        return exit_code
    elif args.file:
        exit_code, _ = run_file_mode(args.file, fins_parser, json_output=args.json)
        return exit_code
    else:
        # Interactive mode is now the default
        return run_interactive_mode(fins_parser, json_output=args.json)


def format_output(output: Output, json_output: bool = False) -> str:
    """
    Format an Output instance for display.
    
    Args:
        output: The Output instance to format
        json_output: Whether to output in JSON format
        
    Returns:
        str: The formatted output string
    """
    if json_output:
        return str(output)  # Uses Output.__str__ which returns JSON
        
    if output.output_type == "error":
        return f"Error: {str(output.data)}"
    elif output.output_type == "void":
        return ""
    elif output.output_type == "basket":
        # Format basket data with metadata using the text formatter
        formatter = TextBasketFormatter()
        result = formatter.format(output.data)
        if output.metadata:
            result += f"\nMetadata: {output.metadata}"
        return result
    else:
        return str(output.data)  # Just the data, not the full JSON


def run_interactive_mode(fins_parser: FinsParser, json_output: bool = False) -> int:
    """
    Run FINS in interactive mode, accepting commands from stdin.
    
    Args:
        fins_parser: An instance of FinsParser
        json_output: Whether to output in JSON format
        
    Returns:
        int: Exit code (0 for success)
    """
    print(f"FINS Interactive Mode. Type '?' for help, 'exit' or 'quit' to leave.")
    
    # Set up prompt session with history
    history_file = setup_history_file()
    session = PromptSession(history=FileHistory(str(history_file)))
    while True:
        try:
            command = session.prompt("F> ").strip()
            if not command:
                continue
            if command.lower() in ("exit", "quit"):
                break

            result = fins_parser.parse(command)
            print(format_output(result, json_output))
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except EOFError:
            break
        except Exception as e:
            print(f"Error: {e}")
    return 0


def run_file_mode(file_path: str, fins_parser: FinsParser, json_output: bool = False) -> Tuple[int, List[Output]]:
    """
    Execute FINS commands from a file.
    
    Args:
        file_path: Path to the file containing FINS commands
        fins_parser: An instance of FinsParser
        json_output: Whether to output in JSON format
        
    Returns:
        tuple: (exit_code, results) where exit_code is 0 for success, non-zero for failure
               and results is a list of command results
    """
    try:
        with open(file_path, 'r') as f:
            commands = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        
        results = []
        for command in commands:
            result = fins_parser.parse(command)
            print(format_output(result, json_output))
            results.append(result)
            
        return 0, results
    except FileNotFoundError:
        error = Output(f"File '{file_path}' not found", output_type="error")
        print(format_output(error, json_output))
        return 1, [error]
    except Exception as e:
        error = Output(e, output_type="error")
        print(format_output(error, json_output))
        return 1, [error]


def run_command_mode(command: str, fins_parser: FinsParser, json_output: bool = False) -> Tuple[int, Output]:
    """
    Execute a single FINS command.
    
    Args:
        command: FINS command to execute
        fins_parser: An instance of FinsParser
        json_output: Whether to output in JSON format

    Returns:
        tuple: (exit_code, result) where exit_code is 0 for success, non-zero for failure
    """
    try:
        result = fins_parser.parse(command)
        print(format_output(result, json_output))
        return 0, result
    except Exception as e:
        error = Output(e, output_type="error")
        print(format_output(error, json_output))
        return 1, error


if __name__ == "__main__":
    sys.exit(main()) 