"""
Net Profit Margin Column
"""

from typing import Optional
from ..column import Column
from ...financial import Symbol


class NpmColumn(Column):
    @classmethod
    def name(cls) -> str:
        return "npm"

    @classmethod
    def description(cls) -> str:
        return "Net Profit Margin"

    def __init__(self, alias: str = None):
        super().__init__(alias=alias)

    def value(self, ticker: str) -> Optional[float]:
        return Symbol.get(ticker).get_analytics("net_profit_margin_ttm")

    def value_str(self, ticker: str) -> str:
        v = self.value(ticker)
        return "n/a" if v is None else  f"{v:.4f}"
