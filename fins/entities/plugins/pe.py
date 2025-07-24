"""
PE (Price/Earnings) Column
"""

from typing import Optional

from .. import BasketItem
from ..plugin_field import FieldPlugin
import pandas as pd


class Pe(FieldPlugin):
    """ Add 'P/E Ratio' field """

    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        if alias is None:
            alias = 'PE'
        super().__init__(alias=alias)

    def field_types(self):
        return [("", Optional[float])]

    def field_values(self, item: BasketItem, data: dict[str, pd.DataFrame]):
        return [item.symbol().get_analytics("pe_ratio_ttm")]
