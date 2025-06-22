import unittest

from fins.terminal.symbols import *
from fins.entities import columns
from fins.entities.basket import Basket
from fins.entities.basket_item import BasketItem
from .tools import time_it, no_cache, unbuffered_output


class BasketTests(unittest.TestCase):

    def test_create_basket(self):
        self.assertBasket(Basket(AAPL * 1.5), {
            "AAPL": 1.5,
        })

    def test_add_item(self):
        self.assertBasket(
            Basket(AAPL * 2) + (GOOG * 1.7),{
            "AAPL": 2,
            "GOOG": 1.7,
        })

    def test_add_baskets(self):
        self.assertBasket(
            Basket(AAPL * 2) + Basket(GOOG * 1.7),{
            "AAPL": 2,
            "GOOG": 1.7,
        })

    def test_remove_item(self):
        self.assertBasket(
            Basket(AAPL * 2, GOOG * 3) / GOOG,{
            "AAPL": 2,
        })

    def test_remove_basket(self):
        # subtraction follows set algebra, thus ignores weights
        self.assertBasket(
            Basket(AAPL * 2, GOOG * 3) / Basket(GOOG * 2),{
            "AAPL": 2,
        })


    def test_add_baskets_overlap(self):
        self.assertBasket(
            Basket(AAPL * 2, GOOG * 1) + Basket(GOOG * 1.7),{
            "AAPL": 2,
            "GOOG": 2.7,
        })

    def test_multiply_weights(self):
        self.assertBasket(
            Basket(AAPL * 2, GOOG * 1) * 3, {
            "AAPL": 6,
            "GOOG": 3,
        })
        self.assertBasket(
            1.5 * Basket(AAPL * 2, GOOG * 1), {
            "AAPL": 3,
            "GOOG": 1.5,
        })



    def assertBasket(self, basket: Basket, expected: dict):
        """
        Assert that the basket contains exactly the expected items with expected weights.

        Args:
            basket: The basket to check
            expected: Dict mapping ticker symbols to expected weights
        """
        # Check that we have the right number of items
        self.assertEqual(len(basket._items), len(expected),
                         f"Expected {len(expected)} items, got {len(basket._items)}")

        # Create a dict of actual items for comparison
        actual = {item.ticker: item.amount for item in basket._items}

        # Check each expected item
        for ticker, expected_weight in expected.items():
            self.assertIn(ticker, actual, f"Expected ticker {ticker} not found in basket")
            self.assertAlmostEqual(actual[ticker], expected_weight, places=6,
                                   msg=f"Expected {ticker} weight {expected_weight}, got {actual[ticker]}")

        # Check that we don't have any unexpected items
        for ticker in actual:
            self.assertIn(ticker, expected, f"Unexpected ticker {ticker} found in basket")


    # @time_it
    # @no_cache
    # @unbuffered_output
    # def test_multithreaded_basket_creation_one(self):
    #     symbols = ["AAPL"]
    #     basket = Basket.from_symbols(symbols)
    #     assert len(basket._items) == len(symbols)
    #
    # @time_it
    # @no_cache
    # @unbuffered_output
    # def test_multithreaded_basket_creation(self):
    #     symbols = ["ATLFF","ALFNF","ACMDY","ASBPW","CWBR","ATIW","FBTC","FXED","PFS","DGRS","BUFIX","GPFT","FFTI","ASXSF","BKAYY","AMH-PE","RGNX","WSCC","RXST","ACU","TIBGX","ZSPY","AHG","GOP","FTA","HROWM","FORD","RSYEX","NNAVW","HNGZY","TNGRF","MARUY","HIZOF","ALRY","RUSHA","ORMP","WLGS","SRTS","DISSX","ULNV","SOGFF","DFLIW","TCEFF","APPZ","CGO","YAMCF","NIKLF",]
    #     # symbols = symbols[0:10]
    #     basket = Basket.from_symbols(symbols, max_workers=50)
    #     assert len(basket._items) == len(symbols)


if __name__ == "__main__":
    unittest.main() 