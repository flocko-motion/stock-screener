#!/usr/bin/env python
"""
FINS CLI - Command Line Interface for the Financial Insights and Notation System.
This module serves as the main entry point for the FINS application.
"""

import sys
import argparse
from pathlib import Path

# Add the parent directory to the path to allow imports from the fins package
sys.path.insert(0, str(Path(__file__).parent.parent))

from fins.dsl import FinsParser


def main():
    """
    Main entry point for the FINS CLI.
    Parses command line arguments and executes the appropriate command.
    """
    parser = argparse.ArgumentParser(
        description="FINS: Financial Insights and Notation System"
    )
    parser.add_argument(
        "command", 
        nargs="?", 
        help="FINS command to execute (e.g., 'AAPL MSFT -> sort mcap desc')"
    )
    parser.add_argument(
        "-f", "--file", 
        help="Execute commands from a file"
    )
    parser.add_argument(
        "-i", "--interactive", 
        action="store_true", 
        help="Start interactive mode"
    )
    parser.add_argument(
        "-v", "--version", 
        action="store_true", 
        help="Show version information"
    )

    args = parser.parse_args()

    # Import version from __init__.py
    from fins import __version__

    if args.version:
        print(f"FINS version {__version__}")
        return 0

    fins_parser = FinsParser()

    if args.interactive:
        run_interactive_mode(fins_parser)
    elif args.file:
        exit_code, _ = run_file_mode(args.file, fins_parser)
        return exit_code
    elif args.command:
        exit_code, _ = run_command_mode(args.command, fins_parser)
        return exit_code
    else:
        parser.print_help()
        return 1


def run_interactive_mode(fins_parser):
    """
    Run FINS in interactive mode, accepting commands from stdin.
    
    Args:
        fins_parser: An instance of FinsParser
    """
    print(f"FINS Interactive Mode. Type 'exit' or 'quit' to exit.")
    while True:
        try:
            command = input("fins> ")
            if command.lower() in ("exit", "quit"):
                break
            if not command.strip():
                continue
                
            result = fins_parser.parse(command)
            print(result)
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
    return 0


def run_file_mode(file_path, fins_parser):
    """
    Execute FINS commands from a file.
    
    Args:
        file_path: Path to the file containing FINS commands
        fins_parser: An instance of FinsParser
        
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
            print(result)
            results.append(result)
            
        return 0, results
    except FileNotFoundError:
        error_msg = f"Error: File '{file_path}' not found"
        print(error_msg)
        return 1, error_msg
    except Exception as e:
        error_msg = f"Error: {e}"
        print(error_msg)
        return 1, error_msg


def run_command_mode(command, fins_parser):
    """
    Execute a single FINS command.
    
    Args:
        command: FINS command to execute
        fins_parser: An instance of FinsParser
        
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        result = fins_parser.parse(command)
        print(result)
        return 0, result
    except Exception as e:
        error_msg = f"Error: {e}"
        print(error_msg)
        return 1, error_msg


if __name__ == "__main__":
    sys.exit(main()) 