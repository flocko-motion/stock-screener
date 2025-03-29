"""
PE (Price/Earnings) Column
"""

from typing import Literal, Optional
from ..column import Column
from . import Symbol


class PeColumn(Column):
    """Price/Earnings ratio column."""

    def __init__(self, mode: Literal["ttm", "forward"] = "ttm"):
        """
        Initialize PE column.
        
        Args:
            mode: Use trailing twelve months ("ttm") or forward ("forward") EPS
        """
        super().__init__()
        self.mode = mode

    def value(self, ticker: str) -> Optional[float]:
        """Get P/E ratio for a ticker."""
        symbol = Symbol.get(ticker)
        
        price = symbol.price
        eps = symbol.get_data('ttm_eps') if self.mode == "ttm" else symbol.get_data('forward_eps')
        
        if price is None or eps is None or eps == 0:
            return None
            
        return price / eps