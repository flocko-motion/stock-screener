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
from ..entities.entity import Entity
from ..dsl.output import Output

class CommandSyntaxTest(unittest.TestCase):
    """Tests for the new command syntax."""
    
    def setUp(self):
        """Set up the test environment."""
        self.parser = FinsParser()
        
    def execute_flow(self, command_str: str) -> Output:
        """
        Execute a FINS command flow.
        
        Args:
            command_str: The command string to execute
            
        Returns:
            The result of the command execution
        """
        return self.parser.parse(command_str)
        
    def get_basket_from_output(self, output: Output) -> Basket:
        """
        Extract a basket from an Output object.
        
        Args:
            output: The Output object
            
        Returns:
            The basket contained in the output
            
        Raises:
            AssertionError: If the output does not contain a basket
        """
        self.assertEqual(output.output_type, "basket", 
                        f"Expected output type 'basket', got '{output.output_type}'")
        self.assertIsInstance(output.data, Basket, 
                             f"Expected data to be a Basket, got {type(output.data)}")
        return output.data
        
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
        implicit_output = self.execute_flow("AAPL MSFT -> + GOOGL")
        implicit_basket = self.get_basket_from_output(implicit_output)
        
        # Explicit syntax
        self.execute_flow("AAPL MSFT -> $temp")
        explicit_output = self.execute_flow("$temp + GOOGL")
        explicit_basket = self.get_basket_from_output(explicit_output)
        
        # Results should be the same
        self.assert_equal_baskets(implicit_basket, explicit_basket)
        
    def test_sort_command(self):
        """Test that explicit and implicit sort syntax produce the same result."""
        # Implicit syntax
        implicit_output = self.execute_flow("AAPL MSFT GOOGL -> sort mcap desc")
        implicit_basket = self.get_basket_from_output(implicit_output)
        
        # Explicit syntax
        self.execute_flow("AAPL MSFT GOOGL -> $temp")
        explicit_output = self.execute_flow("$temp sort mcap desc")
        explicit_basket = self.get_basket_from_output(explicit_output)
        
        # Results should be the same
        self.assert_equal_baskets(implicit_basket, explicit_basket)
        
    def test_column_command(self):
        """Test that explicit and implicit column command syntax produce the same result."""
        # Implicit syntax
        implicit_output = self.execute_flow("AAPL MSFT GOOGL -> pe")
        implicit_basket = self.get_basket_from_output(implicit_output)
        
        # Explicit syntax
        self.execute_flow("AAPL MSFT GOOGL -> $temp")
        explicit_output = self.execute_flow("$temp pe")
        explicit_basket = self.get_basket_from_output(explicit_output)
        
        # Results should be the same
        self.assert_equal_baskets(implicit_basket, explicit_basket)
        
    def test_filter_command(self):
        """Test that explicit and implicit filter syntax produce the same result."""
        # Implicit syntax
        implicit_output = self.execute_flow("AAPL MSFT GOOGL AMZN -> pe < 30")
        implicit_basket = self.get_basket_from_output(implicit_output)
        
        # Explicit syntax
        self.execute_flow("AAPL MSFT GOOGL AMZN -> $temp")
        explicit_output = self.execute_flow("$temp pe < 30")
        explicit_basket = self.get_basket_from_output(explicit_output)
        
        # Results should be the same
        self.assert_equal_baskets(implicit_basket, explicit_basket)


class ChainedCommandTests(CommandSyntaxTest):
    """Tests for chained commands with mixed syntax."""
    
    def test_mixed_syntax_chain(self):
        """Test a chain of commands with mixed syntax."""
        # Create a reference basket using only implicit syntax
        implicit_output = self.execute_flow(
            "AAPL MSFT GOOGL -> + AMZN -> pe -> sort pe asc -> pe < 30"
        )
        implicit_basket = self.get_basket_from_output(implicit_output)
        
        # Create a basket using mixed syntax
        self.execute_flow("AAPL MSFT GOOGL -> $temp")
        mixed_output = self.execute_flow(
            "$temp + AMZN -> pe -> sort pe asc -> pe < 30"
        )
        mixed_basket = self.get_basket_from_output(mixed_output)
        
        # Results should be the same
        self.assert_equal_baskets(implicit_basket, mixed_basket)
        
    def test_storage_forwarding(self):
        """Test that storage operations forward their input."""
        # Store and continue
        output = self.execute_flow("AAPL MSFT -> $tech -> + GOOGL")
        basket = self.get_basket_from_output(output)
        
        # Should contain all three symbols
        symbols = sorted([symbol.name for symbol in basket.symbols])
        self.assertEqual(symbols, ["AAPL", "GOOGL", "MSFT"])
        
        # Verify the stored variable
        stored_output = self.execute_flow("$tech")
        stored_basket = self.get_basket_from_output(stored_output)
        stored_symbols = sorted([symbol.name for symbol in stored_basket.symbols])
        self.assertEqual(stored_symbols, ["AAPL", "MSFT"])


class ColumnCommandFunctionalityTests(CommandSyntaxTest):
    """Tests for the unified column command functionality."""
    
    def test_column_add_only(self):
        """Test that a column command adds a column without filtering."""
        output = self.execute_flow("AAPL MSFT GOOGL -> pe")
        basket = self.get_basket_from_output(output)
        
        # Should contain all symbols
        self.assertEqual(len(basket.symbols), 3)
        
        # Should have the PE column
        self.assertIn("pe", basket.columns)
        
    def test_column_add_and_filter(self):
        """Test that a column command can both add a column and filter."""
        # First get the full basket with PE column
        full_output = self.execute_flow("AAPL MSFT GOOGL AMZN META -> pe")
        full_basket = self.get_basket_from_output(full_output)
        
        # Then filter it
        filtered_output = self.execute_flow("AAPL MSFT GOOGL AMZN META -> pe < 30")
        filtered_basket = self.get_basket_from_output(filtered_output)
        
        # Filtered result should have fewer symbols
        self.assertLessEqual(len(filtered_basket.symbols), len(full_basket.symbols))
        
        # All symbols in filtered result should have PE < 30
        for symbol in filtered_basket.symbols:
            pe = filtered_basket.columns["pe"].get(symbol)
            if pe is not None:
                self.assertLess(pe, 30)


if __name__ == "__main__":
    unittest.main() 