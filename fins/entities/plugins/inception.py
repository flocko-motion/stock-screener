"""
Inception Date Column
"""
from typing import Optional
from datetime import datetime

from .. import BasketItem
from ..plugin_field import FieldPlugin
import pandas as pd


class Inception(FieldPlugin):
    """ Add 'Inception' field """

    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        if alias is None:
            alias = 'Inception'
        super().__init__(alias=alias)

    def field_types(self):
        return [("", Optional[datetime])]

    def field_values(self, item: BasketItem, data: dict[str, pd.DataFrame]):
        return [item.symbol().inception] 