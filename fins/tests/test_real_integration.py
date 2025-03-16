"""
Real integration tests for FINS.

These tests use the actual FINS engine with real data sources to verify
that complete command flows work as expected.
"""

import unittest
from typing import List, Dict, Any, Optional
from ..dsl.parser import FinsParser
from ..entities.basket import Basket
from ..entities.symbol import Symbol
from ..storage.entity import Entity

class RealIntegrationTest(unittest.TestCase):
    """Base class for real integration tests."""
    
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
        
    def assert_basket_contains_symbols(self, basket: Basket, expected_symbols: List[str]):
        """
        Assert that a basket contains the expected symbols.
        
        Args:
            basket: The basket to check
            expected_symbols: List of symbol names that should be in the basket
        """
        actual_symbols = [symbol.name for symbol in basket.symbols]
        for symbol in expected_symbols:
            self.assertIn(symbol, actual_symbols, f"Symbol {symbol} not found in basket")
        
    def assert_basket_size(self, basket: Basket, expected_size: int):
        """
        Assert that a basket has the expected number of symbols.
        
        Args:
            basket: The basket to check
            expected_size: Expected number of symbols
        """
        self.assertEqual(len(basket.symbols), expected_size, 
                         f"Basket has {len(basket.symbols)} symbols, expected {expected_size}")
        
    def assert_basket_has_column(self, basket: Basket, column_name: str):
        """
        Assert that a basket has a specific column.
        
        Args:
            basket: The basket to check
            column_name: Name of the column that should exist
        """
        self.assertIn(column_name, basket.columns, f"Column {column_name} not found in basket")
        
    def assert_basket_sorted_by(self, basket: Basket, column: str, ascending: bool = True):
        """
        Assert that a basket is sorted by a specific column.
        
        Args:
            basket: The basket to check
            column: The column to check sorting by
            ascending: Whether the sort should be ascending (True) or descending (False)
        """
        values = []
        for symbol in basket.symbols:
            if column in basket.columns:
                values.append(basket.columns[column].get(symbol))
            else:
                values.append(getattr(symbol, column, None))
                
        # Filter out None values
        values = [v for v in values if v is not None]
        
        # Check if the list is sorted
        sorted_values = sorted(values, reverse=not ascending)
        self.assertEqual(values, sorted_values, 
                         f"Basket is not sorted by {column} in {'ascending' if ascending else 'descending'} order")


class BasicFlowTests(RealIntegrationTest):
    """Tests for basic FINS command flows."""
    
    def test_create_simple_basket(self):
        """Test creating a simple basket of stocks."""
        result = self.execute_flow("AAPL MSFT")
        
        self.assertIsInstance(result, Basket)
        self.assert_basket_contains_symbols(result, ["AAPL", "MSFT"])
        self.assert_basket_size(result, 2)
        
    def test_add_symbol_to_basket(self):
        """Test adding a symbol to a basket."""
        result = self.execute_flow("AAPL MSFT -> + GOOGL")
        
        self.assertIsInstance(result, Basket)
        self.assert_basket_contains_symbols(result, ["AAPL", "MSFT", "GOOGL"])
        self.assert_basket_size(result, 3)
        
    def test_explicit_add_syntax(self):
        """Test the explicit add syntax."""
        # First create a basket with AAPL and MSFT
        self.execute_flow("AAPL MSFT -> $tech")
        
        # Then add GOOGL using explicit syntax
        result = self.execute_flow("$tech + GOOGL")
        
        self.assertIsInstance(result, Basket)
        self.assert_basket_contains_symbols(result, ["AAPL", "MSFT", "GOOGL"])
        self.assert_basket_size(result, 3)


class ColumnCommandTests(RealIntegrationTest):
    """Tests for column commands."""
    
    def test_add_pe_column(self):
        """Test adding a PE column to a basket."""
        result = self.execute_flow("AAPL MSFT GOOGL -> pe")
        
        self.assertIsInstance(result, Basket)
        self.assert_basket_contains_symbols(result, ["AAPL", "MSFT", "GOOGL"])
        self.assert_basket_has_column(result, "pe")
        
    def test_filter_by_pe(self):
        """Test filtering a basket by PE ratio."""
        # This test assumes that at least one of the stocks has a PE < 30
        result = self.execute_flow("AAPL MSFT GOOGL AMZN META -> pe < 30")
        
        self.assertIsInstance(result, Basket)
        self.assert_basket_has_column(result, "pe")
        
        # Check that all symbols in the result have PE < 30
        for symbol in result.symbols:
            pe = result.columns["pe"].get(symbol)
            if pe is not None:  # Some symbols might not have PE data
                self.assertLess(pe, 30, f"Symbol {symbol.name} has PE {pe} which is not < 30")


class SortCommandTests(RealIntegrationTest):
    """Tests for sort commands."""
    
    def test_sort_by_market_cap(self):
        """Test sorting a basket by market cap."""
        result = self.execute_flow("AAPL MSFT GOOGL -> sort mcap desc")
        
        self.assertIsInstance(result, Basket)
        self.assert_basket_contains_symbols(result, ["AAPL", "MSFT", "GOOGL"])
        self.assert_basket_sorted_by(result, "mcap", ascending=False)
        
    def test_explicit_sort_syntax(self):
        """Test the explicit sort syntax."""
        # First create a basket with tech stocks
        self.execute_flow("AAPL MSFT GOOGL -> $tech")
        
        # Then sort using explicit syntax
        result = self.execute_flow("$tech sort pe")
        
        self.assertIsInstance(result, Basket)
        self.assert_basket_contains_symbols(result, ["AAPL", "MSFT", "GOOGL"])
        self.assert_basket_sorted_by(result, "pe", ascending=True)


class ComplexFlowTests(RealIntegrationTest):
    """Tests for complex command flows."""
    
    def test_filter_then_sort(self):
        """Test filtering a basket and then sorting it."""
        result = self.execute_flow("AAPL MSFT GOOGL AMZN META -> pe < 30 -> sort mcap desc")
        
        self.assertIsInstance(result, Basket)
        self.assert_basket_has_column(result, "pe")
        self.assert_basket_sorted_by(result, "mcap", ascending=False)
        
        # Check that all symbols in the result have PE < 30
        for symbol in result.symbols:
            pe = result.columns["pe"].get(symbol)
            if pe is not None:  # Some symbols might not have PE data
                self.assertLess(pe, 30, f"Symbol {symbol.name} has PE {pe} which is not < 30")
    
    def test_multiple_columns_and_filter(self):
        """Test adding multiple columns and filtering."""
        result = self.execute_flow("AAPL MSFT GOOGL -> pe -> div_yield > 1%")
        
        self.assertIsInstance(result, Basket)
        self.assert_basket_has_column(result, "pe")
        self.assert_basket_has_column(result, "div_yield")
        
        # Check that all symbols in the result have div_yield > 1%
        for symbol in result.symbols:
            div_yield = result.columns["div_yield"].get(symbol)
            if div_yield is not None:  # Some symbols might not have dividend data
                self.assertGreater(div_yield, 0.01, 
                                  f"Symbol {symbol.name} has div_yield {div_yield} which is not > 1%")


if __name__ == "__main__":
    unittest.main() 