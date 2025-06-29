"""
Market Cap Column
"""

from typing import Optional

from .. import BasketItem
from ..plugin import FieldPlugin


class Mcap(FieldPlugin):
    """ Add 'Market Cap' field """

    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        if alias is None:
            alias = 'MCap'
        super().__init__(alias=alias)

    def field_type(self) -> type:
        return float

    def field_value(self, item: BasketItem):
        return item.symbol().get_analytics("market_cap")
