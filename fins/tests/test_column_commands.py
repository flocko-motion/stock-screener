"""
Tests for the ColumnCommand functionality in FINS.

These tests verify that column commands correctly add columns and filter baskets.
"""

import unittest
from typing import List, Dict, Any, Optional
from ..dsl.parser import FinsParser
from ..entities.basket import Basket
from ..entities.symbol import Symbol
from ..storage.entity import Entity
from ..dsl.commands.pe import PEColumnCommand

class ColumnCommandTest(unittest.TestCase):
    """Tests for column commands."""
    
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
        result = self.execute_flow("AAPL MSFT GOOGL -> pe")
        
        # Should have the PE column
        self.assertIn("pe", result.columns)
        
        # All symbols should have a PE value (or None)
        for symbol in result.symbols:
            self.assertIn(symbol, result.columns["pe"])
            
    def test_pe_column_filter(self):
        """Test filtering by PE ratio."""
        # Get all symbols with PE data
        all_result = self.execute_flow("AAPL MSFT GOOGL AMZN META -> pe")
        
        # Filter to PE < 30
        filtered_result = self.execute_flow("AAPL MSFT GOOGL AMZN META -> pe < 30")
        
        # Filtered result should have the PE column
        self.assertIn("pe", filtered_result.columns)
        
        # All symbols in filtered result should have PE < 30
        for symbol in filtered_result.symbols:
            pe = filtered_result.columns["pe"].get(symbol)
            if pe is not None:
                self.assertLess(pe, 30)
                
        # Filtered result should have fewer or equal symbols
        self.assertLessEqual(len(filtered_result.symbols), len(all_result.symbols))


class MultipleColumnCommandTests(ColumnCommandTest):
    """Tests for using multiple column commands."""
    
    def test_multiple_columns(self):
        """Test adding multiple columns to a basket."""
        result = self.execute_flow("AAPL MSFT GOOGL -> pe -> div_yield")
        
        # Should have both columns
        self.assertIn("pe", result.columns)
        self.assertIn("div_yield", result.columns)
        
    def test_column_then_filter(self):
        """Test adding a column and then filtering by it."""
        result = self.execute_flow("AAPL MSFT GOOGL AMZN META -> pe -> pe < 30")
        
        # Should have the PE column
        self.assertIn("pe", result.columns)
        
        # All symbols should have PE < 30
        for symbol in result.symbols:
            pe = result.columns["pe"].get(symbol)
            if pe is not None:
                self.assertLess(pe, 30)
                
    def test_multiple_filters(self):
        """Test applying multiple filters."""
        result = self.execute_flow("AAPL MSFT GOOGL AMZN META -> pe < 30 -> mcap > 500B")
        
        # Should have both columns
        self.assertIn("pe", result.columns)
        self.assertIn("mcap", result.columns)
        
        # All symbols should satisfy both conditions
        for symbol in result.symbols:
            pe = result.columns["pe"].get(symbol)
            mcap = result.columns["mcap"].get(symbol)
            
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
        result = self.execute_flow("$tech pe")
        
        # Should have the PE column
        self.assertIn("pe", result.columns)
        
    def test_explicit_column_filter(self):
        """Test filtering using explicit syntax."""
        # Create a basket
        self.execute_flow("AAPL MSFT GOOGL AMZN META -> $tech")
        
        # Filter using explicit syntax
        result = self.execute_flow("$tech pe < 30")
        
        # Should have the PE column
        self.assertIn("pe", result.columns)
        
        # All symbols should have PE < 30
        for symbol in result.symbols:
            pe = result.columns["pe"].get(symbol)
            if pe is not None:
                self.assertLess(pe, 30)


if __name__ == "__main__":
    unittest.main() 