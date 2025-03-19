"""
Real integration tests for FINS.

These tests use the actual FINS engine with real data sources to verify
that complete command flows work as expected.
"""

import unittest

from ..storage import Storage
from ..dsl.parser import FinsParser
from ..entities import Entity, Basket, BasketItem
from ..dsl.output import Output

class DslTests(unittest.TestCase):
    """Base class for real integration tests."""
    
    def setUp(self):
        """Set up the test environment."""
        self.new_parser()

    def new_parser(self ):
        self.parser = FinsParser(Storage.temp())

    def execute_flow(self, command_str: str) -> Output:
        """
        Execute a FINS command flow.
        
        Args:
            command_str: The command string to execute
            
        Returns:
            The result of the command execution
        """
        return self.parser.parse(command_str)

    def assert_no_error(self, output: Output):
        """
        Assert that an output does not contain an error.

        Args:
            output: The Output object to check
        """
        self.assertNotEqual(output.output_type, "error", f"Output contains an error: {output.data}")
        
    def basket_from_output(self, output: Output) -> Basket:
        """
        Extract a basket from an Output object.
        
        Args:
            output: The Output object
            
        Returns:
            The basket contained in the output
            
        Raises:
            AssertionError: If the output does not contain a basket
        """
        self.assert_no_error(output)
        self.assertEqual(output.output_type, "basket",
                        f"Expected output type 'basket', got '{output.output_type}'")
        self.assertIsInstance(output.data, Basket, 
                             f"Expected data to be a Basket, got {type(output.data)}")
        return output.data
        
    def assert_basket_items(self, basket: Basket, expected: dict[str, float]):
        """
        Assert that a basket contains the expected symbols.
        
        Args:
            basket: The basket to check
            expected: List of symbol names that should be in the basket
        """
        actual_items = [item.ticker for item in basket.items]
        self.assertSetEqual(set(expected.keys()), set(actual_items), f"Basket does not contain expected symbols, got {actual_items}, expected {expected}")
        for item in basket.items:
            expected_value = expected.get(item.ticker, None)
            self.assertIsNotNone(expected_value, f"Basket does not contain expected symbol {item.ticker}")
            self.assertEqual(item.amount, expected_value, f"Basket item {item.ticker} has weight {item.amount}, expected {expected_value}")

        
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
        for symbol in basket.items:
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


class BasicFlowTests(DslTests):
    """Tests for basic FINS command flows."""

    def test_simple_basket_creation(self):
        output = self.execute_flow("AAPL MSFT GOOGL")

        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL": 1, "MSFT": 1, "GOOGL": 1})

    def test_add_items_to_basket(self):
        output = self.execute_flow("AAPL MSFT -> + GOOGL")
        
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL":1, "MSFT":1, "GOOGL":1})

    def test_add_duplicate_items_to_basket(self):
        output = self.execute_flow("AAPL MSFT GOOGL -> + GOOGL")

        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL": 1, "MSFT": 1, "GOOGL": 2})

    def test_add_overlapping_items_to_basket(self):
        output = self.execute_flow("AAPL MSFT GOOGL -> + GOOGL NFLX")

        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL": 1, "MSFT": 1, "GOOGL": 2, "NFLX": 1})

    def test_remove_items_from_basket(self):
        output = self.execute_flow("AAPL MSFT GOOGL -> - MSFT")

        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL": 1, "GOOGL": 1})

    def test_basket_to_variable(self):
        # First create a basket with AAPL and MSFT
        self.new_parser()

        output = self.execute_flow("AAPL -> $a")
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL":1})

        output = self.execute_flow("$a")
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL":1})

    def test_basket_to_file(self):
        # First create a basket with AAPL and MSFT
        self.new_parser()

        # write first file
        output = self.execute_flow("AAPL -> /a/b/c")
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL":1})

        # write another file with another name
        output = self.execute_flow("MSFT -> /d/e")
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"MSFT":1})

        # retrieve first file
        output = self.execute_flow("/a/b/c")
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL":1})

    def test_basket_to_file_overwrite(self):
        # First create a basket with AAPL and MSFT
        self.new_parser()

        # write first file
        output = self.execute_flow("AAPL -> /a/b/c")
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL":1})

        # overwrite file
        output = self.execute_flow("MSFT -> /a/b/c")
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"MSFT":1})

        # retrieve
        output = self.execute_flow("/a/b/c")
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"MSFT":1})

    def test_add_variable_and_basket(self):
        # First create a basket with AAPL and MSFT
        self.new_parser()

        # prepare variable
        output = self.execute_flow("AAPL -> $a")
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL": 1})

        # addition
        output = self.execute_flow("$a -> + MSFT")
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL":1, "MSFT":1})

    def test_add_variable_and_basket_short(self):
        # First create a basket with AAPL and MSFT
        self.new_parser()

        # prepare variable
        output = self.execute_flow("AAPL -> $a")
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL": 1})

        # addition
        output = self.execute_flow("$a + MSFT")
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL":1, "MSFT":1})

        # addition of multiple items
        output = self.execute_flow("$a + MSFT NFLX")
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL":1, "MSFT":1, "NFLX":1})

    def test_complex_basket_operation(self):
        output = self.execute_flow("AAPL 3x MSFT 2.1 NFLX + 7 GOOG AMZN 0.002 TPL -> $a -> + 2x V")

        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL": 1, "MSFT": 1, "NFLX": 1})


