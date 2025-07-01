"""
Name Column
"""
from typing import Optional

from .. import BasketItem
from ..plugin_field import FieldPlugin


class Name(FieldPlugin):
    """ Add 'Name' field """

    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        if alias is None:
            alias = 'Name'
        super().__init__(alias=alias)

    def field_types(self):
        return [("", str)]

    def field_values(self, item: BasketItem):
        return [item.symbol().name]


