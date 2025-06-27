"""
Compound Annual Growth Rate Column
"""
import datetime
from typing import Optional
import pandas as pd

from .. import Plugin, BasketItem
from ..plugin import FieldPlugin


class Cagr(FieldPlugin):
    """
    Calculates Compound Annual Growth Rate (CAGR) for a given time period.
    
    CAGR represents the mean annual growth rate of an investment over a specified time period.
    Supports filtering by date range (date_from/date_to) or a specific year shortcut.
    Resolution can be monthly ('m') or yearly ('y') data.
    """

    def __init__(self, alias: str = None,
                 date_from: Optional[datetime.date] = None,
                 date_to: Optional[datetime.date] = None,
                 year: Optional[int] = None,
                 resolution: str = 'm'
                 ):
        # Validate year parameter usage
        if year is not None:
            if date_from is not None or date_to is not None:
                raise ValueError("year parameter cannot be used with date_from or date_to")
            date_from = datetime.date(year, 1, 1)
            date_to = datetime.date(year, 12, 31)
        
        # Generate alias if not provided
        if alias is None:
            if year is not None:
                alias = f'CAGR[{year}]'
            elif date_from is None and date_to is None:
                alias = 'CAGR'
            else:
                from_str = date_from.strftime('%y-%m-%d') if date_from else ''
                to_str = date_to.strftime('%y-%m-%d') if date_to else ''
                alias = f'CAGR[{from_str};{to_str}]'
        
        super().__init__(alias=alias)
        
        # Validate resolution
        valid_resolutions = ['m', 'y']
        if resolution not in valid_resolutions:
            raise ValueError("resolution must be any of " + ", ".join(valid_resolutions))
        self._resolution = resolution
        
        # Validate date parameters
        if date_from is not None and date_to is not None:
            if date_from >= date_to:
                raise ValueError("date_from must be before date_to")
        
        self._date_from = date_from
        self._date_to = date_to

    def field_type(self) -> type:
        return Optional[float]

    def field_value(self, item: BasketItem):
        df = item.symbol().get_weekly() if self._resolution == 'y' else item.symbol().get_monthly()
        
        if df.empty:
            raise ValueError("No data found for symbol")
            
        # Filter by date range
        if self._date_from is not None:
            df = df[df['date'] >= pd.to_datetime(self._date_from)]
            
        if self._date_to is not None:
            df = df[df['date'] <= pd.to_datetime(self._date_to)]
        
        if df.empty:
            return None
            
        start_price = df.iloc[0, 1]  # First price in range
        end_price = df.iloc[-1, 1]   # Last price in range
        start_date = df.iloc[0, 0]   # First date in range
        end_date = df.iloc[-1, 0]    # Last date in range
        
        if start_price <= 0 or end_price <= 0:
            return None
            
        # Calculate years between dates
        time_diff = end_date - start_date
        years = time_diff.days / 365.25
        
        if years <= 0:
            return None
            
        # Calculate CAGR
        cagr = (end_price / start_price) ** (1 / years) - 1
        
        return cagr

