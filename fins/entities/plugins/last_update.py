from datetime import datetime
from typing import Optional

from .. import BasketItem
from ..plugin import FieldPlugin


class LastUpdate(FieldPlugin):
    """ Add 'LastUpdate' field """

    def __init__(self, alias: Optional[str] = None):
        super().__init__(alias=alias)

    def field_type(self) -> type:
        return Optional[datetime]

    def field_value(self, item: BasketItem):
        s = item.symbol()
        if s.last_price_update is None or s.last_profile_update is None:
            return None
        return min(s.last_price_update, s.last_profile_update)


