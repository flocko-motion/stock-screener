"""
Tests for the ColumnCommand functionality in FINS.

These tests verify that column commands correctly add columns and filter baskets.
"""

import unittest
from typing import List, Dict, Any, Optional
from ..dsl.parser import FinsParser
from ..entities.basket import Basket
from ..entities.symbol import Symbol
from ..entities.entity import Entity
from ..dsl.commands.pe import PEColumnCommand
from ..dsl.output import Output

class ColumnCommandTest(unittest.TestCase):
    """Tests for column commands."""
    
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


class PEColumnCommandTests(ColumnCommandTest):
    """Tests for the PE column command."""
    
    def test_pe_column_creation(self):
        """Test that the PE column command creates a PE column."""
        # Create a PE command instance
        pe_command = PEColumnCommand()
        
        # Check properties
        self.assertEqual(pe_command.column_name, "pe")
        self.assertEqual(pe_command.input_type, Basket)
        self.assertEqual(pe_command.output_type, Basket)
        
    def test_pe_column_add(self):
        """Test adding a PE column to a basket."""
        output = self.execute_flow("AAPL MSFT GOOGL -> pe")
        basket = self.get_basket_from_output(output)
        
        # Should have the PE column
        self.assertIn("pe", basket.columns)
        
        # All symbols should have a PE value (or None)
        for symbol in basket.symbols:
            self.assertIn(symbol, basket.columns["pe"])
            
    def test_pe_column_filter(self):
        """Test filtering by PE ratio."""
        # Get all symbols with PE data
        all_output = self.execute_flow("AAPL MSFT GOOGL AMZN META -> pe")
        all_basket = self.get_basket_from_output(all_output)
        
        # Filter to PE < 30
        filtered_output = self.execute_flow("AAPL MSFT GOOGL AMZN META -> pe < 30")
        filtered_basket = self.get_basket_from_output(filtered_output)
        
        # Filtered result should have the PE column
        self.assertIn("pe", filtered_basket.columns)
        
        # All symbols in filtered result should have PE < 30
        for symbol in filtered_basket.symbols:
            pe = filtered_basket.columns["pe"].get(symbol)
            if pe is not None:
                self.assertLess(pe, 30)
                
        # Filtered result should have fewer or equal symbols
        self.assertLessEqual(len(filtered_basket.symbols), len(all_basket.symbols))


class MultipleColumnCommandTests(ColumnCommandTest):
    """Tests for using multiple column commands."""
    
    def test_multiple_columns(self):
        """Test adding multiple columns to a basket."""
        output = self.execute_flow("AAPL MSFT GOOGL -> pe -> div_yield")
        basket = self.get_basket_from_output(output)
        
        # Should have both columns
        self.assertIn("pe", basket.columns)
        self.assertIn("div_yield", basket.columns)
        
    def test_column_then_filter(self):
        """Test adding a column and then filtering by it."""
        output = self.execute_flow("AAPL MSFT GOOGL AMZN META -> pe -> pe < 30")
        basket = self.get_basket_from_output(output)
        
        # Should have the PE column
        self.assertIn("pe", basket.columns)
        
        # All symbols should have PE < 30
        for symbol in basket.symbols:
            pe = basket.columns["pe"].get(symbol)
            if pe is not None:
                self.assertLess(pe, 30)
                
    def test_multiple_filters(self):
        """Test applying multiple filters."""
        output = self.execute_flow("AAPL MSFT GOOGL AMZN META -> pe < 30 -> mcap > 500B")
        basket = self.get_basket_from_output(output)
        
        # Should have both columns
        self.assertIn("pe", basket.columns)
        self.assertIn("mcap", basket.columns)
        
        # All symbols should satisfy both conditions
        for symbol in basket.symbols:
            pe = basket.columns["pe"].get(symbol)
            mcap = basket.columns["mcap"].get(symbol)
            
            if pe is not None:
                self.assertLess(pe, 30)
                
            if mcap is not None:
                self.assertGreater(mcap, 500_000_000_000)  # 500B


class ExplicitColumnCommandTests(ColumnCommandTest):
    """Tests for explicit column command syntax."""
    
    def test_explicit_column_add(self):
        """Test adding a column using explicit syntax."""
        # Create a basket
        self.execute_flow("AAPL MSFT GOOGL -> $tech")
        
        # Add PE column using explicit syntax
        output = self.execute_flow("$tech pe")
        basket = self.get_basket_from_output(output)
        
        # Should have the PE column
        self.assertIn("pe", basket.columns)
        
    def test_explicit_column_filter(self):
        """Test filtering using explicit syntax."""
        # Create a basket
        self.execute_flow("AAPL MSFT GOOGL AMZN META -> $tech")
        
        # Filter using explicit syntax
        output = self.execute_flow("$tech pe < 30")
        basket = self.get_basket_from_output(output)
        
        # Should have the PE column
        self.assertIn("pe", basket.columns)
        
        # All symbols should have PE < 30
        for symbol in basket.symbols:
            pe = basket.columns["pe"].get(symbol)
            if pe is not None:
                self.assertLess(pe, 30)


if __name__ == "__main__":
    unittest.main() 