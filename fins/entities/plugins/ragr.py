"""
Rolling Annual Growth Rate Plugin
"""
import datetime
from typing import Optional, Tuple, Union
import pandas as pd
import numpy as np

from .. import Plugin, BasketItem
from ..plugin_field import FieldPlugin


class Ragr(FieldPlugin):
    """
    Calculates Rolling Annual Growth Rate (RAGR) statistics over monthly data.
    
    Rolls a 12-month window over the monthly close history and calculates 
    Annual Growth Rate (AGR) for each window. Returns the mean AGR and 
    standard deviation (sigma) as a tuple.
    
    Args:
        alias: Custom field name (auto-generated if None)
        date_from: Start date for analysis (datetime.date or ISO string)
        date_to: End date for analysis (datetime.date or ISO string)
        
    Examples:
        Ragr()                              # Full history RAGR statistics
        Ragr(date_from="2020-01-01")        # RAGR from 2020 start
        Ragr(date_from="2020-01-01", date_to="2023-12-31")  # Custom range
    """

    def __init__(self, alias: str = None,
                 date_from: Union[datetime.date, str, None] = None,
                 date_to: Union[datetime.date, str, None] = None):
        # Register call arguments for __str__ representation
        self._register_call_args(alias=alias, date_from=date_from, date_to=date_to)
        
        # Convert string dates to date objects
        if isinstance(date_from, str):
            try:
                date_from = datetime.date.fromisoformat(date_from)
            except ValueError as e:
                raise ValueError(f"Invalid date_from format '{date_from}'. Expected ISO format 'YYYY-MM-DD'") from e
        if isinstance(date_to, str):
            try:
                date_to = datetime.date.fromisoformat(date_to)
            except ValueError as e:
                raise ValueError(f"Invalid date_to format '{date_to}'. Expected ISO format 'YYYY-MM-DD'") from e
        
        # Generate alias if not provided
        if alias is None:
            if date_from is None and date_to is None:
                alias = 'RAGR'
            else:
                from_str = date_from.strftime('%y-%m-%d') if date_from else ''
                to_str = date_to.strftime('%y-%m-%d') if date_to else ''
                alias = f'RAGR[{from_str};{to_str}]'
        
        super().__init__(alias=alias)
        
        # Validate date parameters
        if date_from is not None and date_to is not None:
            if date_from >= date_to:
                raise ValueError("date_from must be before date_to")
        
        self._date_from = date_from
        self._date_to = date_to

    def field_types(self):
        return [("Avg", Optional[float]), ("Med", Optional[float]), ("Sigma", Optional[float])]

    def field_values(self, item: BasketItem, data: dict[str, pd.DataFrame]):
        df = item.symbol().get_monthly()
        
        if df.empty:
            raise ValueError("No data found for symbol")
            
        # Filter by date range
        if self._date_from is not None:
            df = df[df['date'] >= pd.to_datetime(self._date_from)]
            
        if self._date_to is not None:
            df = df[df['date'] <= pd.to_datetime(self._date_to)]
        
        if df.empty or len(df) < 13:  # Need at least 13 months for 12-month rolling
            return [None, None, None]
        
        # QUALITY FILTER LAYER 1: Remove unreasonable price data
        # Filter out prices below $0.10 (likely data errors, splits not adjusted, etc.)
        min_reasonable_price = 0.10
        df_clean = df[df.iloc[:, 1] >= min_reasonable_price].copy()
        
        if df_clean.empty or len(df_clean) < 13:
            return [None, None, None]
        
        # QUALITY FILTER LAYER 2: Calculate rolling AGR with outlier detection
        rolling_agr_values = []
        
        for i in range(12, len(df_clean)):
            start_price = df_clean.iloc[i-12, 1]  # Price 12 months ago
            end_price = df_clean.iloc[i, 1]       # Current price
            
            if start_price <= 0 or end_price <= 0:
                continue
            
            # Calculate growth ratio
            growth_ratio = end_price / start_price
            
            # QUALITY FILTER LAYER 3: Cap extreme growth rates
            # Reasonable range: -95% decline to +1000% growth (10x)
            if growth_ratio < 0.05 or growth_ratio > 10.0:
                continue
                
            # Calculate Annual Growth Rate for this 12-month period
            agr = growth_ratio - 1
            rolling_agr_values.append(agr)
        
        if len(rolling_agr_values) < 5:  # Need minimum viable sample
            return [None, None, None]
        
        # QUALITY FILTER LAYER 4: Remove only the most extreme outliers (preserve financial volatility)
        rolling_agr_array = np.array(rolling_agr_values)
        
        # Only remove truly extreme outliers that are clearly data errors
        # Keep values between -99.9% and +2000% (20x growth) - this preserves legitimate high volatility
        extreme_outlier_mask = (rolling_agr_array >= -0.999) & (rolling_agr_array <= 19.0)
        filtered_agr_values = rolling_agr_array[extreme_outlier_mask]
        
        if len(filtered_agr_values) < 5:  # Need minimum viable sample after filtering
            return [None, None, None]
            
        # Calculate mean, median, and standard deviation on lightly filtered data
        mean_agr = np.mean(filtered_agr_values)
        median_agr = np.median(filtered_agr_values)
        sigma_agr = np.std(filtered_agr_values, ddof=1)  # Sample standard deviation
        
        return [mean_agr, median_agr, sigma_agr] 