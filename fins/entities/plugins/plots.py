from typing import Optional

import pandas as pd

from .. import BasketItem
from ..plugin import FieldPlugin, SeriesPlugin, Plugin, OutputPlugin, OutputData
from ...financial import Symbol

class PlotItems(OutputPlugin):
    def __init__(self, alias: Optional[str] = None):
        super().__init__(alias=alias)

    def output_item(self, data: dict[str, pd.DataFrame]):
        print(data)


class PlotAll(OutputPlugin):
    def __init__(self, alias: Optional[str] = None):
        super().__init__(alias=alias)


    def output_all(self, data: 'OutputData'):
        print(data)

