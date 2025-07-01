"""
Industry Column  
"""
from typing import Optional

from .. import BasketItem
from ..plugin_field import FieldPlugin


class Industry(FieldPlugin):
    """ Add 'Industry' field """

    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        if alias is None:
            alias = 'Industry'
        super().__init__(alias=alias)

    def field_types(self):
        return [("", Optional[str])]

    def field_values(self, item: BasketItem):
        return [item.symbol().industry]


