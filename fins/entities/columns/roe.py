"""
Return On Equity Column
"""

from typing import Optional
from ..column import Column
from ...financial import Symbol


class RoeColumn(Column):
    @classmethod
    def name(cls) -> str:
        return "roe"

    @classmethod
    def description(cls) -> str:
        return "Return on Equity"

    def __init__(self, alias: str = None):
        super().__init__(alias=alias)

    def value(self, ticker: str) -> Optional[float]:
        return Symbol.get(ticker).get_analytics("return_on_equity_ttm")

    def value_str(self, ticker: str) -> str:
        v = self.value(ticker)
        return "n/a" if v is None else  f"{v:.4f}"
