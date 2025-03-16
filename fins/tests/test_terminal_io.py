#!/usr/bin/env python
"""
Tests for terminal input/output.

This module contains unit tests for the terminal interface, testing various
command inputs and verifying the expected outputs.
"""

import unittest
import sys
import io
from pathlib import Path
from unittest import mock

# Add the parent directory to the path to allow imports from the fins package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fins.cli import main, run_command_mode
from fins.dsl import FinsParser


class TestTerminalIO(unittest.TestCase):
    """Test cases for terminal input/output."""

    def setUp(self):
        """Set up test fixtures."""
        # Redirect stdout to capture output for main() function tests
        self.stdout_patcher = mock.patch('sys.stdout', new_callable=io.StringIO)
        self.mock_stdout = self.stdout_patcher.start()
        
        # Create a parser instance with a mocked parse method
        self.parser = FinsParser()
        self.original_parse = self.parser.parse
        self.parser.parse = mock.MagicMock()

    def tearDown(self):
        """Tear down test fixtures."""
        self.stdout_patcher.stop()
        # Restore the original parse method
        self.parser.parse = self.original_parse

    @mock.patch('fins.dsl.parser.FinsParser.parse')
    @mock.patch('sys.argv')
    def test_basic_command(self, mock_argv, mock_parse):
        """Test a basic command."""
        # Mock the parser response
        expected_output = "AAPL MSFT GOOGL"
        mock_parse.return_value = expected_output
        
        # Mock command line arguments
        mock_argv.return_value = ['fins', expected_output]
        
        # Run the command
        with mock.patch('sys.argv', ['fins', expected_output]):
            main()
        
        # Verify the output
        output = self.mock_stdout.getvalue().strip()
        self.assertEqual(output, expected_output)
        
        # Verify the parser was called with the correct command
        mock_parse.assert_called_once_with(expected_output)

    def test_create_basket(self):
        """Test creating a basket."""
        # Mock the parser response
        expected_output = "Created basket $tech_basket with symbols: AAPL, MSFT, GOOGL"
        self.parser.parse.return_value = expected_output
        
        # Run the command
        exit_code, result = run_command_mode("AAPL MSFT GOOGL -> $tech_basket", self.parser)
        
        # Verify the result
        self.assertEqual(exit_code, 0)
        self.assertEqual(result, expected_output)
        
        # Verify the parser was called with the correct command
        self.parser.parse.assert_called_once_with('AAPL MSFT GOOGL -> $tech_basket')

    def test_add_symbol(self):
        """Test adding a symbol to a basket."""
        # Mock the parser responses
        first_output = "Created basket $test_basket with symbols: AAPL, MSFT"
        second_output = "Added GOOGL to $test_basket"
        self.parser.parse.side_effect = [first_output, second_output]
        
        # Run the commands
        run_command_mode("AAPL MSFT -> $test_basket", self.parser)
        exit_code, result = run_command_mode("$test_basket -> + GOOGL", self.parser)
        
        # Verify the result
        self.assertEqual(exit_code, 0)
        self.assertEqual(result, second_output)
        
        # Verify the parser was called with the correct commands
        self.parser.parse.assert_has_calls([
            mock.call('AAPL MSFT -> $test_basket'),
            mock.call('$test_basket -> + GOOGL')
        ])

    def test_sort_command(self):
        """Test sorting a basket."""
        # Mock the parser responses
        expected_output = "Sorted $test_basket by mcap in descending order"
        self.parser.parse.return_value = expected_output
        
        # Run the command
        exit_code, result = run_command_mode("$test_basket -> sort mcap desc", self.parser)
        
        # Verify the result
        self.assertEqual(exit_code, 0)
        self.assertEqual(result, expected_output)
        
        # Verify the parser was called with the correct command
        self.parser.parse.assert_called_once_with('$test_basket -> sort mcap desc')

    def test_filter_command(self):
        """Test filtering a basket."""
        # Mock the parser responses
        expected_output = "Filtered $test_basket to symbols with mcap > 1000B"
        self.parser.parse.return_value = expected_output
        
        # Run the command
        exit_code, result = run_command_mode("$test_basket -> mcap > 1000B", self.parser)
        
        # Verify the result
        self.assertEqual(exit_code, 0)
        self.assertEqual(result, expected_output)
        
        # Verify the parser was called with the correct command
        self.parser.parse.assert_called_once_with('$test_basket -> mcap > 1000B')

    def test_complex_flow(self):
        """Test a complex command flow."""
        # Mock the parser responses
        expected_output = "Created persistent basket /my_tech_basket with symbols: AAPL, GOOGL, NFLX sorted by mcap with cagr column"
        self.parser.parse.return_value = expected_output
        
        # Run the command
        exit_code, result = run_command_mode("AAPL GOOGL NFLX -> sort mcap desc -> cagr 5y -> /my_tech_basket", self.parser)
        
        # Verify the result
        self.assertEqual(exit_code, 0)
        self.assertEqual(result, expected_output)
        
        # Verify the parser was called with the correct command
        self.parser.parse.assert_called_once_with('AAPL GOOGL NFLX -> sort mcap desc -> cagr 5y -> /my_tech_basket')


if __name__ == "__main__":
    unittest.main() 