"""
Volatility Column
"""

from typing import Optional

from .. import BasketItem
from ..plugin_field import FieldPlugin


class Vol(FieldPlugin):
    """ Add 'Volatility' field """

    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        if alias is None:
            alias = 'Vol'
        super().__init__(alias=alias)

    def field_types(self):
        return [("", float)]

    def field_values(self, item: BasketItem):
        return [item.symbol().get_analytics("52_week_volatility")]
