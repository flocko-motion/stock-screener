"""
Net Profit Margin Column
"""

from typing import Optional

from .. import BasketItem
from ..plugin import FieldPlugin


class Npm(FieldPlugin):
    """ Add 'Net Profit Margin' field """

    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        if alias is None:
            alias = 'NPM'
        super().__init__(alias=alias)

    def field_type(self) -> type:
        return float

    def field_value(self, item: BasketItem):
        return item.symbol().get_analytics("net_profit_margin_ttm")
