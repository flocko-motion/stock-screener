import time
import unittest
from datetime import datetime, date
import numpy as np
import pandas as pd

from fins.data_sources import fmp
from fins.entities.plugins import *
from fins.terminal import *
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
        self.assertIsNotNone(df.iloc[0]['LastUpdatePrice'])
        self.assertIsNotNone(df.iloc[0]['LastUpdateProfile'])

        res2 = Basket(AAPL * 1.5)(Update(older_than=datetime.now()) >> LastUpdatePrice() >> LastUpdateProfile())
        df2 = res2.df()
        self.assertGreater(df2.iloc[0]['LastUpdatePrice'], df.iloc[0]['LastUpdatePrice'])
        self.assertGreater(df2.iloc[0]['LastUpdateProfile'], df.iloc[0]['LastUpdateProfile'])

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
        self.assertIsNotNone(df.iloc[0]['CAGR'])

    def test_plugins_mcap(self):
        res = Basket(AAPL, GOOG, META)(Mcap())
        df = res.df()
        self.assertIsNotNone(df.iloc[0]['MCap'])
        self.assertGreater(df.iloc[0]['MCap'], 0)

    def test_plugins_dividend_yield(self):
        res = Basket(AAPL, GOOG, META)(DividendYield())
        df = res.df()
        self.assertIsNotNone(df.iloc[0]['DividendYield'])

    def test_plugins_npm(self):
        res = Basket(AAPL, GOOG, META)(Npm())
        df = res.df()
        self.assertIsNotNone(df.iloc[0]['NPM'])

    def test_plugins_pe(self):
        res = Basket(AAPL, GOOG, META)(Pe())
        df = res.df()
        self.assertIsNotNone(df.iloc[0]['PE'])

    def test_plugins_peg(self):
        res = Basket(AAPL, GOOG, META)(Peg())
        df = res.df()
        self.assertIsNotNone(df.iloc[0]['PEG'])

    def test_plugins_roe(self):
        res = Basket(AAPL, GOOG, META)(Roe())
        df = res.df()
        self.assertIsNotNone(df.iloc[0]['ROE'])

    def test_plugins_vol(self):
        res = Basket(AAPL, GOOG, META)(Vol())
        df = res.df()
        self.assertIsNotNone(df.iloc[0]['Volume'])
        self.assertGreater(df.iloc[0]['Volume'], 0)

    def test_plugins_inception(self):
        res = Basket(AAPL, GOOG, META)(Inception())
        df = res.df()
        # Inception date might be None for some symbols
        inception_date = df.iloc[0]['Inception']
        if inception_date is not None:
            from datetime import datetime
            self.assertIsInstance(inception_date, datetime)

    def test_plugins_alive(self):
        res = Basket(AAPL, GOOG, META)(Alive())
        df = res.df()
        alive_value = df.iloc[0]['Alive']
        self.assertTrue(isinstance(alive_value, (bool, np.bool_)))

    def test_plugins_age(self):
        res = Basket(AAPL, GOOG, META)(Age())
        df = res.df()
        # Should return age in years as float (or None)
        age_value = df.iloc[0]['Age']
        if age_value is not None:
            self.assertIsInstance(age_value, (float, int))
            self.assertGreater(age_value, 0)  # Should be positive years

    def test_filter_age(self):
        df = Basket(AAPL, GOOG, META)(Age().min(10)).df()
        self.assertIn('Age', df.columns)
        for age in df['Age'].dropna():
            self.assertGreaterEqual(age, 10)

    def test_filter_mcap(self):
        df = Basket(AAPL, GOOG, META)(Mcap().min(1_000_000_000)).df()
        self.assertIn('MCap', df.columns)
        for mcap in df['MCap'].dropna():
            self.assertGreaterEqual(mcap, 1_000_000_000)

    def test_filter_chaining(self):
        df = Basket(AAPL, GOOG, META)(Age().min(10) >> Name() >> Mcap()).df()
        self.assertIn('Age', df.columns)
        self.assertIn('Name', df.columns)
        self.assertIn('MCap', df.columns)
        for age in df['Age'].dropna():
            self.assertGreaterEqual(age, 10)

    def test_filter_string_equality(self):
        df = Basket(AAPL, GOOG, META)(Sector().equals("Technology")).df()
        for sector in df['Sector'].dropna():
            self.assertEqual(sector, "Technology")

    def test_filter_none_handling(self):
        df = Basket(AAPL, GOOG, META)(Pe().min(0)).df()
        if 'PE' in df.columns:
            for pe in df['PE'].dropna():
                self.assertGreaterEqual(pe, 0)

    def test_filter_contains(self):
        df = Basket(AAPL, GOOG, META)(Name().contains("Inc")).df()
        if 'Name' in df.columns:
            for name in df['Name'].dropna():
                self.assertIn("Inc", name)

    def test_filter_multiple_conditions(self):
        df = Basket(AAPL, GOOG, META)(Age().min(5).max(50)).df()
        if 'Age' in df.columns:
            for age in df['Age'].dropna():
                self.assertGreaterEqual(age, 5)
                self.assertLessEqual(age, 50)

    def test_filter_within(self):
        df = Basket(AAPL, GOOG, META)(Age().within(10, 40)).df()
        if 'Age' in df.columns:
            for age in df['Age'].dropna():
                self.assertGreaterEqual(age, 10)
                self.assertLessEqual(age, 40)

    def test_filter_any(self):
        allowed_sectors = ["Technology", "Consumer Cyclical", "Communication Services"]
        df = Basket(AAPL, GOOG, META)(Sector().any(allowed_sectors)).df()
        if 'Sector' in df.columns:
            for sector in df['Sector'].dropna():
                self.assertIn(sector, allowed_sectors)

    def test_filter_exclude_multiple(self):
        excluded_sectors = ["Real Estate", "Utilities", "Energy"]
        df = Basket(AAPL, GOOG, META)(Sector().exclude(excluded_sectors)).df()
        if 'Sector' in df.columns:
            for sector in df['Sector'].dropna():
                self.assertNotIn(sector, excluded_sectors)

    def test_filter_around(self):
        baseline_df = Basket(AAPL, GOOG, META)(Pe()).df()
        if 'PE' in baseline_df.columns and not baseline_df['PE'].isna().all():
            pe_values = baseline_df['PE'].dropna()
            if len(pe_values) > 0:
                target_pe = pe_values.iloc[0]
                df = Basket(AAPL, GOOG, META)(Pe().around(target_pe, precision=0.2)).df()
                if 'PE' in df.columns:
                    lower_bound, upper_bound = target_pe * 0.8, target_pe * 1.2
                    for pe in df['PE'].dropna():
                        self.assertGreaterEqual(pe, lower_bound)
                        self.assertLessEqual(pe, upper_bound)

    def test_filter_dates(self):
        from datetime import datetime
        df_after = Basket(AAPL, GOOG, META)(Inception().min("2000-01-01")).df()
        if 'Inception' in df_after.columns:
            for date in df_after['Inception'].dropna():
                self.assertGreater(date, datetime(2000, 1, 1))
        
        df_before = Basket(AAPL, GOOG, META)(Inception().max(datetime(2020, 1, 1))).df()
        if 'Inception' in df_before.columns:
            for date in df_before['Inception'].dropna():
                self.assertLess(date, datetime(2020, 1, 1))

    def test_filter_boolean(self):
        df_alive = Basket(AAPL, GOOG, META)(Alive().true()).df()
        if 'Alive' in df_alive.columns:
            for value in df_alive['Alive'].dropna():
                self.assertTrue(value)
        
        df_not_alive = Basket(AAPL, GOOG, META)(Alive().false()).df()
        if 'Alive' in df_not_alive.columns:
            for value in df_not_alive['Alive'].dropna():
                self.assertFalse(value)

    # def test_big_update(self):
    #     fmp.DEBUG = True
    #     candidates = Screen(mcap_min=2 * Billion, limit=5000)
    #     print(f"Candidates for further screening: {len(candidates)}")
    #     print(candidates.to_dict())
    #     while True:
    #         try:
    #             candidates(Update(older_than="2025-06-01", max=100))
    #         except Exception as e:
    #             print(f"Exception during update: {e}")
    #             time.sleep(120)

    def test_top_plugin(self):
        """Test the Top plugin keeps only the first n items"""
        # Create a basket with 5 items
        original_basket = Basket(AAPL, GOOG, META, MSFT, TSLA)
        self.assertEqual(len(original_basket._items), 5)
        
        # Apply Top(3) to keep only first 3 items
        result = original_basket(Top(3))
        result_items = result.basket_items()
        
        # Should have exactly 3 items
        self.assertEqual(len(result_items), 3)
        
        # Should be the first 3 items in original order
        original_items = original_basket._items
        for i in range(3):
            self.assertEqual(result_items[i].ticker, original_items[i].ticker)
            self.assertEqual(result_items[i].amount, original_items[i].amount)

    def test_top_plugin_larger_than_basket(self):
        """Test Top plugin when n is larger than basket size"""
        basket = Basket(AAPL, GOOG)
        result = basket(Top(5))
        
        # Should keep all items when n > basket size
        self.assertEqual(len(result.basket_items()), 2)
        self.assertEqual(result.basket_items()[0].ticker, "AAPL")
        self.assertEqual(result.basket_items()[1].ticker, "GOOG")

    def test_top_plugin_validation(self):
        """Test Top plugin input validation"""
        with self.assertRaises(ValueError):
            Top(0)  # Should reject zero
        
        with self.assertRaises(ValueError):
            Top(-1)  # Should reject negative numbers
        
        with self.assertRaises(ValueError):
            Top("5")  # Should reject non-integers

    def test_top_plugin_chaining(self):
        """Test Top plugin works in chains"""
        # Create basket and apply Name plugin then Top
        result = Basket(AAPL, GOOG, META, MSFT)(Name() >> Top(2))
        
        # Should have Name field and only 2 items
        df = result.df()
        self.assertEqual(len(df), 2)
        self.assertIn('Name', df.columns)
        
        # Should be first 2 items
        items = result.basket_items()
        self.assertEqual(items[0].ticker, "AAPL")
        self.assertEqual(items[1].ticker, "GOOG")

    def test_alive(self):
        # we test with a symbol of which we know, that is has no data - it shouldn't pass the Alive() filter
        result = Basket(AAPL, VBLTX, GOOG)(Alive()).basket()
        self.assertEqual(len(result), 2)

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