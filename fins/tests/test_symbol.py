"""
Tests for BasketItem operations.
"""

import unittest
from fins.financial.symbol import Symbol
import fins.financial.symbol as symbol


class SymbolTests(unittest.TestCase):
    """Tests for BasketItem operations."""

    def test_get_stock(self):
        s = Symbol.get("AAPL")
        assert s.ticker == "AAPL"
        assert s.name == 'Apple Inc.'
        assert s.country == 'US'
        assert s.currency == 'USD'
        assert s.description.startswith('Apple Inc. designs, manufactures, and')
        assert s.exchange == 'NASDAQ'
        assert s.industry == 'Consumer Electronics'
        assert s.isin == 'US0378331005'
        assert s.sector == 'Technology'
        assert s.type == symbol.TYPE_STOCK
        assert s.website == 'https://www.apple.com'
        pass

    def test_get_etf(self):
        s = Symbol.get("SPY")
        assert s.ticker == "SPY"
        assert s.name == "SPDR S&P 500 ETF Trust"
        assert s.country == "US"
        assert s.currency == "USD"
        assert s.description.startswith('The Trust seeks to achieve its investment objective')
        assert s.exchange == "AMEX"
        assert s.industry == "Asset Management"
        assert s.isin == "US78462F1030"
        assert s.sector == "Financial Services"
        assert s.type == symbol.TYPE_ETF

    def test_get_crypto(self):
        s = Symbol.get("ADAUSD")
        assert s.ticker == "ADAUSD"
        assert s.name == "Cardano USD"
        assert s.country == None
        assert s.currency == "USD"
        assert s.description == None
        assert s.exchange == "CRYPTO"
        assert s.industry == None
        assert s.isin == None
        assert s.sector == None
        assert s.type == symbol.TYPE_CRYPTO

    def test_stock_cagr(self):
        s = Symbol.get("AAPL")
        cagr_5 = s.get_cagr(5)
        assert cagr_5 > 0.1


if __name__ == "__main__":
    unittest.main() 