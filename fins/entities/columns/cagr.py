"""
Compound Annual Growth Rate Column
"""

from typing import Optional
from ..column import Column
from ...financial import Symbol


class CagrColumn(Column):
    @classmethod
    def name(cls) -> str:
        return "cagr"

    @classmethod
    def description(cls) -> str:
        return "Compound Annual Growth Rate"

    def __init__(self, alias: str = None, years: int = 5):
        super().__init__(alias=alias)
        self.years = int(years) if years else None

    def value(self, ticker: str) -> Optional[float]:
        return Symbol.get(ticker).get_cagr(years=self.years)

    def value_str(self, ticker: str) -> str:
        v = self.value(ticker)
        return "n/a" if v is None else  f"{v:.4f}"
