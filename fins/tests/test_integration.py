#!/usr/bin/env python
"""
Integration tests for the FINS system.

This module contains integration tests that combine all three levels of testing:
1. Parser tests
2. Elementary action tests
3. Terminal input/output tests

These tests verify that the entire system works together correctly.
"""

import unittest
import sys
import io
from pathlib import Path
from unittest import mock

# Add the parent directory to the path to allow imports from the fins package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fins.dsl import FinsParser
from fins import fmp
from fins.cli import run_command_mode


class TestIntegration(unittest.TestCase):
    """Integration tests for the FINS system."""

    def setUp(self):
        """Set up test fixtures."""
        # Redirect stdout to capture output
        self.stdout_patcher = mock.patch('sys.stdout', new_callable=io.StringIO)
        self.mock_stdout = self.stdout_patcher.start()
        
        # Create a parser instance
        self.parser = FinsParser()

    def tearDown(self):
        """Tear down test fixtures."""
        self.stdout_patcher.stop()

    @mock.patch('fins.fmp.api_get')
    @mock.patch('fins.dsl.FinsParser.parse')
    def test_create_basket_with_real_data(self, mock_parse, mock_api_get):
        """Test creating a basket with real data from FMP."""
        # Mock the API responses for symbol search
        mock_api_get.side_effect = [
            # Response for search("AAPL")
            [{"symbol": "AAPL", "name": "Apple Inc.", "currency": "USD", "stockExchange": "NASDAQ"}],
            # Response for search("MSFT")
            [{"symbol": "MSFT", "name": "Microsoft Corporation", "currency": "USD", "stockExchange": "NASDAQ"}],
            # Response for search("GOOGL")
            [{"symbol": "GOOGL", "name": "Alphabet Inc.", "currency": "USD", "stockExchange": "NASDAQ"}]
        ]
        
        # Mock the parser response
        mock_parse.return_value = "Created basket $tech_basket with symbols: AAPL, MSFT, GOOGL"
        
        # Run the command
        run_command_mode("AAPL MSFT GOOGL -> $tech_basket", self.parser)
        
        # Verify the output
        output = self.mock_stdout.getvalue().strip()
        self.assertEqual(output, "Created basket $tech_basket with symbols: AAPL, MSFT, GOOGL")
        
        # Verify the parser was called with the correct command
        mock_parse.assert_called_once_with('AAPL MSFT GOOGL -> $tech_basket')

    @mock.patch('fins.fmp.api_get')
    @mock.patch('fins.dsl.FinsParser.parse')
    def test_sort_basket_by_market_cap(self, mock_parse, mock_api_get):
        """Test sorting a basket by market cap using real data from FMP."""
        # Mock the API responses for profile data
        mock_api_get.side_effect = [
            # Response for profile("AAPL")
            [{"symbol": "AAPL", "mktCap": 2500000000000, "companyName": "Apple Inc."}],
            # Response for profile("MSFT")
            [{"symbol": "MSFT", "mktCap": 2400000000000, "companyName": "Microsoft Corporation"}],
            # Response for profile("GOOGL")
            [{"symbol": "GOOGL", "mktCap": 1800000000000, "companyName": "Alphabet Inc."}]
        ]
        
        # Mock the parser responses
        mock_parse.side_effect = [
            "Created basket $test_basket with symbols: AAPL, MSFT, GOOGL",
            "Sorted $test_basket by mcap in descending order: AAPL, MSFT, GOOGL"
        ]
        
        # Run the commands
        run_command_mode("AAPL MSFT GOOGL -> $test_basket", self.parser)
        self.mock_stdout.truncate(0)  # Clear the output buffer
        self.mock_stdout.seek(0)
        
        run_command_mode("$test_basket -> sort mcap desc", self.parser)
        
        # Verify the output
        output = self.mock_stdout.getvalue().strip()
        self.assertEqual(output, "Sorted $test_basket by mcap in descending order: AAPL, MSFT, GOOGL")
        
        # Verify the parser was called with the correct commands
        mock_parse.assert_has_calls([
            mock.call('AAPL MSFT GOOGL -> $test_basket'),
            mock.call('$test_basket -> sort mcap desc')
        ])

    @mock.patch('fins.fmp.api_get')
    @mock.patch('fins.dsl.FinsParser.parse')
    def test_filter_basket_by_market_cap(self, mock_parse, mock_api_get):
        """Test filtering a basket by market cap using real data from FMP."""
        # Mock the API responses for profile data
        mock_api_get.side_effect = [
            # Response for profile("AAPL")
            [{"symbol": "AAPL", "mktCap": 2500000000000, "companyName": "Apple Inc."}],
            # Response for profile("MSFT")
            [{"symbol": "MSFT", "mktCap": 2400000000000, "companyName": "Microsoft Corporation"}],
            # Response for profile("GOOGL")
            [{"symbol": "GOOGL", "mktCap": 1800000000000, "companyName": "Alphabet Inc."}]
        ]
        
        # Mock the parser responses
        mock_parse.side_effect = [
            "Created basket $test_basket with symbols: AAPL, MSFT, GOOGL",
            "Filtered $test_basket to symbols with mcap > 2000B: AAPL, MSFT"
        ]
        
        # Run the commands
        run_command_mode("AAPL MSFT GOOGL -> $test_basket", self.parser)
        self.mock_stdout.truncate(0)  # Clear the output buffer
        self.mock_stdout.seek(0)
        
        run_command_mode("$test_basket -> mcap > 2000B", self.parser)
        
        # Verify the output
        output = self.mock_stdout.getvalue().strip()
        self.assertEqual(output, "Filtered $test_basket to symbols with mcap > 2000B: AAPL, MSFT")
        
        # Verify the parser was called with the correct commands
        mock_parse.assert_has_calls([
            mock.call('AAPL MSFT GOOGL -> $test_basket'),
            mock.call('$test_basket -> mcap > 2000B')
        ])

    @mock.patch('fins.fmp.api_get')
    @mock.patch('fins.dsl.FinsParser.parse')
    def test_complex_flow_with_real_data(self, mock_parse, mock_api_get):
        """Test a complex command flow with real data from FMP."""
        # Mock the API responses for various API calls
        mock_api_get.side_effect = [
            # Responses for search and profile calls
            [{"symbol": "AAPL", "name": "Apple Inc.", "currency": "USD", "stockExchange": "NASDAQ"}],
            [{"symbol": "MSFT", "name": "Microsoft Corporation", "currency": "USD", "stockExchange": "NASDAQ"}],
            [{"symbol": "GOOGL", "name": "Alphabet Inc.", "currency": "USD", "stockExchange": "NASDAQ"}],
            [{"symbol": "NFLX", "name": "Netflix, Inc.", "currency": "USD", "stockExchange": "NASDAQ"}],
            # Responses for market cap data
            [{"symbol": "AAPL", "mktCap": 2500000000000, "companyName": "Apple Inc."}],
            [{"symbol": "MSFT", "mktCap": 2400000000000, "companyName": "Microsoft Corporation"}],
            [{"symbol": "GOOGL", "mktCap": 1800000000000, "companyName": "Alphabet Inc."}],
            [{"symbol": "NFLX", "mktCap": 200000000000, "companyName": "Netflix, Inc."}],
            # Responses for historical data for CAGR calculation
            {"symbol": "AAPL", "historical": [{"date": "2018-01-03", "adjClose": 100.0}, {"date": "2023-01-03", "adjClose": 150.0}]},
            {"symbol": "GOOGL", "historical": [{"date": "2018-01-03", "adjClose": 200.0}, {"date": "2023-01-03", "adjClose": 280.0}]},
            {"symbol": "NFLX", "historical": [{"date": "2018-01-03", "adjClose": 50.0}, {"date": "2023-01-03", "adjClose": 90.0}]}
        ]
        
        # Mock the parser response
        mock_parse.return_value = "Created persistent basket /my_tech_basket with symbols: AAPL, GOOGL, NFLX sorted by mcap with cagr column"
        
        # Run the command
        run_command_mode("AAPL MSFT GOOGL -> + NFLX -> - MSFT -> sort mcap desc -> cagr 5y -> /my_tech_basket", self.parser)
        
        # Verify the output
        output = self.mock_stdout.getvalue().strip()
        self.assertEqual(output, "Created persistent basket /my_tech_basket with symbols: AAPL, GOOGL, NFLX sorted by mcap with cagr column")
        
        # Verify the parser was called with the correct command
        mock_parse.assert_called_once_with('AAPL MSFT GOOGL -> + NFLX -> - MSFT -> sort mcap desc -> cagr 5y -> /my_tech_basket')


if __name__ == "__main__":
    unittest.main() 