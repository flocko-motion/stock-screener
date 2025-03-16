"""
Tests for the new command syntax in FINS.

These tests verify that both explicit and implicit command syntax work correctly
with the new command structure.
"""

import unittest
from typing import List, Dict, Any, Optional
from ..dsl.parser import FinsParser
from ..entities.basket import Basket
from ..entities.symbol import Symbol
from ..storage.entity import Entity

class CommandSyntaxTest(unittest.TestCase):
    """Tests for the new command syntax."""
    
    def setUp(self):
        """Set up the test environment."""
        self.parser = FinsParser()
        
    def execute_flow(self, command_str: str) -> Entity:
        """
        Execute a FINS command flow.
        
        Args:
            command_str: The command string to execute
            
        Returns:
            The result of the command execution
        """
        return self.parser.parse(command_str)
        
    def assert_equal_baskets(self, basket1: Basket, basket2: Basket):
        """
        Assert that two baskets contain the same symbols.
        
        Args:
            basket1: First basket
            basket2: Second basket
        """
        symbols1 = sorted([symbol.name for symbol in basket1.symbols])
        symbols2 = sorted([symbol.name for symbol in basket2.symbols])
        self.assertEqual(symbols1, symbols2, "Baskets contain different symbols")
        
        # Check that columns are the same
        self.assertEqual(set(basket1.columns.keys()), set(basket2.columns.keys()),
                        "Baskets have different columns")


class ExplicitVsImplicitSyntaxTests(CommandSyntaxTest):
    """Tests comparing explicit vs implicit command syntax."""
    
    def test_add_command(self):
        """Test that explicit and implicit add syntax produce the same result."""
        # Implicit syntax
        implicit_result = self.execute_flow("AAPL MSFT -> + GOOGL")
        
        # Explicit syntax
        self.execute_flow("AAPL MSFT -> $temp")
        explicit_result = self.execute_flow("$temp + GOOGL")
        
        # Results should be the same
        self.assert_equal_baskets(implicit_result, explicit_result)
        
    def test_sort_command(self):
        """Test that explicit and implicit sort syntax produce the same result."""
        # Implicit syntax
        implicit_result = self.execute_flow("AAPL MSFT GOOGL -> sort mcap desc")
        
        # Explicit syntax
        self.execute_flow("AAPL MSFT GOOGL -> $temp")
        explicit_result = self.execute_flow("$temp sort mcap desc")
        
        # Results should be the same
        self.assert_equal_baskets(implicit_result, explicit_result)
        
    def test_column_command(self):
        """Test that explicit and implicit column command syntax produce the same result."""
        # Implicit syntax
        implicit_result = self.execute_flow("AAPL MSFT GOOGL -> pe")
        
        # Explicit syntax
        self.execute_flow("AAPL MSFT GOOGL -> $temp")
        explicit_result = self.execute_flow("$temp pe")
        
        # Results should be the same
        self.assert_equal_baskets(implicit_result, explicit_result)
        
    def test_filter_command(self):
        """Test that explicit and implicit filter syntax produce the same result."""
        # Implicit syntax
        implicit_result = self.execute_flow("AAPL MSFT GOOGL AMZN -> pe < 30")
        
        # Explicit syntax
        self.execute_flow("AAPL MSFT GOOGL AMZN -> $temp")
        explicit_result = self.execute_flow("$temp pe < 30")
        
        # Results should be the same
        self.assert_equal_baskets(implicit_result, explicit_result)


class ChainedCommandTests(CommandSyntaxTest):
    """Tests for chained commands with mixed syntax."""
    
    def test_mixed_syntax_chain(self):
        """Test a chain of commands with mixed syntax."""
        # Create a reference basket using only implicit syntax
        implicit_result = self.execute_flow(
            "AAPL MSFT GOOGL -> + AMZN -> pe -> sort pe asc -> pe < 30"
        )
        
        # Create a basket using mixed syntax
        self.execute_flow("AAPL MSFT GOOGL -> $temp")
        mixed_result = self.execute_flow(
            "$temp + AMZN -> pe -> sort pe asc -> pe < 30"
        )
        
        # Results should be the same
        self.assert_equal_baskets(implicit_result, mixed_result)
        
    def test_storage_forwarding(self):
        """Test that storage operations forward their input."""
        # Store and continue
        result = self.execute_flow("AAPL MSFT -> $tech -> + GOOGL")
        
        # Should contain all three symbols
        symbols = sorted([symbol.name for symbol in result.symbols])
        self.assertEqual(symbols, ["AAPL", "GOOGL", "MSFT"])
        
        # Verify the stored variable
        stored = self.execute_flow("$tech")
        stored_symbols = sorted([symbol.name for symbol in stored.symbols])
        self.assertEqual(stored_symbols, ["AAPL", "MSFT"])


class ColumnCommandFunctionalityTests(CommandSyntaxTest):
    """Tests for the unified column command functionality."""
    
    def test_column_add_only(self):
        """Test that a column command adds a column without filtering."""
        result = self.execute_flow("AAPL MSFT GOOGL -> pe")
        
        # Should contain all symbols
        self.assertEqual(len(result.symbols), 3)
        
        # Should have the PE column
        self.assertIn("pe", result.columns)
        
    def test_column_add_and_filter(self):
        """Test that a column command can both add a column and filter."""
        # First get the full basket with PE column
        full_result = self.execute_flow("AAPL MSFT GOOGL AMZN META -> pe")
        
        # Then filter it
        filtered_result = self.execute_flow("AAPL MSFT GOOGL AMZN META -> pe < 30")
        
        # Filtered result should have fewer symbols
        self.assertLessEqual(len(filtered_result.symbols), len(full_result.symbols))
        
        # All symbols in filtered result should have PE < 30
        for symbol in filtered_result.symbols:
            pe = filtered_result.columns["pe"].get(symbol)
            if pe is not None:
                self.assertLess(pe, 30)


if __name__ == "__main__":
    unittest.main() 