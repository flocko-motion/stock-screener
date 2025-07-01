"""
Last Update Column
"""
from datetime import datetime
from typing import Optional

from .. import BasketItem
from ..plugin_field import FieldPlugin


class LastUpdate(FieldPlugin):
    """ Add 'Last Update' field """

    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        if alias is None:
            alias = 'LastUpdate'
        super().__init__(alias=alias)

    def field_types(self):
        return [("", Optional[datetime])]

    def field_values(self, item: BasketItem):
        s = item.symbol()
        if s.last_price_update is None or s.last_profile_update is None:
            return [None]
        return [min(s.last_price_update, s.last_profile_update)]


