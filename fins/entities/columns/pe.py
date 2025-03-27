"""
PE (Price/Earnings) Column
"""

from typing import Literal, Optional
from ..column import Column
from ...financial import get_symbol


class PeColumn(Column):
    """Price/Earnings ratio column."""

    def __init__(self, mode: Literal["ttm", "forward"] = "ttm"):
        """
        Args:
            mode: Use trailing twelve months ("ttm") or forward ("forward") EPS
        """
        self.mode = mode

    def value(self, ticker: str) -> Optional[float]:
        """Get P/E ratio for a ticker."""
        symbol = get_symbol(ticker)
        
        price = symbol.price
        eps = symbol.ttm_eps if self.mode == "ttm" else symbol.forward_eps
        
        if price is None or eps is None or eps == 0:
            return None
            
        return price / eps 