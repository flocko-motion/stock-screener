"""
Market Cap Column
"""

from typing import Optional
from ..column import Column
from . import Symbol

class McapColumn(Column):
    def __init__(self, alias: str = None):
        super().__init__(alias=alias)

    def value(self, ticker: str) -> Optional[float]:
        return Symbol.get(ticker).get_analytics("market_cap")

    def value_str(self, ticker: str) -> str:
        v = self.value(ticker)
        return "n/a" if v is None else  f"{int(v)}"
