from typing import Optional, List, Any

import pandas as pd

from fins.entities import BasketRuntime, BasketItem
from fins.entities.plugin_field import FieldPlugin
from fins.financial import Symbol


class OutputPlugin(FieldPlugin):

    def __init__(self, alias: Optional[str] = None):
        super().__init__(alias)
        self.subfields_amount = 0

    def field_values(self, item: BasketItem, output_data) -> List[Any]:
        res = self.output_item(item.symbol(),  output_data)
        return res

    def output_item(self, symbol: Symbol, data: dict[str, pd.DataFrame]) -> List:
        """ process a single item and return a list of outputs (e.g. plots) """
        pass

    def output_all(self, data: 'OutputData') -> List[List]:
        """ runner is NOT IMPLEMENTED: process all items at once and return an outer list per plot containing an inner list with a plot per item"""
        pass


class OutputData:

    def __init__(self):
        self._series = list[str]()
        self._items = dict[int, dict[str, pd.DataFrame]]()

    def register_series(self, field_name: str):
        self._series.append(field_name)

    def items(self) -> dict[int, dict[str, pd.DataFrame]]:
        return self._items

    def item_series(self, row_index: int) -> dict[str, pd.DataFrame]:
        if row_index >= len(self._series):
            return {}
        return self._items[row_index]

    def set_series(self, row_index: int, field_name: str, value: pd.DataFrame):
        if row_index not in self._items:
            self._items[row_index] = dict[str, pd.DataFrame]()
        self._items[row_index][field_name] = value
