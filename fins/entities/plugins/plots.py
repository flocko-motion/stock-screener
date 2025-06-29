from typing import Optional

import pandas as pd

from .. import BasketItem
from ..plugin import FieldPlugin, SeriesPlugin, Plugin, OutputPlugin, OutputData
from ...financial import Symbol


class PlotEach(OutputPlugin):
    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        super().__init__(alias=alias)

    def output_item(self, symbol: Symbol, data: dict[str, pd.DataFrame]):
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        
        if not data:
            return
            
        fig, ax1 = plt.subplots(figsize=(6, 4))
        ax2 = None
        
        for alias, df in data.items():
            if df.empty:
                continue
                
            # Assume first column is date/time, rest are data
            time_col = df.columns[0]
            data_cols = df.columns[1:]
            
            # Ensure date column is datetime
            if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
                df[time_col] = pd.to_datetime(df[time_col], unit='s' if df[time_col].dtype in ['int64', 'float64'] else None)
            
            data_type = df.attrs.get('type', 'index')
            
            for col in data_cols:
                series_name = df.attrs.get('title', f"{alias}_{col}")
                
                if data_type == 'indicator':
                    # Use secondary y-axis for indicators
                    if ax2 is None:
                        ax2 = ax1.twinx()
                        ax2.set_ylim(-1.1, 1.1)
                        ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
                        ax2.set_ylabel('Indicators', color='blue')
                    
                    ax2.plot(df[time_col], df[col], label=series_name, alpha=0.7, linewidth=1)
                    
                else:  # 'index' type - price data
                    ax1.plot(df[time_col], df[col], label=series_name, linewidth=2)
        
        # Configure primary axis (price data) - logarithmic scale with fixed range
        ax1.set_yscale('log')
        ax1.set_ylim(10, 1000000)
        ax1.set_ylabel('Value')
        ax1.set_xlabel('Date')
        ax1.grid(True, alpha=0.6, which='major')
        ax1.grid(True, alpha=0.25, which='minor')
        ax1.legend(loc='upper left')
        
        # Format secondary axis if exists
        if ax2 is not None:
            ax2.legend(loc='upper right')
        
        # Format x-axis dates - yearly labels, monthly ticks
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax1.xaxis.set_major_locator(mdates.YearLocator(base=2))
        ax1.xaxis.set_minor_locator(mdates.YearLocator())
        plt.xticks(rotation=60, fontsize=8)
        
        plt.title(f"{symbol.ticker} {symbol.name}")
        plt.tight_layout()
        plt.show()


class PlotAll(OutputPlugin):
    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        super().__init__(alias=alias)


    def output_all(self, data: 'OutputData'):
        print(data)

