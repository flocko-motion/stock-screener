"""
Market Cap Column
"""

from typing import Optional

from .. import BasketItem
from ..plugin import Plugin


class Industry(Plugin):
    """ Add 'Industry' field """

    def __init__(self, alias: Optional[str] = None):
        super().__init__(alias=alias)

    def value(self, item: BasketItem) -> Optional[float] | str:
        return item.symbol().industry

    def run(self, basket):
        pass

