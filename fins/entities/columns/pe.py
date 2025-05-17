"""
PE (Price/Earnings) Column
"""

from typing import Literal, Optional
from ..column import Column
from . import Symbol


class PeColumn(Column):
    def __init__(self, alias: str = None):
        super().__init__(alias=alias)

    def value(self, ticker: str) -> Optional[float]:
        return Symbol.get(ticker).get_analytics("pe_ratio_ttm")
