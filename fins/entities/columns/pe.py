"""
PE (Price/Earnings) Column
"""

from typing import Optional
from ..column import Column
from ...financial import Symbol


class PeColumn(Column):
    @classmethod
    def name(cls) -> str:
        return "pe"

    @classmethod
    def description(cls) -> str:
        return "Price/Earnings ratio (TTM)"

    def __init__(self, alias: str = None):
        super().__init__(alias=alias)

    def value(self, ticker: str) -> Optional[float]:
        return Symbol.get(ticker).get_analytics("pe_ratio_ttm")

    def value_str(self, ticker: str) -> str:
        v = self.value(ticker)
        return "n/a" if v is None else  f"{int(v)}"
