"""
Net Profit Margin Column
"""

from typing import Optional

from .. import BasketItem
from ..plugin_field import FieldPlugin
import pandas as pd


class Npm(FieldPlugin):
    """ Add 'Net Profit Margin' field """

    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        if alias is None:
            alias = 'NPM'
        super().__init__(alias=alias)

    def field_types(self):
        return [("", float)]

    def field_values(self, item: BasketItem, data: dict[str, pd.DataFrame]):
        return [item.symbol().get_analytics("net_profit_margin_ttm")]
