#!/usr/bin/env python
"""
Tests for the FMP (Financial Modeling Prep) API wrapper.

This module contains unit tests for the FMP API wrapper, testing various
functions for retrieving financial data from the Financial Modeling Prep API.
"""

import unittest
import sys
import os
import time
import pandas as pd
from pathlib import Path
import shutil

# Add the parent directory to the path to allow imports from the fins package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fins.data_sources import fmp
from fins.data_sources.cache import get_cache_path, set_test_cache_dir, restore_cache_dir


class TestFMP(unittest.TestCase):
    """Test cases for the FMP API wrapper."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a test cache directory
        self.test_cache_dir = os.path.join(os.path.dirname(__file__), 'test_cache')
        os.makedirs(self.test_cache_dir, exist_ok=True)
        
        # Set the test cache directory
        set_test_cache_dir(self.test_cache_dir)
        
        # Store original rate limit interval
        self.original_rate_limit = fmp.RATE_LIMIT_INTERVAL
        
        # Print API key info for debugging (without revealing the key)
        key_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'api-keys', 'financialmodelingprep.key')
        print(f"API key file path: {key_file_path}")
        print(f"API key file exists: {os.path.exists(key_file_path)}")
        if os.path.exists(key_file_path):
            with open(key_file_path, 'r') as file:
                key = file.read().strip()
                print(f"API key length: {len(key)}")
                print(f"API key first 3 chars: {key[:3]}...")

    def tearDown(self):
        """Tear down test fixtures."""
        # Restore the original cache directory
        restore_cache_dir()
        
        # Restore the original rate limit
        fmp.RATE_LIMIT_INTERVAL = self.original_rate_limit
        
        # Clean up the test cache directory
        if os.path.exists(self.test_cache_dir):
            # Use shutil.rmtree to remove directories recursively
            shutil.rmtree(self.test_cache_dir)

    def test_api_get(self):
        """Test the api_get function with real API."""
        # Call the function with a simple endpoint
        result = fmp.api_get("stable/search-name", {"query": "Apple"})
        
        # Verify the result is a list and contains data
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
        
        # Verify at least one result contains "Apple"
        apple_found = False
        for item in result:
            if "Apple" in item.get("name", ""):
                apple_found = True
                break
        self.assertTrue(apple_found, "No results containing 'Apple' found")

    def test_search(self):
        """Test the search function with real API."""
        # Call the function
        result = fmp.search("Apple")
        
        # Verify the result is a list and contains data
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
        
        # Verify at least one result contains "Apple"
        apple_found = False
        for item in result:
            if "Apple" in item.get("name", ""):
                apple_found = True
                break
        self.assertTrue(apple_found, "No results containing 'Apple' found")

    def test_profile(self):
        """Test the profile function with real API."""
        # Call the function
        result = fmp.profile("AAPL")
        
        # Verify the result contains Apple's profile
        self.assertEqual(result["symbol"], "AAPL")
        self.assertIn("Apple", result["companyName"])

    def test_quote(self):
        """Test the quote function with real API."""
        # Call the function
        result = fmp.quote("AAPL")

        # Verify the result contains Apple's quote
        self.assertEqual(result["symbol"], "AAPL")
        self.assertIn("price", result)


    def test_price_history(self):
        """Test the load_ticker_history function with real API."""
        # Call the function
        monthly, weekly = fmp.price_history("AAPL")
        
        # Verify the result is a DataFrame
        for df in [monthly, weekly]:
            self.assertIsInstance(df, pd.DataFrame)
            self.assertIn("open", df.columns)
            self.assertIn("high", df.columns)
            self.assertIn("low", df.columns)
            self.assertIn("close", df.columns)
            self.assertIn("avg", df.columns)
            self.assertTrue(len(df) > 0)

    def test_search_name(self):
        """Test the search_name function with real API."""
        # Call the function
        result = fmp.search_name("Apple")
        
        # Verify the result is a list and contains data
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
        
        # Verify at least one result contains "Apple"
        apple_found = False
        for item in result:
            if "Apple" in item.get("name", ""):
                apple_found = True
                break
        self.assertTrue(apple_found, "No results containing 'Apple' found")

    def test_tradeable_symbols(self):
        """Test the tradeable_symbols function with real API."""
        # Call the function
        result = fmp.tradeable_symbols()
        
        # Verify the result is a list and contains data
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
        
        # Verify the expected fields are present in the response
        self.assertIn("symbol", result[0])
        self.assertIn("name", result[0])
        self.assertIn("exchange", result[0])

    # Not available in Starter-Plan
    # def test_etf_holder(self):
    #     """Test the etf_holder function with real API."""
    #     # Call the function with a known ETF
    #     result = fmp.etf_holder("SPY")
    #
    #     # Verify the result is a list and contains data
    #     self.assertIsInstance(result, list)
    #     self.assertTrue(len(result) > 0)
    #
    #     # Verify the expected fields are present in the response
    #     self.assertIn("asset", result[0])
    #     self.assertIn("name", result[0])
    #     self.assertIn("weightPercentage", result[0])


if __name__ == "__main__":
    unittest.main() 