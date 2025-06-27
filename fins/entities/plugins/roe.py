"""
Return On Equity Column
"""

from typing import Optional

from .. import BasketItem
from ..plugin import FieldPlugin


class Roe(FieldPlugin):
    """ Add 'Return on Equity' field """

    def __init__(self, alias: Optional[str] = None):
        if alias is None:
            alias = 'ROE'
        super().__init__(alias=alias)

    def field_type(self) -> type:
        return float

    def field_value(self, item: BasketItem):
        return item.symbol().get_analytics("return_on_equity_ttm")
