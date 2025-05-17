"""
Net Profit Margin Column
"""

from typing import Optional
from ..column import Column
from . import Symbol

class NpmColumn(Column):
    def __init__(self, alias: str = None):
        super().__init__(alias=alias)

    def value(self, ticker: str) -> Optional[float]:
        return Symbol.get(ticker).get_analytics("net_profit_margin_ttm")
