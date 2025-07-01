"""
Last Update Column
"""
from datetime import datetime
from typing import Optional

from .. import BasketItem
from ..plugin_field import FieldPlugin


class LastUpdate(FieldPlugin):
    """ Add 'Last Update' field(s) """

    def __init__(self, combined: bool = True, alias: Optional[str] = None):
        self._register_call_args(combined=combined, alias=alias)
        self.combined = combined
        if alias is None:
            alias = 'LastUpdate'
        super().__init__(alias=alias)

    def field_types(self):
        if self.combined:
            return [("", Optional[datetime])]
        else:
            return [("Price", Optional[datetime]), ("Profile", Optional[datetime])]

    def field_values(self, item: BasketItem):
        s = item.symbol()
        if self.combined:
            if s.last_price_update is None or s.last_profile_update is None:
                return [None]
            return [min(s.last_price_update, s.last_profile_update)]
        else:
            return [s.last_price_update, s.last_profile_update]


