from typing import Optional

from .. import BasketItem
from ..plugin import FieldPlugin


class Sector(FieldPlugin):
    """ Add 'Sector' field """

    def __init__(self, alias: Optional[str] = None):
        super().__init__(alias=alias)

    def field_type(self) -> type:
        return Optional[str]

    def field_value(self, item: BasketItem):
        return item.symbol().sector
