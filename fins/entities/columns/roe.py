"""
Return On Equity Column
"""

from typing import Optional
from ..column import Column
from . import Symbol

class RoeColumn(Column):
    def __init__(self):
        super().__init__()

    def value(self, ticker: str) -> Optional[float]:
        return Symbol.get(ticker).get_analytics("return_on_equity_ttm")
