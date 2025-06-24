from datetime import datetime
from typing import Optional

from .. import BasketItem
from ..plugin import FieldPlugin


class LastPriceUpdate(FieldPlugin):
    """ Add 'LastPriceUpdate' field """

    def __init__(self, alias: Optional[str] = None):
        super().__init__(alias=alias)

    def field_type(self) -> type:
        return Optional[datetime]

    def field_value(self, item: BasketItem):
        return item.symbol().last_price_update


