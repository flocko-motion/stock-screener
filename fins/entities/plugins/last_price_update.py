"""
Last Price Update Column
"""
from datetime import datetime
from typing import Optional

from .. import BasketItem
from ..plugin_field import FieldPlugin


class LastUpdatePrice(FieldPlugin):
    """ Add 'Last Price Update' field """

    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        if alias is None:
            alias = 'LastPriceUpdate'
        super().__init__(alias=alias)

    def field_types(self):
        return [("", Optional[datetime])]

    def field_values(self, item: BasketItem):
        return [item.symbol().last_price_update]


