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
        return self.parser.parse(command_str)

    def assert_no_error(self, output: Output):
        self.assertNotEqual(output.output_type, "error", f"Output contains an error: {output.data}")

    def assert_error(self, output: Output):
        self.assertEqual(output.output_type, "error", "Output does not contain an error")

        
    def basket_from_output(self, output: Output) -> Basket:
        self.assert_no_error(output)
        self.assertEqual(output.output_type, "basket",
                        f"Expected output type 'basket', got '{output.output_type}'")
        self.assertIsInstance(output.data, Basket, 
                             f"Expected data to be a Basket, got {type(output.data)}")
        return output.data
        
    def assert_basket_items(self, basket: Basket, expected: dict[str, float]):
        actual_items = [item.ticker for item in basket.items]
        self.assertSetEqual(set(expected.keys()), set(actual_items), f"Basket does not contain expected symbols, got {actual_items}, expected {expected}")
        for item in basket.items:
            expected_value = expected.get(item.ticker, None)
            self.assertIsNotNone(expected_value, f"Basket does not contain expected symbol {item.ticker}")
            self.assertEqual(item.amount, expected_value, f"Basket item {item.ticker} has weight {item.amount}, expected {expected_value}")

    def assert_basket_has_column(self, basket: Basket, column_name: str):
        self.assertTrue(basket.has_column(column_name),
                       f"Column {column_name} not found in basket")
        
    def assert_basket_sorted_by(self, basket: Basket, column: str, ascending: bool = True):
        values = []
        for item in basket.items:
            col = basket.get_column(column)
            if col:
                values.append(col.value(item.ticker))
            else:
                values.append(getattr(item, column, None))
                
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

    def test_simple_weighted_basket_creation(self):
        output = self.execute_flow("3x AAPL 2 MSFT 1.7111x GOOGL AMZN 1.25723 NFLX")

        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL": 3, "MSFT": 2, "GOOGL": 1.7111, "AMZN": 1, "NFLX": 1.25723})

    def test_add_items_to_basket_bad_syntax(self):
        """ missing an operator/function, so we don't know how to act on the left hand input """
        output = self.execute_flow("AAPL MSFT -> GOOGL")
        self.assert_error(output)

    def test_add_items_to_basket(self):
        output = self.execute_flow("AAPL MSFT -> + GOOGL 7x NFLX")
        
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL":1, "MSFT":1, "GOOGL":1, "NFLX":7})

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

    def test_basket_to_variable_and_multiply(self):
        self.new_parser()

        output = self.execute_flow("3x AAPL 1.7 MSFT-> $a")
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL":3, "MSFT": 1.7})

        output = self.execute_flow("2x $a")
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL":6, "MSFT": 3.4})

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

    def test_complex_basket_creation(self):
        output = self.execute_flow("AAPL + 3x MSFT + 2.1 NFLX")

        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL": 1, "MSFT": 3, "NFLX": 2.1})


    def test_complex_basket_operation(self):
        output = self.execute_flow("AAPL 3x MSFT 2.1 NFLX + 7 GOOG AMZN 0.002 TPL -> $a -> + 2x V")

        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL": 1, "MSFT": 3, "NFLX": 2.1, "GOOG": 7, "AMZN": 1, "TPL": 0.002, "V": 2})




class ColumnCommandTests(DslTests):
    """Tests for column commands."""
    
    def test_add_pe_column(self):
        """Test adding a PE column to a basket."""
        output = self.execute_flow("AAPL -> .pe()")
        
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL":1})
        self.assert_basket_has_column(basket, "pe")

        assert basket.data()['pe'].iloc[0] > 0
        
    def test_add_multiple_columns(self):
        """Test adding multiple columns to a basket."""
        output = self.execute_flow("AAPL MSFT GOOGL -> .pe() -> .mcap()")
        
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL":1, "MSFT":1, "GOOGL":1})
        self.assert_basket_has_column(basket, "pe")
        self.assert_basket_has_column(basket, "mcap")

    def test_add_column_with_alias(self):
        """Test adding a column with an alias."""
        output = self.execute_flow("AAPL MSFT GOOGL -> .ratio = .pe()")
        
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL":1, "MSFT":1, "GOOGL":1})
        self.assert_basket_has_column(basket, "ratio")

    def test_add_column_with_args(self):
        """Test adding a column with arguments."""
        output = self.execute_flow("AAPL MSFT GOOGL -> .cagr(years=5)")
        
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_items(basket, {"AAPL":1, "MSFT":1, "GOOGL":1})
        self.assert_basket_has_column(basket, "cagr")


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
    
    def test_multiple_columns(self):
        """Test adding multiple columns."""
        output = self.execute_flow("AAPL MSFT GOOGL -> .pe() -> .mcap() -> .div()")
        
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_has_column(basket, "pe")
        self.assert_basket_has_column(basket, "mcap")
        self.assert_basket_has_column(basket, "div")

    def test_complex_column_flow(self):
        """Test complex column operations."""
        output = self.execute_flow("""
            AAPL MSFT GOOGL -> 
            .pe() ->                    # Add PE column
            .growth = .cagr(years=5) -> # Add CAGR with custom name
            .div()                      # Add dividend yield
        """)
        
        self.assertIsInstance(output, Output)
        basket = self.basket_from_output(output)
        self.assert_basket_has_column(basket, "pe")
        self.assert_basket_has_column(basket, "growth")
        self.assert_basket_has_column(basket, "div")


if __name__ == "__main__":
    unittest.main()
