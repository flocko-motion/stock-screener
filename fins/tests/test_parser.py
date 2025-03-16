#!/usr/bin/env python
"""
Tests for the FINS parser.

This module contains unit tests for the FINS parser, testing various command
structures and ensuring the parser correctly interprets and executes them.
"""

import unittest
import sys
from pathlib import Path

# Add the parent directory to the path to allow imports from the fins package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fins.dsl import FinsParser


class TestFinsParser(unittest.TestCase):
    """Test cases for the FINS parser."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = FinsParser()

    def test_basic_symbol_list(self):
        """Test parsing a basic list of symbols."""
        result = self.parser.parse("AAPL MSFT GOOGL")
        self.assertIsNotNone(result)
        # Add more specific assertions based on expected output structure

    def test_create_basket(self):
        """Test creating a basket and storing it in a variable."""
        result = self.parser.parse("AAPL MSFT GOOGL -> $tech_basket")
        self.assertIsNotNone(result)
        # Verify the basket was created correctly

    def test_add_symbol(self):
        """Test adding a symbol to a basket."""
        self.parser.parse("AAPL MSFT -> $test_basket")
        result = self.parser.parse("$test_basket -> + GOOGL")
        self.assertIsNotNone(result)
        # Verify the symbol was added correctly

    def test_remove_symbol(self):
        """Test removing a symbol from a basket."""
        self.parser.parse("AAPL MSFT GOOGL -> $test_basket")
        result = self.parser.parse("$test_basket -> - MSFT")
        self.assertIsNotNone(result)
        # Verify the symbol was removed correctly

    def test_sort_command(self):
        """Test sorting a basket."""
        self.parser.parse("AAPL MSFT GOOGL -> $test_basket")
        result = self.parser.parse("$test_basket -> sort mcap desc")
        self.assertIsNotNone(result)
        # Verify the basket was sorted correctly

    def test_filter_command(self):
        """Test filtering a basket."""
        self.parser.parse("AAPL MSFT GOOGL -> $test_basket")
        result = self.parser.parse("$test_basket -> mcap > 1000B")
        self.assertIsNotNone(result)
        # Verify the basket was filtered correctly

    def test_add_column(self):
        """Test adding an analysis column to a basket."""
        self.parser.parse("AAPL MSFT GOOGL -> $test_basket")
        result = self.parser.parse("$test_basket -> cagr 5y")
        self.assertIsNotNone(result)
        # Verify the column was added correctly

    def test_complex_flow(self):
        """Test a complex command flow."""
        result = self.parser.parse(
            "AAPL MSFT GOOGL -> + NFLX -> - MSFT -> sort mcap desc -> cagr 5y -> /my_tech_basket"
        )
        self.assertIsNotNone(result)
        # Verify the entire flow worked correctly

    def test_persistent_variable(self):
        """Test storing a basket in a persistent variable."""
        result = self.parser.parse("AAPL MSFT GOOGL -> /persistent_basket")
        self.assertIsNotNone(result)
        # Verify the basket was stored in a persistent variable

    def test_non_persistent_variable(self):
        """Test storing a basket in a non-persistent variable."""
        result = self.parser.parse("AAPL MSFT GOOGL -> $non_persistent_basket")
        self.assertIsNotNone(result)
        # Verify the basket was stored in a non-persistent variable
        
    def test_variable_storage_and_retrieval(self):
        """Test that variables are properly stored and can be retrieved."""
        # Create and store a basket
        result = self.parser.parse("AAPL MSFT GOOGL -> $tech_stocks")
        print(f"Result of creating basket: {result}")
        print(f"Parser variables: {self.parser.variables}")
        
        # Verify the variable exists in the parser's variables dictionary
        self.assertIn("$tech_stocks", self.parser.variables)
        
        # Retrieve the variable and verify it returns the expected result
        result = self.parser.parse("$tech_stocks")
        self.assertIsNotNone(result)
        self.assertIn("Retrieved variable", result)
        
        # Test variable locking
        self.parser.parse("lock $tech_stocks")
        self.assertIn("$tech_stocks", self.parser.locked_variables)
        
        # Test variable unlocking
        self.parser.parse("unlock $tech_stocks")
        self.assertNotIn("$tech_stocks", self.parser.locked_variables)


if __name__ == "__main__":
    unittest.main() 