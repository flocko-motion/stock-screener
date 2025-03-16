#!/usr/bin/env python
"""
Tests for elementary actions with the FMP API.

This module contains unit tests for basic interactions with the Financial Modeling Prep API,
testing the ability to query symbols, get stock data, and perform other elementary actions.
"""

import unittest
import sys
import os
import pandas as pd
from pathlib import Path
from unittest import mock
import shutil

# Add the parent directory to the path to allow imports from the fins package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fins.data_sources import fmp
from fins.data_sources.cache import set_test_cache_dir, restore_cache_dir


class TestFMPClient(unittest.TestCase):
    """Test cases for the FMP API client."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock cache directory for testing
        self.test_cache_dir = os.path.join(os.path.dirname(__file__), 'test_cache')
        os.makedirs(self.test_cache_dir, exist_ok=True)
        
        # Set the test cache directory
        set_test_cache_dir(self.test_cache_dir)

    def tearDown(self):
        """Tear down test fixtures."""
        # Restore the original cache directory
        restore_cache_dir()
        
        # Clean up the test cache directory
        if os.path.exists(self.test_cache_dir):
            # Use shutil.rmtree to remove directories recursively
            shutil.rmtree(self.test_cache_dir)

    @mock.patch('fins.fmp.requests.get')
    def test_search(self, mock_get):
        """Test searching for a symbol."""
        # Mock the API response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"symbol": "AAPL", "name": "Apple Inc.", "currency": "USD", "stockExchange": "NASDAQ", "exchangeShortName": "NASDAQ"}
        ]
        mock_get.return_value = mock_response

        # Call the search function
        result = fmp.search("Apple")

        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["symbol"], "AAPL")
        self.assertEqual(result[0]["name"], "Apple Inc.")

    @mock.patch('fins.fmp.requests.get')
    def test_profile(self, mock_get):
        """Test getting a company profile."""
        # Mock the API response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "symbol": "AAPL",
                "price": 150.0,
                "beta": 1.2,
                "volAvg": 30000000,
                "mktCap": 2500000000000,
                "lastDiv": 0.82,
                "range": "120.0-150.0",
                "changes": 0.5,
                "companyName": "Apple Inc.",
                "currency": "USD",
                "cik": "0000320193",
                "isin": "US0378331005",
                "cusip": "037833100",
                "exchange": "NASDAQ",
                "exchangeShortName": "NASDAQ",
                "industry": "Consumer Electronics",
                "website": "https://www.apple.com",
                "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.",
                "ceo": "Timothy Cook",
                "sector": "Technology",
                "country": "US",
                "fullTimeEmployees": 147000,
                "phone": "408-996-1010",
                "address": "One Apple Park Way",
                "city": "Cupertino",
                "state": "CA",
                "zip": "95014",
                "dcfDiff": 0.05,
                "dcf": 160.0,
                "image": "https://financialmodelingprep.com/image-stock/AAPL.png",
                "ipoDate": "1980-12-12",
                "defaultImage": False,
                "isEtf": False,
                "isActivelyTrading": True,
                "isAdr": False,
                "isFund": False
            }
        ]
        mock_get.return_value = mock_response

        # Call the profile function
        result = fmp.profile("AAPL")

        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["symbol"], "AAPL")
        self.assertEqual(result[0]["companyName"], "Apple Inc.")
        self.assertEqual(result[0]["sector"], "Technology")

    @mock.patch('fins.fmp.requests.get')
    def test_quote(self, mock_get):
        """Test getting a stock quote."""
        # Mock the API response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "price": 150.0,
                "changesPercentage": 0.5,
                "change": 0.75,
                "dayLow": 149.0,
                "dayHigh": 151.0,
                "yearHigh": 155.0,
                "yearLow": 120.0,
                "marketCap": 2500000000000,
                "priceAvg50": 148.0,
                "priceAvg200": 145.0,
                "volume": 30000000,
                "avgVolume": 35000000,
                "exchange": "NASDAQ",
                "open": 149.5,
                "previousClose": 149.25,
                "eps": 5.0,
                "pe": 30.0,
                "earningsAnnouncement": "2023-04-28T00:00:00.000Z",
                "sharesOutstanding": 16000000000,
                "timestamp": 1617300000000
            }
        ]
        mock_get.return_value = mock_response

        # Call the quote function
        result = fmp.quote("AAPL")

        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["symbol"], "AAPL")
        self.assertEqual(result[0]["price"], 150.0)
        self.assertEqual(result[0]["marketCap"], 2500000000000)

    @mock.patch('fins.fmp.api_get')
    def test_load_ticker_fundamentals(self, mock_api_get):
        """Test loading ticker fundamentals."""
        # Mock the API response
        mock_api_get.return_value = [
            {
                "symbol": "AAPL",
                "price": 150.0,
                "beta": 1.2,
                "volAvg": 30000000,
                "mktCap": 2500000000000,
                "companyName": "Apple Inc.",
                "sector": "Technology",
                "industry": "Consumer Electronics"
            }
        ]

        # Call the load_ticker_fundamentals function
        result = fmp.load_ticker_fundamentals("AAPL")

        # Verify the result
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape[0], 1)
        self.assertEqual(result.iloc[0]["symbol"], "AAPL")
        self.assertEqual(result.iloc[0]["companyName"], "Apple Inc.")
        self.assertEqual(result.iloc[0]["sector"], "Technology")

    @mock.patch('fins.fmp.api_get')
    @mock.patch('pandas.read_pickle')
    @mock.patch('pandas.DataFrame.to_pickle')
    @mock.patch('os.path.exists')
    def test_load_ticker_history(self, mock_exists, mock_to_pickle, mock_read_pickle, mock_api_get):
        """Test loading ticker history."""
        # Mock the cache check
        mock_exists.return_value = False

        # Mock the API response
        mock_api_get.return_value = {
            "symbol": "AAPL",
            "historical": [
                {"date": "2023-01-03", "adjClose": 125.0},
                {"date": "2023-01-04", "adjClose": 126.0},
                {"date": "2023-01-05", "adjClose": 127.0}
            ]
        }

        # Call the load_ticker_history function
        result = fmp.load_ticker_history("AAPL")

        # Verify the API was called with the correct parameters
        # No parameters expected now that we're fetching full history
        mock_api_get.assert_called_once_with("historical-price-full/AAPL", {})
        
        # Verify the result has the expected structure
        self.assertIn("close", result.columns)
        self.assertEqual(len(result), 3)
        
        # Verify the prices are not normalized (actual prices are used)
        self.assertEqual(result.iloc[0]["close"], 125.0)


if __name__ == "__main__":
    unittest.main() 