#!/usr/bin/env python
"""
FINS Test Runner

This script runs all unit tests for the FINS system.
It can be used to run specific test modules or all tests.
"""

import sys
import unittest
import argparse
from pathlib import Path

# Add the parent directory to the path to allow imports from the fins package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def run_tests(test_pattern=None, verbose=False):
    """
    Run the FINS test suite.
    
    Args:
        test_pattern: Optional pattern to filter tests
        verbose: Whether to show verbose output
    
    Returns:
        int: Number of test failures
    """
    loader = unittest.TestLoader()
    
    if test_pattern:
        suite = loader.loadTestsFromName(test_pattern)
    else:
        # Discover all tests in the tests directory
        start_dir = Path(__file__).parent
        suite = loader.discover(start_dir=start_dir, pattern='test_*.py')
    
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return len(result.failures) + len(result.errors)


def main():
    """
    Main entry point for the test runner.
    Parses command line arguments and runs the tests.
    """
    parser = argparse.ArgumentParser(
        description="FINS Test Runner"
    )
    parser.add_argument(
        "test_pattern", 
        nargs="?", 
        help="Optional test pattern (e.g., 'test_parser' or 'test_parser.TestFinsParser.test_basic_command')"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Show verbose output"
    )
    
    args = parser.parse_args()
    
    print(f"Running FINS tests{f' matching {args.test_pattern}' if args.test_pattern else ''}...")
    failures = run_tests(args.test_pattern, args.verbose)
    
    return failures


if __name__ == "__main__":
    sys.exit(main()) 