class ColumnCommandTests(DslTests):
    """Tests for column commands."""
    
    def test_add_pe_column(self):
        """Test adding a PE column to a basket."""
        output = self.execute_flow("AAPL MSFT GOOGL -> pe")
        
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL":1, "MSFT":1, "GOOGL":1})
        self.assert_basket_has_column(basket, "pe")
        
    def test_filter_by_pe(self):
        """Test filtering a basket by PE ratio."""
        # This test assumes that at least one of the stocks has a PE < 30
        output = self.execute_flow("AAPL MSFT GOOGL AMZN META -> pe < 30")
        
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_has_column(basket, "pe")
        
        # Check that all symbols in the result have PE < 30
        for symbol in basket.symbols:
            pe = basket.columns["pe"].get(symbol)
            if pe is not None:  # Some symbols might not have PE data
                self.assertLess(pe, 30, f"Symbol {symbol.name} has PE {pe} which is not < 30")


class SortCommandTests(DslTests):
    """Tests for sort commands."""
    
    def test_sort_by_market_cap(self):
        """Test sorting a basket by market cap."""
        output = self.execute_flow("AAPL MSFT GOOGL -> sort mcap desc")
        
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, ["AAPL", "MSFT", "GOOGL"])
        self.assert_basket_sorted_by(basket, "mcap", ascending=False)
        
    def test_explicit_sort_syntax(self):
        """Test the explicit sort syntax."""
        # First create a basket with tech stocks
        self.execute_flow("AAPL MSFT GOOGL -> $tech")
        
        # Then sort using explicit syntax
        output = self.execute_flow("$tech sort pe")
        
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, ["AAPL", "MSFT", "GOOGL"])
        self.assert_basket_sorted_by(basket, "pe", ascending=True)


class ComplexFlowTests(DslTests):
    """Tests for complex command flows."""
    
    def test_filter_then_sort(self):
        """Test filtering a basket and then sorting it."""
        output = self.execute_flow("AAPL MSFT GOOGL AMZN META -> pe < 30 -> sort mcap desc")
        
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_has_column(basket, "pe")
        self.assert_basket_sorted_by(basket, "mcap", ascending=False)
        
        # Check that all symbols in the result have PE < 30
        for symbol in basket.symbols:
            pe = basket.columns["pe"].get(symbol)
            if pe is not None:  # Some symbols might not have PE data
                self.assertLess(pe, 30, f"Symbol {symbol.name} has PE {pe} which is not < 30")
    
    def test_multiple_columns_and_filter(self):
        """Test adding multiple columns and filtering."""
        output = self.execute_flow("AAPL MSFT GOOGL -> pe -> div_yield > 0.01")
        
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_has_column(basket, "pe")
        self.assert_basket_has_column(basket, "div_yield")
        
        # Check that all symbols in the result have div_yield > 1%
        for symbol in basket.symbols:
            div_yield = basket.columns["div_yield"].get(symbol)
            if div_yield is not None:  # Some symbols might not have dividend data
                self.assertGreater(div_yield, 0.01, 
                                  f"Symbol {symbol.name} has div_yield {div_yield} which is not > 1%")


if __name__ == "__main__":
    unittest.main()
