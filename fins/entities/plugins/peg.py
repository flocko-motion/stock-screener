"""
PEG Ratio Column  
"""
from typing import Optional

import pandas as pd

from .. import BasketItem
from ..plugin_field import FieldPlugin


class Peg(FieldPlugin):
    """ Add 'PEG Ratio' field """

    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        if alias is None:
            alias = 'PEG'
        super().__init__(alias=alias)

    def field_types(self):
        return [("", float)]

    def field_values(self, item: BasketItem, data: dict[str, pd.DataFrame]):
        return [item.symbol().get_analytics("peg_ratio_ttm")]
