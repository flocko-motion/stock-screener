import unittest
from datetime import datetime

from fins.entities.plugins import *
from fins.terminal.symbols import *
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

    def test_subtract_basket(self):
        b0 = Basket(AAPL * 2, GOOG * 3)
        b1 = Basket(GOOG * 2)
        b2 = b0 - b1
        self.assertBasket(
            b0,{
            "AAPL": 2,
            "GOOG": 3,
        })
        self.assertBasket(
            b1,{
                "GOOG": 2,
            }
        )
        self.assertBasket(
            b2,{
                "AAPL": 2,
                "GOOG": 1,
            }
        )

    def test_slash_item(self):
        self.assertBasket(
            Basket(AAPL * 2, GOOG * 3) / GOOG,{
            "AAPL": 2,
        })


    def test_slash_basket(self):
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

    def test_minimal_plugin_application(self):
        res = Basket(AAPL * 1.5, GOOG * 10)(Industry())
        df = res.df()
        
        self.assertEqual(df.iloc[0]['Industry'], 'Consumer Electronics')
        self.assertEqual(df.iloc[1]['Industry'], 'Internet Content & Information')

    def test_two_plugin_application(self):
        res = Basket(AAPL * 1.5, GOOG * 10)(Industry() >> Name() >> Name(alias="foo"))
        df = res.df()

        self.assertEqual(df.iloc[0]['Industry'], 'Consumer Electronics')
        self.assertEqual(df.iloc[1]['Industry'], 'Internet Content & Information')
        self.assertEqual(df.iloc[0]['Name'], 'Apple Inc.')
        self.assertEqual(df.iloc[1]['Name'], 'Alphabet Inc.')
        self.assertEqual(df.iloc[0]['foo'], 'Apple Inc.')
        self.assertEqual(df.iloc[1]['foo'], 'Alphabet Inc.')

    def test_plugin_alias_collision(self):
        try:
            Basket(AAPL * 1.5, GOOG * 10)(Industry() >> Name() >> Name())
            assert False
        except RuntimeError as e:
            assert str(e).startswith('Plugin Name already exists')

        try:
            Basket(AAPL * 1.5, GOOG * 10)(Industry(alias="foo") >> Name(alias="foo"))
            assert False
        except RuntimeError as e:
            assert str(e).startswith('Plugin foo already exists in pipe')

    def test_plugins_update(self):
        res = Basket(AAPL * 1.5)(Name() >> LastUpdatePrice() >> LastUpdateProfile())
        df = res.df()
        self.assertIsNotNone(df.iloc[0]['LastPriceUpdate'])
        self.assertIsNotNone(df.iloc[0]['LastProfileUpdate'])

        res2 = Basket(AAPL * 1.5)(Update(older_than=datetime.now()) >> LastUpdatePrice() >> LastUpdateProfile())
        df2 = res2.df()
        self.assertGreater(df2.iloc[0]['LastPriceUpdate'], df.iloc[0]['LastPriceUpdate'])
        self.assertGreater(df2.iloc[0]['LastProfileUpdate'], df.iloc[0]['LastProfileUpdate'])

    def test_plugins_simple_price(self):
        res = Basket(AAPL)(WeeklyClose() >> MonthlyClose() >> PlotEach())
        data = res.output_data()
        self.assertTrue(len(data._series) == 2)

    def test_plugins_crop_time_series(self):
        res = Basket(AAPL, GOOG, META)(WeeklyClose() >> Crop() >> PlotEach())
        data = res.output_data()

    def test_plugins_cagr(self):
        res = Basket(AAPL, GOOG, META)(Cagr())
        df = res.df()
        self.assertIsNotNone(df.iloc[0]['Cagr'])

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


if __name__ == "__main__":
    unittest.main() 