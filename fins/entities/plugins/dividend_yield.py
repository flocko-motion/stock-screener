"""
Dividend Yield Column
"""

from typing import Optional

from .. import BasketItem
from ..plugin import FieldPlugin


class DividendYield(FieldPlugin):
    """ Add 'Dividend Yield' field """

    def __init__(self, alias: Optional[str] = None):
        if alias is None:
            alias = 'DividendYield'
        super().__init__(alias=alias)

    def field_type(self) -> type:
        return float

    def field_value(self, item: BasketItem):
        return item.symbol().get_analytics("dividend_yield_ttm")

