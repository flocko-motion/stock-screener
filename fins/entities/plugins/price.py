from typing import Optional

from .. import BasketItem
from ..plugin import FieldPlugin, SeriesPlugin
from ...financial import Symbol

class Price(SeriesPlugin):
    def __init__(self, alias: Optional[str] = None, ticker: Optional[str] = None, resolution: str = "m", metric: str = "close"):
        self._resolution = resolution
        self._metric = metric
        if alias is None:
            alias = (ticker or "") + self.resolution_name() + self.metric_name()
        super().__init__(alias=alias)
        self._ticker = ticker


    def field_value(self, item: BasketItem):
        symbol = item.symbol() if self._ticker is None else Symbol.get(self._ticker)
        df = symbol.get_weekly() if self._resolution == "w" else symbol.get_monthly()
        
        res = df[['date', self._metric]]
        res.attrs['type'] = "index"
        res.attrs['title'] = symbol.ticker + " " + self.resolution_name() + " " + self.metric_name()
        return res

    def resolution_name(self):
        return "Weekly" if self._resolution == "w" else "Monthly"

    def metric_name(self):
        return self._metric.capitalize()

class WeeklyClose(Price):
    """ Add 'WeeklyClose' series """

    def __init__(self, alias: Optional[str] = None, ticker: Optional[str] = None):
        super().__init__(alias=alias, ticker=ticker, resolution="w", metric="close")


class MonthlyClose(Price):
    """ Add 'MonthlyClose' series """
    def __init__(self, alias: Optional[str] = None,    ticker: Optional[str] = None):
        super().__init__(alias=alias, ticker=ticker, resolution="m", metric="close")


