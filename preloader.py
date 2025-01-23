"""
Run this script to preload the data for all caches and calculate the financial metrics for all tickers.
"""

from lib import Ticker

Ticker.load_all_data()