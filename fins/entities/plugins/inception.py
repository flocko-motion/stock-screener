from typing import Optional
from datetime import datetime

from .. import BasketItem
from ..plugin import FieldPlugin


class Inception(FieldPlugin):
    """ Add 'Inception Date' field """

    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        if alias is None:
            alias = 'Inception'
        super().__init__(alias=alias)

    def field_type(self) -> type:
        return Optional[datetime]

    def field_value(self, item: BasketItem):
        return item.symbol().inception 