"""
Market Cap Column
"""

from typing import Optional
from ..column import Column
from ...financial import Symbol


class SectorColumn(Column):
    @classmethod
    def name(cls) -> str:
        return "sector"

    @classmethod
    def description(cls) -> str:
        return "sector"

    def __init__(self, alias: str = None):
        super().__init__(alias=alias)

    def value(self, ticker: str) -> Optional[float]:
        raise NotImplementedError()

    def value_str(self, ticker: str) -> str:
        return Symbol.get(ticker).sector
