"""
PE (Price/Earnings) Column
"""

from typing import Optional

from .. import BasketItem
from ..plugin import FieldPlugin


class Pe(FieldPlugin):
    """ Add 'P/E Ratio' field """

    def __init__(self, alias: Optional[str] = None):
        if alias is None:
            alias = 'PE'
        super().__init__(alias=alias)

    def field_type(self) -> type:
        return float

    def field_value(self, item: BasketItem):
        return item.symbol().get_analytics("pe_ratio_ttm")
