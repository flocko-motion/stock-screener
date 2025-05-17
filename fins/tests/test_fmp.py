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
        result = fmp.price_history("AAPL")
        
        # Verify the result is a DataFrame
        self.assertIsInstance(result, pd.DataFrame)
        
        # Verify the DataFrame has the expected structure
        self.assertIn("close", result.columns)
        
        # Verify the DataFrame has data
        self.assertTrue(len(result) > 0)

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

    def test_load_ticker_history_caching(self):
        """Test that ticker history is properly cached."""
        # First call should hit the API
        print("\nTesting load_ticker_history caching...")
        
        # Get the cache path that would be used by the load_ticker_history function
        cache_path = get_cache_path("AAPL", "fmp_history", "pkl")
        print(f"Expected cache path: {cache_path}")
        
        # Delete the cache file if it exists
        if os.path.exists(cache_path):
            os.remove(cache_path)
            print(f"Removed existing cache file: {cache_path}")
        
        print("First call (should hit API):")
        start_time = time.time()
        result1 = fmp.price_history("AAPL")
        first_call_time = time.time() - start_time
        print(f"First call took {first_call_time:.2f} seconds")
        
        # Verify the cache file was created
        self.assertTrue(os.path.exists(cache_path), f"Cache file was not created at {cache_path}")
        
        # Second call should use cache
        print("Second call (should use cache):")
        start_time = time.time()
        result2 = fmp.price_history("AAPL")
        second_call_time = time.time() - start_time
        print(f"Second call took {second_call_time:.2f} seconds")
        
        # Verify the results are the same
        pd.testing.assert_frame_equal(result1, result2)
        
        # Verify the cache file exists
        self.assertTrue(os.path.exists(cache_path), "Cache file does not exist")



if __name__ == "__main__":
    unittest.main() 