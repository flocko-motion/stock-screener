from typing import Optional

from .. import BasketItem
from ..plugin import FieldPlugin


class Name(FieldPlugin):
    """ Add 'Name' field """

    def __init__(self, alias: Optional[str] = None):
        super().__init__(alias=alias)

    def field_type(self) -> type:
        return str

    def field_value(self, item: BasketItem):
        return item.symbol().name


