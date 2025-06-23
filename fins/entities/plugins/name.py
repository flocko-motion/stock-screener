"""
Market Cap Column
"""

from typing import Optional

from .. import Plugin
from ...financial import Symbol


class NameColumn(Plugin):
    @classmethod
    def name(cls) -> str:
        return "name"

    @classmethod
    def description(cls) -> str:
        return "Name"

    def __init__(self, alias: str = None):
        super().__init__(alias=alias)

    def value(self, ticker: str) -> Optional[float]:
        raise NotImplementedError()

    def value_str(self, ticker: str) -> str:
        return Symbol.get(ticker).name
