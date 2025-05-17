"""
Compound Annual Growth Rate Column
"""

from typing import Optional
from ..column import Column
from . import Symbol

class CagrColumn(Column):
    def __init__(self, alias: str = None, years: str = None):
        super().__init__(alias=alias)
        self.years = int(years) if years else None

    def value(self, ticker: str) -> Optional[float]:
        # TODO: implement
        return 0
