"""
Compound Annual Growth Rate Column
"""

from typing import Optional
import pandas as pd
from ..column import Column
from ...financial import Symbol


class CagrColumn(Column):
    @classmethod
    def name(cls) -> str:
        return "cagr"

    @classmethod
    def description(cls) -> str:
        return "Compound Annual Growth Rate"

    def __init__(self, alias: str = None, years: int = 5, frequency: str = 'monthly'):
        super().__init__(alias=alias)
        self.years = int(years) if years else None
        if frequency not in ['weekly', 'monthly']:
            raise ValueError("frequency must be either 'weekly' or 'monthly'")
        self.frequency = frequency

    def value(self, ticker: str) -> Optional[float]:
        symbol = Symbol.get(ticker)
        history = symbol.get_monthly() if self.frequency == 'monthly' else symbol.get_weekly()
        
        if history is None or len(history) == 0:
            return None
            
        latest_date = history['date'].max()
        start_date = history['date'].min()
        if self.years:
            start_date = max(latest_date - pd.DateOffset(years=self.years), start_date)
        years = (latest_date - start_date) / pd.Timedelta(days=365.25)

        start_prices = history[history['date'] >= start_date].head(1)
        end_prices = history[history['date'] <= latest_date].tail(1)

        if len(start_prices) == 0 or len(end_prices) == 0:
            return None

        start_price = start_prices['close'].values[0]
        end_price = end_prices['close'].values[0]

        if start_price <= 0:
            return None

        cagr = (end_price / start_price) ** (1 / years) - 1
        return cagr

    def value_str(self, ticker: str) -> str:
        v = self.value(ticker)
        return "n/a" if v is None else  f"{v:.4f}"
