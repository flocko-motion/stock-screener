from typing import Optional

from .. import BasketItem
from ..plugin import FieldPlugin, SeriesPlugin
from ...financial import Symbol

class Price(SeriesPlugin):
    def __init__(self, alias: Optional[str] = None, ticker: Optional[str] = None, resolution: str = "m", metric: str = "close"):
        if alias is None:
            alias = (ticker or "") + ("Weekly" if resolution == "w" else "Monthly") + metric.capitalize()
        super().__init__(alias=alias)
        self._ticker = ticker
        self._resolution = resolution
        self._metric = metric

    def field_value(self, item: BasketItem):
        symbol = item.symbol() if self._ticker is None else Symbol.get(self._ticker)
        df = symbol.get_weekly() if self._resolution == "w" else symbol.get_monthly()
        res = df[[self._metric]].reset_index()
        res.attrs['type'] = "index"
        return res

class WeeklyClose(Price):
    """ Add 'WeeklyClose' series """

    def __init__(self, alias: Optional[str] = None, ticker: Optional[str] = None):
        super().__init__(alias=alias, ticker=ticker, resolution="w", metric="close")


class MonthlyClose(Price):
    """ Add 'MonthlyClose' series """
    def __init__(self, alias: Optional[str] = None,    ticker: Optional[str] = None):
        super().__init__(alias=alias, ticker=ticker, resolution="m", metric="close")


