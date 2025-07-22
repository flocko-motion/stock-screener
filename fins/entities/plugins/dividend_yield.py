"""
Dividend Yield Column
"""

from typing import Optional

from .. import BasketItem
from ..plugin_field import FieldPlugin
import pandas as pd


class DivYield(FieldPlugin):
    """ Add 'Dividend Yield' field """

    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        if alias is None:
            alias = 'DivYield'
        super().__init__(alias=alias)

    def field_types(self):
        return [("", float)]

    def field_values(self, item: BasketItem, data: dict[str, pd.DataFrame]):
        return [item.symbol().get_analytics("dividend_yield_ttm")]

