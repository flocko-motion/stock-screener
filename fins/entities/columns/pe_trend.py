"""
PE Trend Indicator Column
"""

from typing import Optional
from ..column import Column
from . import Symbol


class PeTrendColumn(Column):
    """Normalized PE trend indicator [-1, +1]."""

    def value(self, ticker: str) -> Optional[float]:
        """Get normalized PE trend for a ticker.
        
        Returns:
            -1: Strong positive earnings trend (forward PE much lower than TTM)
             0: Stable earnings (forward PE equals TTM)
            +1: Strong negative earnings trend (forward PE much higher than TTM)
        """
        symbol = Symbol.get(ticker)
        
        price = symbol.price
        ttm_eps = symbol.get_data('ttm_eps')
        forward_eps = symbol.get_data('forward_eps')
        
        if price is None or ttm_eps is None or forward_eps is None or ttm_eps == 0 or forward_eps == 0:
            return None
            
        ttm_pe = price / ttm_eps
        forward_pe = price / forward_eps
        
        return (forward_pe - ttm_pe) / (forward_pe + ttm_pe) 